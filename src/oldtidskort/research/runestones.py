from __future__ import annotations

import concurrent.futures
import csv
import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..core.http import client, request
from ..sources.runesten import SPARQL_URL, _catalog_key, _parse_point
from .models import (
    Confidence,
    CoordinateMethod,
    EvidenceRecord,
    IdentityLink,
    LocationAssessment,
    LocationRole,
    RegisteredObservation,
    SourceRecord,
    StoneRecord,
)

RESEARCH_QUERY = """
SELECT ?item ?itemLabel ?coord ?catalog ?fortidsminderId ?runorId
       ?discovery ?discoveryLabel ?discoveryCoord
       ?location ?locationLabel ?locationCoord
       ?collection ?collectionLabel ?collectionCoord WHERE {
  ?item wdt:P31 wd:Q24566025 ; wdt:P17 wd:Q35 .
  OPTIONAL { ?item wdt:P625 ?coord . }
  OPTIONAL { ?item wdt:P1261 ?catalog . }
  OPTIONAL { ?item wdt:P3596 ?fortidsminderId . }
  OPTIONAL { ?item wdt:P1260 ?runorId . }
  OPTIONAL {
    ?item wdt:P189 ?discovery .
    OPTIONAL { ?discovery wdt:P625 ?discoveryCoord . }
  }
  OPTIONAL {
    ?item wdt:P276 ?location .
    OPTIONAL { ?location wdt:P625 ?locationCoord . }
  }
  OPTIONAL {
    ?item wdt:P195 ?collection .
    OPTIONAL { ?collection wdt:P625 ?collectionCoord . }
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "da,en" . }
}
"""

TABLES = ("stones", "registered_observations", "identity_links", "locations", "evidence", "sources")
RUNOR_API = "http://runor.nordiska.uu.se/rest"
RUNOR_EDITION = "2020"


@dataclass
class ResearchDataset:
    stones: list[StoneRecord]
    registered_observations: list[RegisteredObservation]
    identity_links: list[IdentityLink]
    locations: list[LocationAssessment]
    evidence: list[EvidenceRecord]
    sources: list[SourceRecord]


def fetch(raw_path: Path, refresh: bool = False) -> Path:
    if raw_path.exists() and not refresh:
        return raw_path
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with client() as http:
        response = request(
            http,
            "GET",
            SPARQL_URL,
            params={"query": RESEARCH_QUERY, "format": "json"},
            headers={"Accept": "application/sparql-results+json"},
        )
    raw_path.write_bytes(response.content)
    return raw_path


def fetch_runor(raw_path: Path, refresh: bool = False) -> Path:
    """Hent alle danske DR-poster og behold kun genstandstypen runsten."""
    if raw_path.exists() and not refresh:
        return raw_path
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with client() as http:
        response = request(
            http,
            "GET",
            f"{RUNOR_API}/search",
            params={
                "edition_id": RUNOR_EDITION,
                "matching_text": "DR",
                "search_field": "SIGNUM",
            },
        )
    index = {
        item["inscription_id"]: item
        for item in response.json()
        if item.get("signum1") == "DR"
        and item.get("provenance", {}).get("country", {}).get("country_code") == "DK"
    }

    def fetch_one(item: dict) -> dict:
        with client() as http:
            return request(
                http,
                "GET",
                f"{RUNOR_API}/inscriptions/{item['inscription_id']}",
                params={"edition_id": RUNOR_EDITION},
            ).json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(fetch_one, index.values()))
    runestones = [
        record
        for record in records
        if any(item.get("artefact") == "runsten" for item in record.get("artefacts", []))
    ]
    raw_path.write_text(
        json.dumps({"edition": RUNOR_EDITION, "records": runestones}, ensure_ascii=False),
        encoding="utf-8",
    )
    return raw_path


def build_dataset(
    raw_path: Path,
    fortidsminder_path: Path | None = None,
    runor_path: Path | None = None,
    accessed_at: str | None = None,
) -> ResearchDataset:
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    rows_by_item: dict[str, list[dict]] = defaultdict(list)
    for row in payload.get("results", {}).get("bindings", []):
        rows_by_item[_value(row, "item").rsplit("/", 1)[-1]].append(row)

    stones: list[StoneRecord] = []
    registered_observations: list[RegisteredObservation] = []
    identity_links: list[IdentityLink] = []
    locations: list[LocationAssessment] = []
    evidence: list[EvidenceRecord] = []
    sources: list[SourceRecord] = []
    fortidsminder_links: dict[str, set[str]] = defaultdict(set)
    accessed = accessed_at or datetime.now(tz=UTC).date().isoformat()

    for qid, rows in sorted(rows_by_item.items()):
        row = rows[0]
        stone_id = _catalog_key(_value(row, "catalog")) or qid
        source_id = f"wikidata:{qid}"
        sources.append(
            SourceRecord(
                source_id=source_id,
                title=f"Wikidata-entitet {qid}",
                publisher="Wikimedia Foundation / Wikidata-bidragydere",
                url=f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json",
                license="CC0 1.0",
                accessed_at=accessed,
            )
        )
        stones.append(
            StoneRecord(
                stone_id=stone_id,
                dr_number=_value(row, "catalog") or None,
                wikidata_id=qid,
                runor_id=_runor_uuid(_value(row, "runorId")) or None,
                name=_value(row, "itemLabel") or qid,
                record_note=(
                    "Maskinelt importeret fra Wikidata. Posten er med, fordi P31 er Q24566025 "
                    "og P17 er Danmark; den er ikke individuelt fagligt efterprøvet endnu."
                ),
            )
        )
        _append_unknown_original(stone_id, locations)
        _append_findspot(stone_id, rows, source_id, locations, evidence)
        _append_current(stone_id, rows, source_id, locations, evidence)

    if runor_path is not None:
        _merge_runor(
            runor_path,
            accessed,
            stones,
            fortidsminder_links,
            locations,
            evidence,
            sources,
        )

    if fortidsminder_path is not None:
        for qid, rows in rows_by_item.items():
            stone_id = _catalog_key(_value(rows[0], "catalog")) or qid
            for row in rows:
                if fortidsminder_id := _value(row, "fortidsminderId"):
                    fortidsminder_links[fortidsminder_id].add(stone_id)
        _append_fortidsminder(
            fortidsminder_path,
            accessed,
            fortidsminder_links,
            registered_observations,
            identity_links,
            locations,
            evidence,
            sources,
        )

    return ResearchDataset(
        stones, registered_observations, identity_links, locations, evidence, sources
    )


def _merge_runor(
    raw_path: Path,
    accessed: str,
    stones: list[StoneRecord],
    fortidsminder_links: dict[str, set[str]],
    locations: list[LocationAssessment],
    evidence: list[EvidenceRecord],
    sources: list[SourceRecord],
) -> None:
    raw_records = json.loads(raw_path.read_text(encoding="utf-8")).get("records", [])
    records = list({record["inscription_id"]: record for record in raw_records}.values())
    catalog_counts: dict[str, int] = defaultdict(int)
    for item in records:
        catalog_counts[_catalog_key(f"{item['signum1']} {item['signum2']}")] += 1
    by_runor_id = {stone.runor_id: stone for stone in stones if stone.runor_id}
    by_catalog = {_catalog_key(stone.dr_number): stone for stone in stones if stone.dr_number}
    for record in records:
        runor_id = record["inscription_id"]
        dr_number = f"{record['signum1']} {record['signum2']}"
        catalog_key = _catalog_key(dr_number)
        stone = by_runor_id.get(runor_id)
        if stone is None and catalog_counts[catalog_key] == 1:
            stone = by_catalog.get(catalog_key)
        place = (record.get("provenance", {}).get("place") or {}).get("place")
        if stone is None:
            stone_id = (
                f"{catalog_key}:{runor_id[:8]}"
                if catalog_counts[catalog_key] > 1
                else catalog_key
            )
            stone = StoneRecord(
                stone_id=stone_id,
                dr_number=dr_number,
                runor_id=runor_id,
                name=f"{place or dr_number}-stenen",
                period=_period(record),
                survival_status="extant" if record.get("extant") else "lost",
                record_note=(
                    f"Importeret fra Samnordisk runtextdatabas, udgave {RUNOR_EDITION}; "
                    "genstandstype runsten og proveniensland Danmark."
                ),
            )
            stones.append(stone)
        else:
            stone.runor_id = runor_id
            stone.period = _period(record)
            stone.survival_status = "extant" if record.get("extant") else "lost"
            stone.record_note += (
                f" Matchet med Samnordisk runtextdatabas via "
                f"{'P1260/UUID' if by_runor_id.get(runor_id) else 'DR-nummer'}."
            )

        source_id = f"runor:{runor_id}"
        sources.append(
            SourceRecord(
                source_id=source_id,
                title=f"Samnordisk runtextdatabas: {dr_number}",
                publisher="Uppsala universitet / Riksantikvarieämbetet",
                url=record["uri"],
                license="CC0 metadata via K-samsök",
                accessed_at=accessed,
            )
        )
        for heritage_register in record.get("her_identifiers", []):
            if heritage_register.get("country", {}).get("country_code") != "DK":
                continue
            for identifier in heritage_register.get("identifiers", []):
                if identifier.get("key") == "locality" and identifier.get("value"):
                    fortidsminder_links[str(identifier["value"])].add(stone.stone_id)
        _append_runor_locations(stone, record, source_id, locations, evidence)


def _append_runor_locations(
    stone: StoneRecord,
    record: dict,
    source_id: str,
    locations: list[LocationAssessment],
    evidence: list[EvidenceRecord],
) -> None:
    position = record.get("position") or {}
    earliest = (position.get("oldest_known") or {}).get("coordinates")
    provenance = record.get("provenance") or {}
    place = (provenance.get("place") or {}).get("place")
    original = record.get("original_location") or {}
    earliest_id = f"{stone.stone_id}:earliest:runor"
    if earliest:
        locations.append(
            LocationAssessment(
                location_id=earliest_id,
                stone_id=stone.stone_id,
                role=LocationRole.EARLIEST_KNOWN,
                label=place,
                lon=earliest[0],
                lat=earliest[1],
                coordinate_method=CoordinateMethod.SOURCE_COORDINATE,
                confidence=Confidence.HIGH,
                is_estimate=False,
                rationale=(
                    "Samnordisk runtextdatabas angiver dette som ældst belagte koordinat. "
                    "Det er ikke automatisk identisk med fundsted eller oprindelig opstilling."
                ),
                review_status="reviewed",
            )
        )
        evidence.append(
            EvidenceRecord(
                evidence_id=f"{earliest_id}:position-oldest-known",
                location_id=earliest_id,
                source_id=source_id,
                source_property="position.oldest_known",
                source_statement=f"Ældst belagte koordinat: {earliest[1]}, {earliest[0]}; sted {place}.",
                interpretation="Publiceres som ældst kendte sted, uden stærkere historisk påstand.",
            )
        )
        if original.get("original") is True:
            original_id = f"{stone.stone_id}:original:runor"
            locations.append(
                LocationAssessment(
                    location_id=original_id,
                    stone_id=stone.stone_id,
                    role=LocationRole.ORIGINAL,
                    label=place,
                    lon=earliest[0],
                    lat=earliest[1],
                    coordinate_method=CoordinateMethod.SOURCE_COORDINATE,
                    confidence=Confidence.HIGH,
                    is_estimate=False,
                    rationale=(
                        "Kilden markerer original_location.original=true; det ældst belagte "
                        "koordinat bruges derfor også som dokumenteret oprindelig placering."
                    ),
                    review_status="reviewed",
                )
            )
            evidence.append(
                EvidenceRecord(
                    evidence_id=f"{original_id}:original-true",
                    location_id=original_id,
                    source_id=source_id,
                    source_property="original_location.original",
                    source_statement="Samnordisk runtextdatabas markerer, at stenen står oprindeligt.",
                    interpretation="Ældst kendte koordinat klassificeres også som oprindeligt sted.",
                )
            )

    current = (position.get("current") or {}).get("coordinates")
    current_id = f"{stone.stone_id}:current:runor"
    placement = record.get("placement")
    if current:
        locations.append(
            LocationAssessment(
                location_id=current_id,
                stone_id=stone.stone_id,
                role=LocationRole.CURRENT,
                label=placement,
                lon=current[0],
                lat=current[1],
                coordinate_method=CoordinateMethod.SOURCE_COORDINATE,
                confidence=Confidence.HIGH,
                is_estimate=False,
                rationale="Samnordisk runtextdatabas angiver et særskilt current-koordinat.",
                review_status="reviewed",
            )
        )
        evidence.append(
            EvidenceRecord(
                evidence_id=f"{current_id}:position-current",
                location_id=current_id,
                source_id=source_id,
                source_property="position.current",
                source_statement=f"Nuværende koordinat: {current[1]}, {current[0]}; placering {placement}.",
                interpretation="Publiceres som nuværende placering.",
            )
        )
    elif placement:
        locations.append(
            LocationAssessment(
                location_id=current_id,
                stone_id=stone.stone_id,
                role=LocationRole.CURRENT,
                label=placement,
                coordinate_method=CoordinateMethod.UNKNOWN,
                confidence=Confidence.UNKNOWN,
                is_estimate=False,
                rationale=(
                    "Kilden navngiver den nuværende placering, men leverer ikke et særskilt "
                    "current-koordinat. Teksten bevares uden at opfinde et punkt."
                ),
                review_status="needs_review",
            )
        )


def _runor_uuid(value: str) -> str:
    return value.rstrip("/").rsplit("/", 1)[-1] if value else ""


def _period(record: dict) -> str:
    value = (record.get("period") or {}).get("period")
    return "middelalder" if value == "M" else "vikingetid"


def write_location_geojson(dataset: ResearchDataset, target: Path) -> int:
    """Skriv dokumenterede/markerede stedvurderinger som et selvstændigt kortlag."""
    stones = {stone.stone_id: stone for stone in dataset.stones}
    source_by_id = {source.source_id: source for source in dataset.sources}
    evidence_by_location: dict[str, list[EvidenceRecord]] = defaultdict(list)
    for item in dataset.evidence:
        evidence_by_location[item.location_id].append(item)

    selected: dict[tuple[str, LocationRole], LocationAssessment] = {}
    priorities = {"reviewed": 2, "needs_review": 1, "imported": 0}
    for location in dataset.locations:
        if location.lon is None or location.role is LocationRole.REGISTERED:
            continue
        key = (location.stone_id, location.role)
        previous = selected.get(key)
        if previous is None or priorities[location.review_status] > priorities[previous.review_status]:
            selected[key] = location

    features = []
    for location in sorted(selected.values(), key=lambda item: item.location_id):
        stone = stones[location.stone_id]
        evidence_rows = evidence_by_location[location.location_id]
        source_links = [
            {
                "title": source_by_id[item.source_id].title,
                "url": str(source_by_id[item.source_id].url),
                "property": item.source_property,
                "statement": item.source_statement,
                "interpretation": item.interpretation,
            }
            for item in evidence_rows
        ]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [location.lon, location.lat]},
            "properties": {
                "id": location.location_id,
                "source": "runestone_research",
                "source_id": stone.stone_id,
                "site_type": "runesten",
                "name": stone.name,
                "description": location.label,
                "period": stone.period,
                "period_raw": None,
                "municipality": None,
                "url": source_links[0]["url"] if source_links else None,
                "license": "Se de enkelte kilder og data/curated/runestones/sources.csv",
                "extra": {
                    "katalognummer": stone.dr_number,
                    "location_role": location.role,
                    "location_label": location.label,
                    "coordinate_method": location.coordinate_method,
                    "confidence": location.confidence,
                    "uncertainty_m": location.uncertainty_m,
                    "is_estimate": location.is_estimate,
                    "rationale": location.rationale,
                    "review_status": location.review_status,
                    "survival_status": stone.survival_status,
                    "evidence": source_links,
                },
            },
        })
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )
    return len(features)


def _append_fortidsminder(
    raw_path: Path,
    accessed: str,
    fortidsminder_links: dict[str, set[str]],
    observations: list[RegisteredObservation],
    identity_links: list[IdentityLink],
    locations: list[LocationAssessment],
    evidence: list[EvidenceRecord],
    sources: list[SourceRecord],
) -> None:
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    for feature in payload.get("features", []):
        props = feature.get("properties") or {}
        system_id = str(props["systemnr"])
        feature_type = str(props.get("anlaegstype", ""))
        if feature_type.casefold() != "runesten" and system_id not in fortidsminder_links:
            continue
        source_id = f"fortidsminder:{system_id}"
        source_url = f"https://www.kulturarv.dk/fundogfortidsminder/Lokalitet/{system_id}/"
        sources.append(
            SourceRecord(
                source_id=source_id,
                title=f"Fund og Fortidsminder, lokalitet {system_id}",
                publisher="Slots- og Kulturstyrelsen",
                url=source_url,
                license="Offentlige data; kreditering påkrævet",
                accessed_at=accessed,
            )
        )
        coords = feature["geometry"]["coordinates"][:2]
        observation_id = f"fortidsminder:{system_id}"
        observations.append(
            RegisteredObservation(
                observation_id=observation_id,
                source_id=source_id,
                source_record_id=system_id,
                feature_type=feature_type,
                label=f"Stednr. {props.get('stednr')}, lokalnr. {props.get('loknr')}",
                lon=coords[0],
                lat=coords[1],
                source_statement=(
                    f"Anlægstype {feature_type}; systemnr {system_id}; stednr {props.get('stednr')}; "
                    f"loknr {props.get('loknr')}; koordinat {coords[1]}, {coords[0]}."
                ),
                interpretation=(
                    "Autoritativ registerobservation. En lokalitet kan beskrive flere sten eller "
                    "en historisk fase og er derfor ikke automatisk en stenidentitet."
                ),
                review_status="needs_review",
            )
        )
        stone_ids = fortidsminder_links.get(system_id, set())
        if not stone_ids:
            continue
        for stone_id in sorted(stone_ids):
            identity_links.append(
                IdentityLink(
                    link_id=f"{stone_id}:{observation_id}",
                    stone_id=stone_id,
                    observation_id=observation_id,
                    method="authoritative_external_identifier",
                    confidence=Confidence.HIGH,
                    rationale=(
                        "Wikidata P3596 eller Samnordisk runtextdatabases danske HER-lokalitets-ID "
                        "peger eksplicit på dette systemnummer i Fund og Fortidsminder."
                    ),
                )
            )
            location_id = f"{stone_id}:registered:{system_id}"
            locations.append(
                LocationAssessment(
                    location_id=location_id,
                    stone_id=stone_id,
                    role=LocationRole.REGISTERED,
                    label=f"Stednr. {props.get('stednr')}, lokalnr. {props.get('loknr')}",
                    lon=coords[0],
                    lat=coords[1],
                    coordinate_method=CoordinateMethod.SOURCE_COORDINATE,
                    uncertainty_m=25,
                    confidence=Confidence.HIGH,
                    is_estimate=False,
                    rationale=(
                        "Direkte punktkoordinat fra Fund og Fortidsminders WFS. Punktet dokumenterer "
                        "registerets lokalitet, men klassificeres ikke automatisk som fundsted, "
                        "oprindeligt opstillingssted eller nuværende placering."
                    ),
                    review_status="needs_review",
                )
            )
            evidence.append(
                EvidenceRecord(
                    evidence_id=f"{location_id}:wfs",
                    location_id=location_id,
                    source_id=source_id,
                    source_property="WFS geometry + systemnr/stednr/loknr",
                    source_statement=observations[-1].source_statement,
                    interpretation=(
                        "Autoritativ registerposition. Den historiske rolle afgøres først efter "
                        "gennemgang af lokalitetens beskrivelse og undersøgelseshistorie."
                    ),
                )
            )


def write_dataset(dataset: ResearchDataset, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in TABLES:
        records = getattr(dataset, name)
        rows = [record.model_dump(mode="json") for record in records]
        if not rows:
            continue
        with (destination / f"{name}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def _append_unknown_original(stone_id: str, locations: list[LocationAssessment]) -> None:
    locations.append(
        LocationAssessment(
            location_id=f"{stone_id}:original",
            stone_id=stone_id,
            role=LocationRole.ORIGINAL,
            coordinate_method=CoordinateMethod.UNKNOWN,
            confidence=Confidence.UNKNOWN,
            is_estimate=False,
            rationale=(
                "Ingen undersøgt kilde dokumenterer endnu stenens oprindelige opstillingssted. "
                "Fundsted og oprindeligt opstillingssted må ikke sidestilles."
            ),
            review_status="needs_review",
        )
    )


def _append_findspot(
    stone_id: str,
    rows: list[dict],
    source_id: str,
    locations: list[LocationAssessment],
    evidence: list[EvidenceRecord],
) -> None:
    row = next((candidate for candidate in rows if _value(candidate, "discovery")), None)
    location_id = f"{stone_id}:findspot"
    if row is None:
        locations.append(_unknown_location(location_id, stone_id, LocationRole.FINDSPOT))
        return
    coords = _parse_point(_value(row, "discoveryCoord"))
    label = _value(row, "discoveryLabel") or None
    if coords is None:
        locations.append(
            LocationAssessment(
                location_id=location_id,
                stone_id=stone_id,
                role=LocationRole.FINDSPOT,
                label=label,
                coordinate_method=CoordinateMethod.UNKNOWN,
                confidence=Confidence.UNKNOWN,
                is_estimate=False,
                rationale="Wikidata angiver et fundsted med P189, men stedet mangler koordinater.",
                review_status="needs_review",
            )
        )
    else:
        locations.append(
            LocationAssessment(
                location_id=location_id,
                stone_id=stone_id,
                role=LocationRole.FINDSPOT,
                label=label,
                lon=coords[0],
                lat=coords[1],
                coordinate_method=CoordinateMethod.RELATED_PLACE_COORDINATE,
                uncertainty_m=5000,
                confidence=Confidence.MEDIUM,
                is_estimate=True,
                rationale=(
                    "Wikidata P189 navngiver fundstedet; punktet er P625-koordinatet for det "
                    "relaterede sted og ikke nødvendigvis det præcise fundpunkt. 5 km er en "
                    "konservativ standardusikkerhed indtil individuel kontrol."
                ),
                review_status="needs_review",
            )
        )
    evidence.append(
        EvidenceRecord(
            evidence_id=f"{location_id}:wikidata-p189",
            location_id=location_id,
            source_id=source_id,
            source_property="P189",
            source_statement=f"Wikidata angiver location of discovery: {label or _value(row, 'discovery')}",
            interpretation="Udsagnet støtter fundsted, men ikke oprindeligt opstillingssted.",
        )
    )


def _append_current(
    stone_id: str,
    rows: list[dict],
    source_id: str,
    locations: list[LocationAssessment],
    evidence: list[EvidenceRecord],
) -> None:
    row = next((candidate for candidate in rows if _value(candidate, "coord")), None)
    location_id = f"{stone_id}:current"
    if row is None:
        locations.append(_unknown_location(location_id, stone_id, LocationRole.CURRENT))
        return
    coords = _parse_point(_value(row, "coord"))
    place_label = _value(row, "locationLabel") or _value(row, "collectionLabel") or None
    locations.append(
        LocationAssessment(
            location_id=location_id,
            stone_id=stone_id,
            role=LocationRole.CURRENT,
            label=place_label,
            lon=coords[0],
            lat=coords[1],
            coordinate_method=CoordinateMethod.SOURCE_COORDINATE,
            uncertainty_m=100,
            confidence=Confidence.MEDIUM,
            is_estimate=False,
            rationale=(
                "Koordinatet er Wikidata P625 på selve stenen. Det behandles foreløbigt som "
                "nuværende placering, fordi Wikidata ikke angiver koordinatets historiske rolle. "
                "Klassifikationen kræver individuel kontrol; 100 m er en foreløbig usikkerhed."
            ),
            review_status="needs_review",
        )
    )
    evidence.append(
        EvidenceRecord(
            evidence_id=f"{location_id}:wikidata-p625",
            location_id=location_id,
            source_id=source_id,
            source_property="P625",
            source_statement=f"Wikidata angiver P625: {coords[1]}, {coords[0]}.",
            interpretation="Foreløbigt klassificeret som nuværende placering, ikke som fundsted.",
        )
    )


def _unknown_location(
    location_id: str, stone_id: str, role: LocationRole
) -> LocationAssessment:
    return LocationAssessment(
        location_id=location_id,
        stone_id=stone_id,
        role=role,
        coordinate_method=CoordinateMethod.UNKNOWN,
        confidence=Confidence.UNKNOWN,
        is_estimate=False,
        rationale=f"Den maskinelt undersøgte Wikidata-post har ingen oplysning om {role.value}.",
        review_status="needs_review",
    )


def _value(row: dict, key: str) -> str:
    return str(row.get(key, {}).get("value", ""))


def dataset_counts(dataset: ResearchDataset) -> dict[str, int]:
    return {
        "stones": len(dataset.stones),
        "registered_observations": len(dataset.registered_observations),
        "identity_links": len(dataset.identity_links),
        "locations": len(dataset.locations),
        "evidence": len(dataset.evidence),
        "findspots_with_coordinates": sum(
            location.role is LocationRole.FINDSPOT and location.lon is not None
            for location in dataset.locations
        ),
        "current_with_coordinates": sum(
            location.role is LocationRole.CURRENT and location.lon is not None
            for location in dataset.locations
        ),
    }


def validate_foreign_keys(dataset: ResearchDataset) -> None:
    stone_ids = {stone.stone_id for stone in dataset.stones}
    observation_ids = {
        observation.observation_id for observation in dataset.registered_observations
    }
    location_ids = {location.location_id for location in dataset.locations}
    source_ids = {source.source_id for source in dataset.sources}
    if len(stone_ids) != len(dataset.stones):
        raise ValueError("dublerede stone_id")
    if len(observation_ids) != len(dataset.registered_observations):
        raise ValueError("dublerede observation_id")
    _require_members((link.stone_id for link in dataset.identity_links), stone_ids, "stone_id")
    _require_members(
        (link.observation_id for link in dataset.identity_links), observation_ids, "observation_id"
    )
    _require_members((location.stone_id for location in dataset.locations), stone_ids, "stone_id")
    _require_members((item.location_id for item in dataset.evidence), location_ids, "location_id")
    _require_members((item.source_id for item in dataset.evidence), source_ids, "source_id")


def _require_members(values: Iterable[str], allowed: set[str], field: str) -> None:
    missing = sorted(set(values) - allowed)
    if missing:
        raise ValueError(f"ukendte {field}: {missing}")

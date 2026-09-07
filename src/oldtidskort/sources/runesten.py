"""Runestensfund.

Danmarks Runeindskrifter (runer.ku.dk) har ingen offentlig API, så primær
kilde er Wikidata: runesten og runeindskrifter i Danmark har typisk både
DR-nummer, koordinat og datering, og data er CC0. En manuelt kurateret CSV i
`data/raw/runesten.csv` supplerer/overskriver, når Wikidata mangler noget.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path

from ..core.http import client, request
from ..core.models import Period, Site, SiteType
from ..core.periods import parse_period, period_for_year
from .base import register

SPARQL_URL = "https://query.wikidata.org/sparql"

# Q24566025 = nordisk runesten; P17 = land, Q35 = Danmark.
# P625 = koordinat, P1261 = Rundata-katalognummer (fx DR 42).
QUERY = """
SELECT ?item ?itemLabel ?coord ?inception ?admin ?adminLabel ?catalog WHERE {
  ?item wdt:P31 wd:Q24566025 ;
        wdt:P17 wd:Q35 ;
        wdt:P625 ?coord .
  OPTIONAL { ?item wdt:P571 ?inception . }
  OPTIONAL { ?item wdt:P131 ?admin . }
  OPTIONAL { ?item wdt:P1261 ?catalog . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "da,en". }
}
"""

CSV_COLUMNS = ("dr_nummer", "navn", "lon", "lat", "datering", "kommune", "kilde_url")


class Runesten:
    name = "runesten"
    license = "CC0 1.0 (Wikidata); kuraterede rækker: se kilde_url"
    homepage = "https://www.wikidata.org/"

    def fetch(self, raw_dir: Path, refresh: bool = False) -> Path:
        raw_dir.mkdir(parents=True, exist_ok=True)
        target = raw_dir / f"{self.name}.json"
        if target.exists() and not refresh:
            return target
        with client() as http:
            response = request(
                http,
                "GET",
                SPARQL_URL,
                params={"query": QUERY, "format": "json"},
                headers={"Accept": "application/sparql-results+json"},
            )
        target.write_bytes(response.content)
        return target

    def parse(self, raw_path: Path) -> Iterator[Site]:
        wikidata = list(self._parse_wikidata(raw_path))
        curated = list(self._parse_csv(raw_path.parent / "runesten.csv"))
        curated_by_catalog = {
            _catalog_key(site.source_id): site for site in curated if _catalog_key(site.source_id)
        }

        used_catalogs: set[str] = set()
        for site in wikidata:
            catalog = _catalog_key(site.extra.get("katalognummer"))
            override = curated_by_catalog.get(catalog)
            if override is None:
                yield site
                continue
            used_catalogs.add(catalog)
            # Bevar Wikidata-QID'et som stabilt id, men lad den kuraterede række
            # rette de felter, der faktisk er udfyldt i CSV'en.
            updates = {
                field: value
                for field, value in override.model_dump().items()
                if value not in (None, "", {}) and field not in {"id", "source", "source_id", "extra"}
            }
            updates["extra"] = {**site.extra, "katalognummer": override.source_id}
            updates["license"] = f"{site.license}; kurateret supplement"
            yield site.model_copy(update=updates)

        for site in curated:
            if _catalog_key(site.source_id) not in used_catalogs:
                yield site

    def _parse_wikidata(self, raw_path: Path) -> Iterator[Site]:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        for row in payload.get("results", {}).get("bindings", []):
            coords = _parse_point(row["coord"]["value"])
            if coords is None:
                continue
            lon, lat = coords
            qid = row["item"]["value"].rsplit("/", 1)[-1]
            inception = row.get("inception", {}).get("value")
            catalog = row.get("catalog", {}).get("value")
            yield Site(
                id=f"{self.name}:{qid}",
                source=self.name,
                source_id=qid,
                site_type=SiteType.RUNESTEN,
                name=row.get("itemLabel", {}).get("value"),
                lon=lon,
                lat=lat,
                # Langt de fleste danske runesten er vikingetid; vi lader kun
                # eksplicit datering overskrive den antagelse.
                period_raw=inception,
                period=period_for_year(_year(inception)) if inception else Period.VIKINGETID,
                year_from=_year(inception),
                municipality=row.get("adminLabel", {}).get("value"),
                url=row["item"]["value"],
                license="CC0 1.0 (Wikidata)",
                extra={"katalognummer": catalog},
            )

    def _parse_csv(self, csv_path: Path) -> Iterator[Site]:
        if not csv_path.exists():
            return
        with csv_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                yield Site(
                    id=f"{self.name}:{row['dr_nummer']}",
                    source=self.name,
                    source_id=row["dr_nummer"],
                    site_type=SiteType.RUNESTEN,
                    name=row.get("navn") or None,
                    lon=float(row["lon"]),
                    lat=float(row["lat"]),
                    period_raw=row.get("datering"),
                    period=parse_period(row.get("datering")) if row.get("datering") else Period.VIKINGETID,
                    municipality=row.get("kommune") or None,
                    url=row.get("kilde_url") or None,
                    license="kurateret",
                )


def _parse_point(wkt: str) -> tuple[float, float] | None:
    """Wikidata leverer 'Point(9.419 55.756)' — lon først."""
    if not wkt.startswith("Point("):
        return None
    lon, _, lat = wkt[len("Point(") : -1].partition(" ")
    try:
        return float(lon), float(lat)
    except ValueError:
        return None


def _year(value: str | None) -> int | None:
    """Wikidata-datoer er ISO 8601, evt. med negativt år."""
    if not value:
        return None
    head = value.lstrip("+")
    digits = head[:4]
    return int(digits) if digits.isdigit() else None


def _catalog_key(value: object) -> str:
    """Normalisér fx `DR 42` og `dr42`, så CSV kan overskrive Wikidata."""
    return "".join(character for character in str(value or "").upper() if character.isalnum())


register(Runesten())

"""Danske bebyggelsesnavne dateret efter navneendelse.

Kilde: OpenStreetMap via Overpass — `place`-noder dækker stort set alle danske
byer og landsbyer og har fri licens. Dateringen kommer ikke fra OSM, men fra
det kuraterede endelsesdatasæt i `data/curated/placename_suffixes/`.

Et bynavn er ikke et fortidsminde: laget er med for at kunne holde
bebyggelsesnavnenes kronologi op mod gravhøje og runesten på kortets fælles
periodeakse. Se det kuraterede datasæts README for forbeholdene.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import httpx

from ..core.http import client, request
from ..core.models import Site, SiteType
from ..core.placenames import CURATED_DIR, classify
from .base import register

OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

#: Kun egentlige bebyggelser. `isolated_dwelling` og `farm` udelades: de er
#: ujævnt kortlagt og ville skævvride tætheden.
PLACE_RANKS = ("city", "town", "village", "hamlet", "suburb")

QUERY = """
[out:json][timeout:600];
area["ISO3166-1"="DK"][admin_level=2]->.dk;
(
  node["place"~"^(city|town|village|hamlet|suburb)$"]["name"](area.dk);
);
out center tags;
"""


def _population(tags: dict) -> int | None:
    value = (tags.get("population") or "").replace(".", "").replace(" ", "")
    return int(value) if value.isdigit() else None


class Bynavne:
    name = "bynavne_osm"
    license = "ODbL 1.0 — © OpenStreetMap-bidragydere"
    homepage = "https://www.openstreetmap.org/copyright"

    def __init__(self, curated_dir: Path = CURATED_DIR) -> None:
        self.curated_dir = curated_dir

    def fetch(self, raw_dir: Path, refresh: bool = False) -> Path:
        raw_dir.mkdir(parents=True, exist_ok=True)
        target = raw_dir / f"{self.name}.json"
        if target.exists() and not refresh:
            return target
        errors: list[str] = []
        with client() as http:
            for url in OVERPASS_URLS:
                try:
                    response = request(http, "POST", url, data={"data": QUERY})
                    target.write_bytes(response.content)
                    return target
                except (RuntimeError, httpx.HTTPError) as error:
                    errors.append(f"{url}: {error}")
        raise RuntimeError("Overpass svarede ikke:\n  " + "\n  ".join(errors))

    def parse(self, raw_path: Path) -> Iterator[Site]:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        for element in payload.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name")
            center = element.get("center") or element
            lon, lat = center.get("lon"), center.get("lat")
            if not name or lon is None or lat is None:
                continue
            if tags.get("place") not in PLACE_RANKS:
                continue
            suffix = classify(name, self.curated_dir)
            source_id = f"{element['type']}/{element['id']}"
            yield Site(
                id=f"{self.name}:{source_id}",
                source=self.name,
                source_id=source_id,
                site_type=SiteType.BYNAVN,
                name=name,
                description=suffix.gloss if suffix else None,
                lon=lon,
                lat=lat,
                period=suffix.period if suffix else Site.model_fields["period"].default,
                period_raw=suffix.family_label if suffix else None,
                year_from=suffix.year_from if suffix else None,
                year_to=suffix.year_to if suffix else None,
                license=self.license,
                url=f"https://www.openstreetmap.org/{element['type']}/{element['id']}",
                extra={
                    "suffix": suffix.suffix if suffix else None,
                    "suffix_family": suffix.family if suffix else None,
                    "suffix_label": suffix.family_label if suffix else None,
                    "horizon": suffix.horizon if suffix else None,
                    "confidence": suffix.confidence if suffix else None,
                    "gloss": suffix.gloss if suffix else None,
                    "place_rank": tags.get("place"),
                    "population": _population(tags),
                },
            )


register(Bynavne())

"""Middelalderlige og senere kirker.

Kilde: OpenStreetMap via Overpass. Bred dækning (stort set alle danske
sognekirker er kortlagt) og fri licens. `start_date` er ujævnt udfyldt, så
periode udledes af både datering og `historic`-tags.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

import httpx

from ..core.http import client, request
from ..core.models import Period, Site, SiteType
from ..core.periods import parse_period
from .base import register

# Overpass har flere spejle; vi prøver dem i rækkefølge ved travlhed.
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

QUERY = """
[out:json][timeout:600];
area["ISO3166-1"="DK"][admin_level=2]->.dk;
(
  nwr["building"="church"](area.dk);
  nwr["building"="chapel"](area.dk);
  nwr["historic"="church"](area.dk);
  nwr["amenity"="place_of_worship"]["religion"="christian"](area.dk);
);
out center tags;
"""

#: Kirker uden datering skal ikke antages middelalderlige; kun eksplicitte
#: signaler tæller.
_MEDIEVAL_TAGS = {"church", "monastery", "ruins"}


class Kirker:
    name = "kirker_osm"
    license = "ODbL 1.0 — © OpenStreetMap-bidragydere"
    homepage = "https://www.openstreetmap.org/copyright"

    def fetch(self, raw_dir: Path) -> Path:
        raw_dir.mkdir(parents=True, exist_ok=True)
        target = raw_dir / f"{self.name}.json"
        if target.exists():
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
            center = element.get("center") or element
            lon, lat = center.get("lon"), center.get("lat")
            if lon is None or lat is None:
                continue
            source_id = f"{element['type']}/{element['id']}"
            start_date = tags.get("start_date") or tags.get("building:start_date")
            year = parse_osm_year(start_date)
            yield Site(
                id=f"{self.name}:{source_id}",
                source=self.name,
                source_id=source_id,
                site_type=SiteType.KIRKE,
                name=tags.get("name"),
                description=tags.get("description"),
                lon=lon,
                lat=lat,
                period_raw=start_date,
                period=period_for(start_date, tags),
                year_from=year,
                license=self.license,
                url=f"https://www.openstreetmap.org/{element['type']}/{element['id']}",
                extra={
                    "denomination": tags.get("denomination"),
                    "heritage": tags.get("heritage"),
                    "wikidata": tags.get("wikidata"),
                },
            )


def parse_osm_year(value: str | None) -> int | None:
    """Tidligste årstal i OSM `start_date`: '1180', 'C12', '~1150', '1180-01-01'."""
    if not value:
        return None
    century = re.fullmatch(r"[Cc](\d{1,2})", value.strip())
    if century:
        # 'C12' er 1100-tallet, dvs. år 1101-1200.
        return (int(century.group(1)) - 1) * 100 + 1
    match = re.search(r"\d{3,4}", value)
    return int(match.group()) if match else None


def period_for(value: str | None, tags: dict) -> Period:
    """Et århundrede placeres efter sin midte — 'C11' er en kirke fra
    1000-tallet, ikke nødvendigvis fra år 1001."""
    year = parse_osm_year(value)
    if year is not None:
        if value and re.fullmatch(r"[Cc]\d{1,2}", value.strip()):
            year += 49
        if year < 1050:
            return Period.VIKINGETID
        if year < 1536:
            return Period.MIDDELALDER
        return Period.RENAESSANCE
    if tags.get("historic") in _MEDIEVAL_TAGS:
        return parse_period(tags.get("historic:period") or "")
    return Period.UKENDT


register(Kirker())

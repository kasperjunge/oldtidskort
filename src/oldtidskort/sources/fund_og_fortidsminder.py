"""Gravhøje og andre fortidsminder fra Fund og Fortidsminder (Slots- og Kulturstyrelsen).

Data hentes via styrelsens offentlige WFS. Lagnavne er ikke hardcodede: vi
læser GetCapabilities og vælger punktlagene, så en omdøbning hos udbyderen
giver en forståelig fejl frem for et tomt datasæt. Kør
`oldtidskort inspect fund_og_fortidsminder` for at se, hvad serveren tilbyder.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar
from xml.etree.ElementTree import ParseError

import httpx

from ..core.geo import in_denmark, utm32_to_wgs84
from ..core.http import client
from ..core.models import Site, SiteType
from ..core.periods import parse_period
from ..core.wfs import capabilities, get_features, output_formats, pick_output_format
from .base import register

# Styrelsen har flyttet servicen mellem hosts; vi prøver de kendte i rækkefølge.
WFS_ENDPOINTS = (
    "https://www.kulturarv.dk/ffgeoserver/public/wfs",
    "https://www.kulturarv.dk/ffpublic/wfs",
    "https://www.kulturarv.dk/geoserver/wfs",
)

#: Punktlag med fortidsminder. Både fredede og ikke-fredede skal med — langt
#: fra alle registrerede gravhøje er fredede.
LAYER_HINTS = ("fundogfortidsminder", "fortidsminder")
POINT_HINTS = ("punkt", "point")

#: Feltnavne varierer mellem lagene; vi prøver kandidaterne i rækkefølge.
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    # `stednr` identifies an archaeological area and is shared by many monuments.
    # Production's `systemnr` is the stable locality id; the point serial is the
    # best fallback when a locality id is missing.
    "id": (
        "systemnr",
        "lokalitet_punkt_lbnr",
        "stedid",
        "id",
        "objectid",
        "fid",
        "anlaegid",
        "stednr",
    ),
    "name": ("stednavn", "navn", "lokalitet", "anlaegsnavn"),
    "type": ("anlaegsbetegnelse", "anlaegstype", "anlaeg", "type", "betegnelse"),
    "period": ("datering", "periode", "dateringtekst"),
    "municipality": ("kommune", "kommunenavn"),
    "parish": ("sogn", "sognenavn"),
    "url": ("url",),
}


def _first(props: dict, keys: tuple[str, ...]) -> str | None:
    """Slår op case-insensitivt — GeoServer-lag blander store og små bogstaver."""
    lowered = {str(k).casefold(): v for k, v in props.items()}
    for key in keys:
        value = lowered.get(key)
        if value not in (None, ""):
            return str(value)
    return None


class FundOgFortidsminder:
    name = "fund_og_fortidsminder"
    license = "Offentlige data fra Slots- og Kulturstyrelsen — kreditér kilden"
    homepage = "https://www.kulturarv.dk/fundogfortidsminder/"

    #: Anlægsbetegnelser der tælles som gravhøj. Kildens vokabular er stort;
    #: matchning er substring-baseret og case-insensitiv.
    barrow_terms: ClassVar[tuple[str, ...]] = (
        "rundhøj",
        "langhøj",
        "gravhøj",
        "højgruppe",
        "dysse",
        "jættestue",
        "stenkiste",
        "skibssætning",
        "gravplads",
        "gravhøje",
    )

    def endpoints(self) -> tuple[str, ...]:
        return WFS_ENDPOINTS

    def discover_layers(self, http, endpoint: str) -> list[str]:
        """Punktlag hos udbyderen, der ser ud til at indeholde fortidsminder."""
        names = []
        for feature_type in capabilities(http, endpoint):
            haystack = f"{feature_type.name} {feature_type.title}".casefold()
            if any(hint in haystack for hint in LAYER_HINTS) and any(
                hint in haystack for hint in POINT_HINTS
            ):
                names.append(feature_type.name)
        return names

    def fetch(self, raw_dir: Path) -> Path:
        raw_dir.mkdir(parents=True, exist_ok=True)
        target = raw_dir / f"{self.name}.json"
        if target.exists():
            return target

        errors: list[str] = []
        with client() as http:
            for endpoint in self.endpoints():
                try:
                    layers = self.discover_layers(http, endpoint)
                    if not layers:
                        errors.append(f"{endpoint}: ingen punktlag med fortidsminder")
                        continue
                    output_format = pick_output_format(output_formats(http, endpoint))
                    features: list[dict] = []
                    for layer in layers:
                        features.extend(
                            get_features(http, endpoint, layer, output_format=output_format)
                        )
                    target.write_text(
                        json.dumps(
                            {"endpoint": endpoint, "layers": layers, "features": features},
                            ensure_ascii=False,
                        ),
                        encoding="utf-8",
                    )
                    return target
                except (RuntimeError, httpx.HTTPError, ParseError, ValueError) as error:
                    # Et endpoint kan være flyttet eller nede; næste kan sagtens virke.
                    errors.append(f"{endpoint}: {error}")
        raise RuntimeError(
            "Kunne ikke hente Fund og Fortidsminder fra nogen kendt WFS:\n  "
            + "\n  ".join(errors)
        )

    def is_barrow(self, type_text: str | None) -> bool:
        if not type_text:
            return False
        lowered = type_text.casefold()
        return any(term in lowered for term in self.barrow_terms)

    def parse(self, raw_path: Path) -> Iterator[Site]:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        for feature in payload.get("features", []):
            props = feature.get("properties") or {}
            type_text = _first(props, FIELD_ALIASES["type"])
            if not self.is_barrow(type_text):
                continue
            coords = _coordinates(feature)
            if coords is None:
                continue
            lon, lat = coords
            source_id = _first(props, FIELD_ALIASES["id"]) or str(feature.get("id", ""))
            if not source_id:
                continue
            period_raw = _first(props, FIELD_ALIASES["period"])
            yield Site(
                id=f"{self.name}:{source_id}",
                source=self.name,
                source_id=source_id,
                site_type=SiteType.GRAVHOEJ,
                name=_first(props, FIELD_ALIASES["name"]),
                description=type_text,
                lon=lon,
                lat=lat,
                period_raw=period_raw,
                period=parse_period(period_raw or type_text),
                municipality=_first(props, FIELD_ALIASES["municipality"]),
                parish=_first(props, FIELD_ALIASES["parish"]),
                url=_first(props, FIELD_ALIASES["url"]),
                license=self.license,
                extra={
                    "anlaegsbetegnelse": type_text,
                    "fredet": "punkt_fredet" in str(feature.get("id", "")),
                    "stednr": _first(props, ("stednr",)),
                },
            )


def _coordinates(feature: dict) -> tuple[float, float] | None:
    """Punktkoordinat i WGS84.

    Vi beder om EPSG:4326, men nogle lag ignorerer `srsName` og svarer i
    UTM32N. Store værdier afslører det, og så omprojicerer vi selv.
    """
    geometry = feature.get("geometry") or {}
    if geometry.get("type") != "Point":
        return None
    x, y = geometry["coordinates"][:2]
    if abs(x) > 180 or abs(y) > 90:
        x, y = utm32_to_wgs84(x, y)
    # Nogle servere svarer lat/lon i stedet for lon/lat på WFS 1.1.0.
    if not in_denmark(x, y) and in_denmark(y, x):
        x, y = y, x
    return x, y


register(FundOgFortidsminder())

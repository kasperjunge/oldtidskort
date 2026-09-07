"""Minimal WFS-klient.

Vi hardcoder ikke lagnavne: `capabilities()` henter dem fra serveren, så en
omdøbning hos udbyderen giver en forståelig fejl i stedet for et tomt datasæt.
"""

from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree

import httpx

from .http import request

# GeoJSON er ikke garanteret på ældre GeoServer-installationer; rækkefølgen er
# vores præference, og `pick_output_format` vælger den første understøttede.
PREFERRED_FORMATS = (
    "application/json",
    "json",
    "application/json; subtype=geojson",
    "geojson",
)


@dataclass(frozen=True)
class FeatureType:
    name: str
    title: str
    srs: str | None


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def capabilities(http: httpx.Client, url: str, version: str = "1.1.0") -> list[FeatureType]:
    """Henter og parser GetCapabilities. Namespace-agnostisk, da WFS 1.0/1.1/2.0
    bruger hver sit namespace."""
    response = request(
        http,
        "GET",
        url,
        params={"service": "WFS", "version": version, "request": "GetCapabilities"},
    )
    root = ElementTree.fromstring(response.content)
    types: list[FeatureType] = []
    for element in root.iter():
        if _localname(element.tag) != "FeatureType":
            continue
        fields: dict[str, str] = {}
        for child in element:
            key = _localname(child.tag)
            if key in {"Name", "Title", "DefaultSRS", "SRS", "DefaultCRS"} and child.text:
                fields.setdefault(key, child.text.strip())
        if "Name" in fields:
            types.append(
                FeatureType(
                    name=fields["Name"],
                    title=fields.get("Title", ""),
                    srs=fields.get("DefaultSRS") or fields.get("SRS") or fields.get("DefaultCRS"),
                )
            )
    return types


def output_formats(http: httpx.Client, url: str, version: str = "1.1.0") -> set[str]:
    response = request(
        http,
        "GET",
        url,
        params={"service": "WFS", "version": version, "request": "GetCapabilities"},
    )
    root = ElementTree.fromstring(response.content)
    formats: set[str] = set()
    for element in root.iter():
        if _localname(element.tag) in {"Value", "Format"} and element.text:
            formats.add(element.text.strip())
    return formats


def pick_output_format(available: set[str]) -> str:
    lowered = {value.lower(): value for value in available}
    for candidate in PREFERRED_FORMATS:
        if candidate in lowered:
            return lowered[candidate]
    raise RuntimeError(
        "Serveren tilbyder ikke GeoJSON. Tilgængelige formater: " + ", ".join(sorted(available))
    )


def get_features(
    http: httpx.Client,
    url: str,
    typename: str,
    *,
    output_format: str,
    version: str = "1.1.0",
    srs: str = "EPSG:4326",
    page_size: int = 5000,
    max_features: int | None = None,
) -> list[dict]:
    """Henter alle features med paging. Returnerer GeoJSON-features."""
    # WFS 1.0.0 kender ikke startIndex; der falder vi tilbage til ét stort kald.
    supports_paging = version >= "1.1.0"
    key = "typeNames" if version.startswith("2") else "typeName"
    features: list[dict] = []
    start = 0
    while True:
        params = {
            "service": "WFS",
            "version": version,
            "request": "GetFeature",
            key: typename,
            "outputFormat": output_format,
            "srsName": srs,
        }
        if supports_paging:
            params["count" if version.startswith("2") else "maxFeatures"] = str(page_size)
            params["startIndex"] = str(start)
        payload = request(http, "GET", url, params=params).json()
        page = payload.get("features", [])
        features.extend(page)
        if max_features is not None and len(features) >= max_features:
            return features[:max_features]
        if not supports_paging or len(page) < page_size:
            return features
        start += page_size

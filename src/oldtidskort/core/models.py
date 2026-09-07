"""Kanonisk datamodel. Alle kilder normaliseres til `Site`."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class Period(StrEnum):
    """Grov periodeinddeling brugt til filtrering i kortet."""

    STENALDER = "stenalder"
    BRONZEALDER = "bronzealder"
    JERNALDER = "jernalder"
    VIKINGETID = "vikingetid"
    MIDDELALDER = "middelalder"
    RENAESSANCE = "renaessance"
    UKENDT = "ukendt"


class SiteType(StrEnum):
    BYNAVN = "bynavn"
    GRAVHOEJ = "gravhoej"
    KIRKE = "kirke"
    RUNESTEN = "runesten"


class Site(BaseModel):
    """Ét historisk punkt på kortet."""

    id: str = Field(description="Stabilt id: '<source>:<kildens id>'")
    source: str
    source_id: str
    site_type: SiteType
    name: str | None = None
    description: str | None = None

    # Geometri i WGS84 (EPSG:4326) — projektion sker i core.geo.
    lon: float
    lat: float

    period: Period = Period.UKENDT
    period_raw: str | None = Field(default=None, description="Kildens egen periodetekst")
    year_from: int | None = None
    year_to: int | None = None

    municipality: str | None = None
    parish: str | None = None
    url: HttpUrl | None = None
    license: str | None = None
    extra: dict = Field(default_factory=dict)

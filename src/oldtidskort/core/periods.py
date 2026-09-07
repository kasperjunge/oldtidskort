"""Mapping fra kildernes fritekst-perioder til vores `Period`."""

from __future__ import annotations

from .models import Period

# Kilderne (især Fund og Fortidsminder) bruger mange varianter; udvid efter behov.
_KEYWORDS: list[tuple[str, Period]] = [
    ("vikingetid", Period.VIKINGETID),
    ("viking", Period.VIKINGETID),
    ("middelalder", Period.MIDDELALDER),
    ("renæssance", Period.RENAESSANCE),
    ("bronzealder", Period.BRONZEALDER),
    ("jernalder", Period.JERNALDER),
    ("stenalder", Period.STENALDER),
    ("neolit", Period.STENALDER),
    ("mesolit", Period.STENALDER),
]


def parse_period(raw: str | None) -> Period:
    if not raw:
        return Period.UKENDT
    text = raw.casefold()
    for keyword, period in _KEYWORDS:
        if keyword in text:
            return period
    return Period.UKENDT


# Grove årstalsgrænser for dansk periodisering (vikingetid regnes ca. 750-1050,
# middelalder til reformationen 1536).
def period_for_year(year: int | None) -> Period:
    if year is None:
        return Period.UKENDT
    if year < -1700:
        return Period.STENALDER
    if year < -500:
        return Period.BRONZEALDER
    if year < 750:
        return Period.JERNALDER
    if year < 1050:
        return Period.VIKINGETID
    if year < 1536:
        return Period.MIDDELALDER
    return Period.RENAESSANCE

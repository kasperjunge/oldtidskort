"""Datering af danske bebyggelsesnavne ud fra navneendelsen.

Klassifikationen ligger som kurateret data i
`data/curated/placename_suffixes/`, ikke i koden, så den faglige vurdering kan
læses og reviewes for sig. Se mappens README for forbeholdene — en endelse
daterer navnetypen, ikke nødvendigvis bebyggelsen.
"""

from __future__ import annotations

import csv
import functools
from dataclasses import dataclass
from pathlib import Path

from .models import Period

CURATED_DIR = Path(__file__).resolve().parents[3] / "data" / "curated" / "placename_suffixes"

#: Uden en rimelig stamme foran endelsen er matchet oftest tilfældigt.
MIN_STEM = 2


@dataclass(frozen=True)
class Suffix:
    """Én endelsesform og den datering, navnelaget tilskrives."""

    suffix: str
    family: str
    family_label: str
    horizon: str
    period: Period
    year_from: int | None
    year_to: int | None
    confidence: str
    gloss: str


def _int(value: str) -> int | None:
    return int(value) if value.strip() else None


@functools.cache
def load_suffixes(curated_dir: Path = CURATED_DIR) -> tuple[Suffix, ...]:
    """Endelser sorteret længst først, så '-strup' vinder over '-rup'."""
    with (curated_dir / "suffixes.csv").open(encoding="utf-8") as handle:
        rows = [
            Suffix(
                suffix=row["suffix"].strip().casefold(),
                family=row["family"].strip(),
                family_label=row["family_label"].strip(),
                horizon=row["horizon"].strip(),
                period=Period(row["period"].strip()),
                year_from=_int(row["year_from"]),
                year_to=_int(row["year_to"]),
                confidence=row["confidence"].strip(),
                gloss=row["gloss"].strip(),
            )
            for row in csv.DictReader(handle)
        ]
    return tuple(sorted(rows, key=lambda item: len(item.suffix), reverse=True))


@functools.cache
def load_exceptions(curated_dir: Path = CURATED_DIR) -> dict[str, str]:
    """Navn (casefoldet) → `family`, eller 'none' når navnet ikke skal dateres."""
    path = curated_dir / "exceptions.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return {
            row["name"].strip().casefold(): row["decision"].strip()
            for row in csv.DictReader(handle)
            if row["name"].strip()
        }


def _by_family(curated_dir: Path) -> dict[str, Suffix]:
    families: dict[str, Suffix] = {}
    for entry in load_suffixes(curated_dir):
        families.setdefault(entry.family, entry)
    return families


def classify(name: str | None, curated_dir: Path = CURATED_DIR) -> Suffix | None:
    """Finder navnelaget for et bebyggelsesnavn, eller None hvis intet passer.

    Sammensatte navne vurderes på sidste ord: 'Store Heddinge' → 'Heddinge'.
    """
    if not name:
        return None
    exception = load_exceptions(curated_dir).get(name.strip().casefold())
    if exception == "none":
        return None
    if exception:
        return _by_family(curated_dir).get(exception)

    last_word = name.strip().replace("-", " ").split()[-1].casefold() if name.strip() else ""
    for entry in load_suffixes(curated_dir):
        if last_word.endswith(entry.suffix) and len(last_word) - len(entry.suffix) >= MIN_STEM:
            return entry
    return None

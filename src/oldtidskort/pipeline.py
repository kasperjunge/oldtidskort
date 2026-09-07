"""Kører kilder end-to-end: fetch -> parse -> validate -> skriv datasæt."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .core.geo import in_denmark
from .core.io import PROCESSED_DIR, RAW_DIR, write_dataset
from .core.models import Site
from .sources import REGISTRY


@dataclass
class BuildReport:
    source: str
    kept: int = 0
    dropped_duplicate: int = 0
    dropped_outside_dk: int = 0
    paths: list[Path] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"{self.source}: {self.kept} punkter "
            f"(frasorteret {self.dropped_duplicate} dubletter, "
            f"{self.dropped_outside_dk} uden for Danmark)"
        )


def validate(sites: Iterable[Site], report: BuildReport | None = None) -> Iterator[Site]:
    """Frasorterer dubletter og punkter uden for Danmark."""
    seen: set[str] = set()
    for site in sites:
        if site.id in seen:
            if report:
                report.dropped_duplicate += 1
            continue
        if not in_denmark(site.lon, site.lat):
            if report:
                report.dropped_outside_dk += 1
            continue
        seen.add(site.id)
        if report:
            report.kept += 1
        yield site


def build(
    source_name: str,
    raw_dir: Path = RAW_DIR,
    out_dir: Path = PROCESSED_DIR,
    refresh: bool = False,
) -> BuildReport:
    source = REGISTRY[source_name]
    report = BuildReport(source=source_name)
    raw_path = source.fetch(raw_dir, refresh=refresh)
    sites = list(validate(source.parse(raw_path), report))
    if not sites:
        raise ValueError(f"{source_name} gav ingen gyldige punkter; eksisterende output bevares")
    report.paths = write_dataset(sites, source_name, out_dir)
    return report


def build_all(
    raw_dir: Path = RAW_DIR, out_dir: Path = PROCESSED_DIR, refresh: bool = False
) -> tuple[list[BuildReport], list[Path]]:
    """Bygger alle kilder og et samlet `alle_lokaliteter`-datasæt til kortet."""
    reports = [build(name, raw_dir, out_dir, refresh=refresh) for name in REGISTRY]
    combined: list[Site] = []
    for name in REGISTRY:
        source = REGISTRY[name]
        combined.extend(validate(source.parse(source.fetch(raw_dir))))
    paths = write_dataset(combined, "alle_lokaliteter", out_dir)
    return reports, paths

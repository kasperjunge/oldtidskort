from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol, runtime_checkable

from ..core.models import Site


@runtime_checkable
class Source(Protocol):
    """Kontrakt for en datakilde: hent rå data, og oversæt til `Site`."""

    name: str
    license: str
    homepage: str

    def fetch(self, raw_dir: Path) -> Path:
        """Henter rå data ned og returnerer stien til filen (cache-venligt)."""

    def parse(self, raw_path: Path) -> Iterator[Site]:
        """Oversætter rå data til kanoniske `Site`-objekter."""


REGISTRY: dict[str, Source] = {}


def register(source: Source) -> Source:
    REGISTRY[source.name] = source
    return source

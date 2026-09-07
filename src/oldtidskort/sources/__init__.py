"""Én modul pr. datakilde. Alle implementerer `Source`-protokollen i `base.py`."""

# Import for side-effect: registrerer kilderne i REGISTRY.
from . import fund_og_fortidsminder, kirker, runesten  # noqa: F401
from .base import REGISTRY, Source, register

__all__ = ["REGISTRY", "Source", "register"]

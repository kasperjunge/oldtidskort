#!/usr/bin/env python3
"""Build the committed GitHub Pages site locally from processed data."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "data" / "processed" / "fund_og_fortidsminder.geojson",
    ROOT / "data" / "processed" / "runesten_lokationer.geojson",
    ROOT / "data" / "processed" / "bynavne_osm.geojson",
)
WEB = ROOT / "web"
PAGES = ROOT / ".pages-dist"


def compact_feature(feature: dict) -> list:
    props = feature["properties"]
    details = props.get("extra") or {}
    if isinstance(details, str):
        details = json.loads(details)
    record_id = props["id"]
    return [
        *[round(value, 6) for value in feature["geometry"]["coordinates"][:2]],
        record_id,
        props.get("site_type"),
        props.get("name"),
        details.get("anlaegsbetegnelse") or props.get("description"),
        props.get("period", "ukendt"),
        props.get("period_raw"),
        props.get("url"),
        details,
        props.get("municipality"),
    ]


def build(sources: tuple[Path, ...] = SOURCES, destination: Path = PAGES) -> tuple[int, Path]:
    missing = [source for source in sources if not source.exists()]
    if missing:
        names = ", ".join(str(path.relative_to(ROOT)) for path in missing)
        raise SystemExit(
            f"Mangler {names}. Kør først: uv run oldtidskort build fund_og_fortidsminder "
            "&& uv run oldtidskort build bynavne_osm "
            "&& uv run python scripts/build_runestone_research.py"
        )

    features = []
    for source in sources:
        payload = json.loads(source.read_text(encoding="utf-8"))
        features.extend(compact_feature(feature) for feature in payload["features"])

    if destination.exists():
        shutil.rmtree(destination)
    (destination / "data").mkdir(parents=True)
    for filename in ("index.html", "style.css", "app.js"):
        shutil.copy2(WEB / filename, destination / filename)
    (destination / ".nojekyll").touch()

    target = destination / "data" / "lokaliteter.json"
    target.write_text(
        json.dumps(
            {"format": "oldtidskort-v2", "features": features},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    return len(features), target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", dest="sources")
    parser.add_argument("--destination", type=Path, default=PAGES)
    args = parser.parse_args()
    count, target = build(tuple(args.sources) if args.sources else SOURCES, args.destination)
    print(f"Byggede {count:,} punkter → {target.relative_to(ROOT)} ({target.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()

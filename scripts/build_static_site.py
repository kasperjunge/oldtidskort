#!/usr/bin/env python3
"""Build the committed GitHub Pages site locally from processed data."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "processed" / "fund_og_fortidsminder.geojson"
WEB = ROOT / "web"
PAGES = ROOT / ".pages-dist"


def compact_feature(feature: dict) -> list:
    props = feature["properties"]
    details = props.get("extra") or {}
    if isinstance(details, str):
        details = json.loads(details)
    source_id = props["id"].rsplit(":", 1)[-1]
    return [
        *[round(value, 6) for value in feature["geometry"]["coordinates"][:2]],
        int(source_id) if source_id.isdigit() else source_id,
        details.get("anlaegsbetegnelse") or props.get("description"),
        props.get("period", "ukendt"),
        props.get("period_raw"),
        bool(details.get("fredet")),
        details.get("stednr"),
    ]


def build(source: Path = SOURCE, destination: Path = PAGES) -> tuple[int, Path]:
    if not source.exists():
        raise SystemExit(
            f"Mangler {source.relative_to(ROOT)}. "
            "Kør først: uv run oldtidskort build fund_og_fortidsminder"
        )

    payload = json.loads(source.read_text(encoding="utf-8"))
    features = [compact_feature(feature) for feature in payload["features"]]

    if destination.exists():
        shutil.rmtree(destination)
    (destination / "data").mkdir(parents=True)
    for filename in ("index.html", "style.css", "app.js"):
        shutil.copy2(WEB / filename, destination / filename)
    (destination / ".nojekyll").touch()

    target = destination / "data" / "gravhoeje.json"
    target.write_text(
        json.dumps(
            {"format": "oldtidskort-v1", "features": features},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    return len(features), target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--destination", type=Path, default=PAGES)
    args = parser.parse_args()
    count, target = build(args.source, args.destination)
    print(f"Byggede {count:,} punkter → {target.relative_to(ROOT)} ({target.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()

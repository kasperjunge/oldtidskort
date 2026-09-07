#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from oldtidskort.research.runestones import (
    build_dataset,
    dataset_counts,
    fetch,
    fetch_runor,
    validate_foreign_keys,
    write_dataset,
    write_location_geojson,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "runestone_research.json"
DESTINATION = ROOT / "data" / "curated" / "runestones"
FORTIDSMINDER = ROOT / "data" / "raw" / "fund_og_fortidsminder.json"
RUNOR = ROOT / "data" / "raw" / "runor_api_2020.json"
GEOJSON = ROOT / "data" / "processed" / "runesten_lokationer.geojson"


def main() -> None:
    parser = argparse.ArgumentParser(description="Byg dokumenteret researchdatasæt for runesten")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--destination", type=Path, default=DESTINATION)
    parser.add_argument("--fortidsminder", type=Path, default=FORTIDSMINDER)
    parser.add_argument("--runor", type=Path, default=RUNOR)
    parser.add_argument("--geojson", type=Path, default=GEOJSON)
    args = parser.parse_args()

    raw_path = fetch(args.raw, refresh=args.refresh)
    runor_path = fetch_runor(args.runor, refresh=args.refresh)
    dataset = build_dataset(raw_path, args.fortidsminder, runor_path)
    validate_foreign_keys(dataset)
    write_dataset(dataset, args.destination)
    print(f"map_features: {write_location_geojson(dataset, args.geojson)}")
    for key, value in dataset_counts(dataset).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

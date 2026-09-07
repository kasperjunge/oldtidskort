"""Læsning/skrivning af datasæt. Parquet internt, GeoJSON som leverance."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from .models import Site

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"


def to_geodataframe(sites: Iterable[Site]) -> gpd.GeoDataFrame:
    rows = []
    for site in sites:
        row = site.model_dump(mode="json")
        # GeoJSON har ingen indlejrede objekter; `extra` gemmes som JSON-tekst.
        extra = {k: v for k, v in row["extra"].items() if v is not None}
        row["extra"] = json.dumps(extra, ensure_ascii=False) if extra else None
        rows.append(row)
    df = pd.DataFrame(rows)
    geometry = [Point(xy) for xy in zip(df["lon"], df["lat"], strict=True)]
    return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


def write_dataset(sites: Iterable[Site], name: str, out_dir: Path = PROCESSED_DIR) -> list[Path]:
    """Skriver både GeoJSON (til kort) og Parquet (til analyse)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    gdf = to_geodataframe(sites)
    geojson = out_dir / f"{name}.geojson"
    parquet = out_dir / f"{name}.parquet"
    gdf.to_file(geojson, driver="GeoJSON")
    gdf.drop(columns="geometry").to_parquet(parquet, index=False)
    return [geojson, parquet]

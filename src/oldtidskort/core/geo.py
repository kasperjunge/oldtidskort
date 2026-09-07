"""Geometri-hjælpere: projektion og simple sanity checks."""

from __future__ import annotations

from pyproj import Transformer

# Kilder leverer typisk UTM32N / ETRS89 (EPSG:25832); kortet vil have WGS84.
_UTM32_TO_WGS84 = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)

# Groft bounding box for Danmark inkl. Bornholm, brugt til at fange fejlprojektioner.
DK_BBOX = (7.5, 54.4, 15.5, 57.9)


def utm32_to_wgs84(easting: float, northing: float) -> tuple[float, float]:
    """Returnerer (lon, lat)."""
    lon, lat = _UTM32_TO_WGS84.transform(easting, northing)
    return lon, lat


def in_denmark(lon: float, lat: float) -> bool:
    min_lon, min_lat, max_lon, max_lat = DK_BBOX
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat

import json
import shutil

from oldtidskort.core.models import Site, SiteType
from oldtidskort.pipeline import build_all, validate


def _site(site_id: str, lon: float, lat: float) -> Site:
    return Site(
        id=site_id,
        source="test",
        source_id=site_id,
        site_type=SiteType.GRAVHOEJ,
        lon=lon,
        lat=lat,
    )


def test_validate_fjerner_dubletter_og_udenlandske_punkter():
    sites = [_site("a", 10.0, 56.0), _site("a", 10.0, 56.0), _site("b", 2.35, 48.85)]
    assert [s.id for s in validate(sites)] == ["a"]


def test_build_all_skriver_samlet_datasaet(tmp_path, fixture_path):
    """End-to-end mod fixtures: fetch() genbruger cachet råfil i raw_dir."""
    raw = tmp_path / "raw"
    raw.mkdir()
    for name in ("fund_og_fortidsminder", "kirker_osm", "runesten"):
        shutil.copy(fixture_path(f"{name}.json"), raw / f"{name}.json")

    reports, paths = build_all(raw, tmp_path / "out")

    assert {r.source: r.kept for r in reports} == {
        "fund_og_fortidsminder": 2,
        "kirker_osm": 2,
        "runesten": 2,
    }
    combined = json.loads(paths[0].read_text(encoding="utf-8"))
    assert len(combined["features"]) == 6
    assert combined["features"][0]["geometry"]["type"] == "Point"
    assert {p.suffix for p in paths} == {".geojson", ".parquet"}

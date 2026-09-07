import json
import runpy
from pathlib import Path

BUILD_SCRIPT = Path(__file__).parents[1] / "scripts" / "build_static_site.py"


def _collection(site_type: str, source_id: str) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10.0, 56.0]},
            "properties": {
                "id": f"source:{source_id}", "site_type": site_type, "name": "Et sted",
                "period": "vikingetid", "period_raw": "970", "municipality": "Vejle",
                "url": "https://example.com", "extra": '{"katalognummer":"DR 1"}',
            },
        }],
    }


def test_static_site_indeholder_gravminder_og_runesten(tmp_path):
    build = runpy.run_path(str(BUILD_SCRIPT), run_name="build_static_site")["build"]
    mounds = tmp_path / "mounds.geojson"
    stones = tmp_path / "stones.geojson"
    mounds.write_text(json.dumps(_collection("gravhoej", "1")), encoding="utf-8")
    stones.write_text(json.dumps(_collection("runesten", "Q1")), encoding="utf-8")

    count, target = build((mounds, stones), tmp_path / "site")

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert count == 2
    assert payload["format"] == "oldtidskort-v2"
    assert {row[3] for row in payload["features"]} == {"gravhoej", "runesten"}
    assert payload["features"][1][9]["katalognummer"] == "DR 1"

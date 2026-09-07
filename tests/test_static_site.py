import json
import re
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


def test_static_site_indeholder_alle_fire_lag(tmp_path):
    build = runpy.run_path(str(BUILD_SCRIPT), run_name="build_static_site")["build"]
    mounds = tmp_path / "mounds.geojson"
    stones = tmp_path / "stones.geojson"
    places = tmp_path / "places.geojson"
    mounds.write_text(json.dumps(_collection("gravhoej", "1")), encoding="utf-8")
    stones.write_text(json.dumps(_collection("runesten", "Q1")), encoding="utf-8")
    places.write_text(json.dumps(_collection("bynavn", "node/1")), encoding="utf-8")

    churches = tmp_path / "churches.geojson"
    churches.write_text(json.dumps(_collection("kirke", "way/1")), encoding="utf-8")

    count, target = build((mounds, stones, places, churches), tmp_path / "site")

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert count == 4
    assert payload["format"] == "oldtidskort-v2"
    assert {row[3] for row in payload["features"]} == {"gravhoej", "runesten", "bynavn", "kirke"}
    assert payload["features"][1][9]["katalognummer"] == "DR 1"


def test_aktiver_faar_versionsstempel_saa_cache_ikke_blander_udgaver(tmp_path):
    """index.html, app.js og datafilen skal skifte i takt.

    Uden versionen kan en browser genbruge en cachet app.js sammen med en ny
    index.html; kortet tegner, men panelets elementer er skiftet ud.
    """
    build = runpy.run_path(str(BUILD_SCRIPT), run_name="build_static_site")["build"]
    mounds = tmp_path / "mounds.geojson"
    mounds.write_text(json.dumps(_collection("gravhoej", "1")), encoding="utf-8")

    _, target = build((mounds,), tmp_path / "site")
    site = target.parent.parent

    index = (site / "index.html").read_text(encoding="utf-8")
    stamp = re.search(r'\./app\.js\?v=([0-9a-f]{10})"', index).group(1)
    assert f'./style.css?v={stamp}' in index
    assert f'"./data/lokaliteter.json?v={stamp}"' in (site / "app.js").read_text(encoding="utf-8")

    # Filnavnet er uændret; deploy-scriptet verificerer netop den sti.
    assert target.name == "lokaliteter.json"


def test_versionsstempel_aendrer_sig_med_indholdet(tmp_path):
    build = runpy.run_path(str(BUILD_SCRIPT), run_name="build_static_site")["build"]
    stamps = []
    for index, source_id in enumerate(("1", "2")):
        mounds = tmp_path / f"mounds{index}.geojson"
        mounds.write_text(json.dumps(_collection("gravhoej", source_id)), encoding="utf-8")
        _, target = build((mounds,), tmp_path / f"site{index}")
        html = (target.parent.parent / "index.html").read_text(encoding="utf-8")
        stamps.append(re.search(r'\./app\.js\?v=([0-9a-f]{10})"', html).group(1))
    assert stamps[0] != stamps[1]

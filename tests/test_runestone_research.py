import json

from oldtidskort.research.models import LocationRole
from oldtidskort.research.runestones import build_dataset, validate_foreign_keys


def test_researchdatasæt_dokumenterer_alle_stedroller(tmp_path, fixture_path):
    raw = tmp_path / "runesten.json"
    payload = json.loads(fixture_path("runesten.json").read_text(encoding="utf-8"))
    payload["results"]["bindings"] = payload["results"]["bindings"][:2]
    raw.write_text(json.dumps(payload), encoding="utf-8")

    dataset = build_dataset(raw, accessed_at="2026-09-07")
    validate_foreign_keys(dataset)

    for stone in dataset.stones:
        roles = {item.role for item in dataset.locations if item.stone_id == stone.stone_id}
        assert roles == {LocationRole.ORIGINAL, LocationRole.FINDSPOT, LocationRole.CURRENT}
    assert all(item.rationale for item in dataset.locations)
    assert all(item.source_statement and item.interpretation for item in dataset.evidence)


def test_fortidsminder_bevares_som_uklassificeret_registerpunkt(tmp_path, fixture_path):
    wikidata = tmp_path / "runesten.json"
    wikidata.write_text('{"results":{"bindings":[]}}', encoding="utf-8")
    fortidsminder = tmp_path / "fortidsminder.json"
    fortidsminder.write_text(
        json.dumps({
            "features": [{
                "geometry": {"type": "Point", "coordinates": [10.0, 56.0]},
                "properties": {
                    "anlaegstype": "Runesten", "systemnr": 42,
                    "stednr": "123456", "loknr": 7,
                },
            }],
        }),
        encoding="utf-8",
    )

    dataset = build_dataset(wikidata, fortidsminder, accessed_at="2026-09-07")

    assert len(dataset.registered_observations) == 1
    assert not dataset.identity_links
    assert not [item for item in dataset.locations if item.role is LocationRole.REGISTERED]
    assert "ikke automatisk en stenidentitet" in dataset.registered_observations[0].interpretation

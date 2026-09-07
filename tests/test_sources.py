"""Parser-tests mod gemte svar fra de rigtige kilder (se tests/fixtures/)."""

from oldtidskort.core.models import Period, SiteType
from oldtidskort.sources import REGISTRY
from oldtidskort.sources.kirker import parse_osm_year


def test_fund_og_fortidsminder_filtrerer_og_omprojicerer(fixture_path):
    sites = list(REGISTRY["fund_og_fortidsminder"].parse(
        fixture_path("fund_og_fortidsminder.json")
    ))
    # Vejstenen er ikke en gravhøj og skal frasorteres.
    assert [s.source_id for s in sites] == ["170403-12", "020101-5"]
    assert sites[0].period is Period.BRONZEALDER
    assert sites[0].site_type is SiteType.GRAVHOEJ
    # Anden feature kom i UTM32N og skal være omprojiceret til Danmark i WGS84.
    assert 8 < sites[1].lon < 13
    assert 55 < sites[1].lat < 57


def test_fund_og_fortidsminder_bruger_unikt_produktions_id(tmp_path):
    """Flere monumenter må gerne dele stednummer uden at blive dubletter."""
    import json

    payload = {
        "features": [
            {
                "id": f"fundogfortidsminder_punkt_fredet.{point_id}",
                "geometry": {"type": "Point", "coordinates": [10.0 + point_id / 1000, 56.0]},
                "properties": {
                    "lokalitet_punkt_lbnr": point_id,
                    "systemnr": systemnr,
                    "stednr": "060303",
                    "anlaegstype": "Rundhøj",
                    "datering": "Oldtid",
                    "url": f"https://example.test/Lokalitet/{systemnr}",
                },
            }
            for point_id, systemnr in ((101, 23), (102, 24))
        ]
    }
    path = tmp_path / "production.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    sites = list(REGISTRY["fund_og_fortidsminder"].parse(path))

    assert [site.source_id for site in sites] == ["23", "24"]
    assert len({site.id for site in sites}) == 2
    assert sites[0].extra == {
        "anlaegsbetegnelse": "Rundhøj",
        "fredet": True,
        "stednr": "060303",
    }
    assert str(sites[0].url) == "https://example.test/Lokalitet/23"


def test_kirker_parser_center_og_datering(fixture_path):
    sites = list(REGISTRY["kirker_osm"].parse(fixture_path("kirker_osm.json")))
    # Relationen uden geometri skal springes over.
    assert [s.name for s in sites] == ["Jelling Kirke", "Ny Kirke"]
    assert sites[0].year_from == 1001
    assert sites[0].period is Period.MIDDELALDER
    assert sites[1].period is Period.RENAESSANCE
    assert sites[0].url is not None


def test_kirker_aarstal_varianter():
    assert parse_osm_year("C12") == 1101
    assert parse_osm_year("~1150") == 1150
    assert parse_osm_year("1180-01-01") == 1180
    assert parse_osm_year("ukendt") is None
    assert parse_osm_year(None) is None


def test_runesten_fra_wikidata(fixture_path):
    source = REGISTRY["runesten"]
    sites = list(source._parse_wikidata(fixture_path("runesten.json")))
    # Ikke-punkt-geometrien skal springes over.
    assert [s.source_id for s in sites] == ["Q207404", "Q123456"]
    assert sites[0].year_from == 965
    assert sites[0].extra["katalognummer"] == "DR 42"
    # Uden datering antager vi vikingetid.
    assert sites[1].period is Period.VIKINGETID


def test_kurateret_runesten_overskriver_wikidata_uden_dublet(tmp_path, fixture_path):
    raw_path = tmp_path / "runesten.json"
    raw_path.write_text(fixture_path("runesten.json").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "runesten.csv").write_text(
        "dr_nummer,navn,lon,lat,datering,kommune,kilde_url\n"
        "DR42,Den opdaterede Jellingsten,9.419,55.756,970,Vejle,https://example.com/dr42\n",
        encoding="utf-8",
    )

    sites = list(REGISTRY["runesten"].parse(raw_path))

    matches = [site for site in sites if site.extra.get("katalognummer") == "DR42"]
    assert len(matches) == 1
    assert matches[0].id == "runesten:Q207404"
    assert matches[0].name == "Den opdaterede Jellingsten"
    assert str(matches[0].url) == "https://example.com/dr42"

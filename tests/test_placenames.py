"""Endelsesklassifikationen mod det kuraterede datasæt."""

import pytest

from oldtidskort.core.models import Period
from oldtidskort.core.placenames import classify, load_suffixes


@pytest.mark.parametrize(
    ("name", "family", "period"),
    [
        ("Herlev", "lev", Period.JERNALDER),
        ("Store Heddinge", "inge", Period.JERNALDER),
        ("Farum", "um", Period.JERNALDER),
        ("Sæby", "by", Period.VIKINGETID),
        ("Vinderup", "torp", Period.VIKINGETID),
        ("Gentofte", "toft", Period.VIKINGETID),
        ("Birkerød", "roed", Period.MIDDELALDER),
    ],
)
def test_endelser_dateres(name, family, period):
    result = classify(name)
    assert result is not None
    assert result.family == family
    assert result.period is period


def test_laengste_endelse_vinder():
    """'-strup' er en torp-form og må ikke matche som '-rup' eller '-up'."""
    assert classify("Vindstrup").suffix == "strup"


def test_sammensat_navn_vurderes_paa_sidste_ord():
    assert classify("Kirke Hyllinge").family == "inge"


def test_ukendt_endelse_giver_ingen_datering():
    assert classify("Randers") is None
    assert classify(None) is None
    assert classify("") is None


def test_for_kort_stamme_matcher_ikke():
    """'Tofte' er for kort til at endelsen kan udskilles med sikkerhed."""
    assert classify("Tofte") is None


def test_undtagelsesliste_gaar_forud_for_automatikken():
    # Rødovre ender lydligt på -rød-mønstret, men er ikke et rydningsnavn.
    assert classify("Rødovre") is None
    # Rødby har rød- som forled; endelsen er -by.
    assert classify("Rødby").family == "by"


def test_alle_endelser_har_gyldig_periode_og_sikkerhed():
    for entry in load_suffixes():
        assert entry.confidence in {"high", "medium", "low"}
        assert isinstance(entry.period, Period)
        if entry.year_from is not None and entry.year_to is not None:
            assert entry.year_from < entry.year_to

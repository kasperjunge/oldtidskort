from oldtidskort.core.models import Period
from oldtidskort.core.periods import parse_period


def test_genkender_kendte_perioder():
    assert parse_period("Yngre vikingetid") is Period.VIKINGETID
    assert parse_period("Middelalder, 1200-tallet") is Period.MIDDELALDER
    assert parse_period(None) is Period.UKENDT
    assert parse_period("noget helt andet") is Period.UKENDT

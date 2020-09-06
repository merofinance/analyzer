from decimal import Decimal as D

import pytest

from backd.tokens.dai.dsr import DSR, DSR_DIVISOR


@pytest.mark.parametrize("block_number,expected", [
    (100, D("1") * DSR_DIVISOR),
    (101, D("1") * DSR_DIVISOR),
    (104, D("1") * DSR_DIVISOR),
    (105, D("1.1") * DSR_DIVISOR),
    (106, D("1.1") * DSR_DIVISOR),
    (109, D("1.1") * DSR_DIVISOR),
    (110, D("1.5") * DSR_DIVISOR),
    (112, D("1.5") * DSR_DIVISOR),
])
def test_dsr_get(dsr_rates, block_number, expected):
    dsr = DSR(dsr_rates)
    assert dsr.get(block_number) == expected

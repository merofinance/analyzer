from decimal import Decimal as D

import pytest

from backd.tokens.dai.dsr import DSR


@pytest.mark.parametrize("block_number,expected", [
    (100, D("1")),
    (101, D("1")),
    (104, D("1")),
    (105, D("1.1")),
    (106, D("1.1")),
    (109, D("1.1")),
    (110, D("1.5")),
    (112, D("1.5")),
])
def test_dsr_get(dsr_rates, block_number, expected):
    dsr = DSR(dsr_rates)
    assert dsr.get(block_number) == expected

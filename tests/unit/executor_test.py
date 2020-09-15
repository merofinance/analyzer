from decimal import Decimal
from unittest.mock import patch

from backd import executor

from tests.conftest import DUMMY_MARKETS_META


MAIN_MARKET = "0x1A3B"


@patch("backd.constants.COMPOUND_MARKETS", DUMMY_MARKETS_META)
def test_process_all_events():
    state = executor.process_all_events(
        "compound", min_block=120, max_block=125)
    market = state.markets.find_by_address(MAIN_MARKET)
    liquidator_user_balance = market.users["0xab31"].balances
    assert liquidator_user_balance.token_balance == 55
    assert market.collateral_factor == Decimal("0.4")

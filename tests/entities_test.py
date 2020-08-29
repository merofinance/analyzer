from typing import List

import pytest

from miru.entities import PointInTime, UserMarket, UserMarkets


def test_point_in_time_from_event(compound_redeem_event):
    point_in_time = PointInTime.from_event(compound_redeem_event)
    assert point_in_time.block_number == 10590848
    assert point_in_time.transaction_index == 114
    assert point_in_time.log_index == 110


def test_find_market_by_address(markets):
    user_markets = UserMarkets(markets)
    market = user_markets.find_by_address("0xA234")
    assert market == markets[0]
    assert id(market) != id(markets[0])
    assert market.total_borrowed == 1
    assert market.total_supplied == 2

    new_address = "0xXXXX"
    market = user_markets.find_by_address(new_address)
    assert market.address == new_address.lower()
    assert market.total_borrowed == 0
    assert market.total_supplied == 0


def test_replace_market(markets: List[UserMarket]):
    user_markets = UserMarkets(markets)
    first_market_address = markets[0].address
    updated_market = UserMarket(first_market_address, 2, 3)
    updated_user_markets = user_markets.replace_or_add_market(updated_market)
    assert len(updated_user_markets) == 2
    replaced_market = updated_user_markets.find_by_address(first_market_address)
    assert replaced_market.total_borrowed == 2
    assert replaced_market.total_supplied == 3

    new_address = "0xXXXX"
    new_market = UserMarket(new_address, 4, 5)
    new_user_markets = user_markets.replace_or_add_market(new_market)
    assert len(new_user_markets) == 3
    replaced_market = new_user_markets.find_by_address(new_address.lower())
    assert replaced_market.total_borrowed == 4
    assert replaced_market.total_supplied == 5

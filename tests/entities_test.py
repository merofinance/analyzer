import pytest

from miru.entities import PointInTime, Market, Markets


def test_point_in_time_from_event(compound_redeem_event):
    point_in_time = PointInTime.from_event(compound_redeem_event)
    assert point_in_time.block_number == 10590848
    assert point_in_time.transaction_index == 114
    assert point_in_time.log_index == 110


def test_find_market_by_address(markets: Markets):
    market = markets.find_by_address("0xA234")
    assert market == markets[0]
    assert id(market) == id(markets[0])
    assert market.balances.total_borrowed == 1
    assert market.balances.total_supplied == 2

    with pytest.raises(ValueError):
        markets.find_by_address("0xXXXX")


def test_add_market(markets: Markets):
    new_market = Market("0xABC123")
    markets.add_market(new_market)
    assert len(markets) == 4

    with pytest.raises(ValueError):
        markets.add_market(new_market)
    assert len(markets) == 4

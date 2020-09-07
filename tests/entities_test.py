import pytest

from backd.entities import PointInTime, Market, Markets, Oracles, Oracle, MarketUser, UserBalances


def test_point_in_time_from_event(compound_redeem_event):
    point_in_time = PointInTime.from_event(compound_redeem_event)
    assert point_in_time.block_number == 10590848
    assert point_in_time.transaction_index == 114
    assert point_in_time.log_index == 110


def test_user_borrowed_at():
    user = MarketUser(balances=UserBalances(total_borrowed=100))
    assert user.borrowed_at(int(11e17)) == 110


def test_markets_find_market_by_address(markets: Markets):
    market = markets.find_by_address("0xA234")
    assert market == markets[0]
    assert id(market) == id(markets[0])
    assert market.balances.total_borrowed == 1
    assert market.balances.total_supplied == 2

    with pytest.raises(ValueError):
        markets.find_by_address("0xXXXX")


def test_markets_add_market(markets: Markets):
    new_market = Market("0xABC123")
    markets.add_market(new_market)
    assert len(markets) == 4

    with pytest.raises(ValueError):
        markets.add_market(new_market)
    assert len(markets) == 4


def test_oracles_get_oracle():
    oracles = Oracles()
    assert len(oracles) == 0
    oracle = oracles.get_oracle("0x1234")
    assert isinstance(oracle, Oracle)
    assert len(oracles) == 1


def test_oracle_get_price():
    asset = "0x1abc"
    oracle = Oracle()
    assert oracle.get_price(asset) == 0
    oracle.update_price(asset, 100)
    assert oracle.get_price(asset) == 100

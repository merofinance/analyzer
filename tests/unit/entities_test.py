from decimal import Decimal

import pytest

from backd.entities import PointInTime, Market, Markets, Oracles, Oracle, MarketUser
from backd.entities import Balances, UserBalances


def test_point_in_time_from_event(compound_redeem_event):
    point_in_time = PointInTime.from_event(compound_redeem_event)
    assert point_in_time.block_number == 10590848
    assert point_in_time.transaction_index == 114
    assert point_in_time.log_index == 110


def test_point_in_time_order():
    assert PointInTime(1, 2, 3) < PointInTime(2, 0, 0)
    assert PointInTime(1, 2, 3) < PointInTime(1, 3, 1)
    assert PointInTime(1, 2, 1) < PointInTime(1, 2, 3)


def test_user_borrowed_at():
    user = MarketUser(balances=UserBalances(total_borrowed=100))
    assert user.borrowed_at(11 * 10 ** 17) == 110


def test_markets_find_market_by_address(markets: Markets):
    market = markets.find_by_address("0xA234")
    assert market == markets[0]
    assert id(market) == id(markets[0])
    assert market.balances.total_borrowed == 1
    assert market.balances.total_underlying == 2

    with pytest.raises(ValueError):
        markets.find_by_address("0xXXXX")


def test_markets_add_market(markets: Markets):
    new_market = Market("0xABC123")
    markets.add_market(new_market)
    assert len(markets) == 4

    with pytest.raises(ValueError):
        markets.add_market(new_market)
    assert len(markets) == 4


def test_market_underlying_exchange_rate():
    # values take at block 10827297 from
    # https://etherscan.io/token/0x5d3a536e4d6dbd6114cc1ead35777bab948e3643#readContract
    balances = Balances(
        total_underlying=126481409090838027046951927,
        total_borrowed=523702215450739537804145681,
        token_balance=3147635947303247595,
    )
    market = Market(address="0x", reserves=527492004048007051547203, balances=balances)
    assert market.underlying_exchange_rate == 206394940016530694621454013


def test_oracles_get_oracle():
    oracles = Oracles(Markets())
    assert len(oracles) == 0
    oracle = oracles.get_oracle("0xab23")
    assert isinstance(oracle, Oracle)
    assert len(oracles) == 1

    with pytest.raises(ValueError):
        oracles.get_oracle("0x12341234") # address must exist


def test_oracle_get_price():
    asset = "0x1abc"
    oracle = Oracle(Markets())
    assert oracle.get_price(asset) == 0
    oracle.update_price(asset, 100)
    assert oracle.get_price(asset) == 100


def test_oracle_update_price():
    asset = "0x1abc"
    oracle = Oracle(Markets())
    oracle.update_price(asset, 100)
    assert oracle.get_price(asset) == 100
    oracle.update_price(asset, int(2e18), inverted=True)  # 2
    assert oracle.get_price(asset) == int(5e17)  # 0.5

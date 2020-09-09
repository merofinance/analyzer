from unittest.mock import patch

from backd.protocols.compound import oracles
from backd.entities import Markets, Market
from backd.constants import COMPOUND_MARKETS


def test_is_token():
    assert oracles.is_token("0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5", "ETH")
    assert oracles.is_token("0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5", "ETH")

    assert not oracles.is_token("0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5", "USDC")

    assert not oracles.is_token("0x01234", "ETH")


def test_price_oracle_v1():
    oracle = oracles.PriceOracleV1(Markets())
    oracle.update_price("0x1234", 1)
    assert oracle.get_price("0x1234") == 1

    # should be shared between instances
    oracle = oracles.PriceOracleV1(Markets())
    assert oracle.get_price("0x1234") == 1

def test_price_oracle_v1_underlying_price():
    sample_market = COMPOUND_MARKETS[0]
    address = sample_market["address"]
    underlying_address = sample_market["underlying_address"]
    oracle = oracles.PriceOracleV1(Markets())
    oracle.update_price(underlying_address, 100)
    assert oracle.get_price(underlying_address) == 100

    assert oracle.get_underlying_price("0x123456") == 0
    assert oracle.get_underlying_price(address) == 0
    oracle.markets = Markets([Market(address, listed=False)])
    assert oracle.get_underlying_price(address) == 0
    oracle.markets = Markets([Market(address, listed=True)])
    assert oracle.get_underlying_price(address) == 100


def test_price_oracle_v11():
    oracle = oracles.PriceOracleV1(Markets())
    oracle.update_price("0x1234", 1)
    assert oracle.get_price("0x1234") == 1

    # should be shared with subclasses
    oracle = oracles.PriceOracleV11(Markets())
    assert oracle.get_price("0x1234") == 1


def test_price_oracle_v12():
    oracle = oracles.PriceOracleV12(Markets())
    oracle.update_price(oracles.USDC_ORACLE_KEY, 100)
    assert oracle.get_underlying_price(ctoken_address("USDC")) == 100


def test_price_oracle_v13():
    oracle = oracles.PriceOracleV13(Markets())
    oracle.update_price(oracles.PriceOracleV13.maker_usd_oracle_key, 50)
    assert oracle.get_underlying_price(ctoken_address("USDC")) == int(50e12)

    # values taken at block 9012401
    oracle.update_price(oracle.maker_usd_oracle_key, 6505757595471992)
    oracle.update_price(oracles.USDC_ORACLE_KEY, 6543771170404755000000000000)
    oracle.update_price(oracles.DAI_ORACLE_KEY, 6509366069108860)
    assert oracle.get_underlying_price(ctoken_address("SAI")) == 6471552357658807


def test_price_oracle_v14():
    oracle = oracles.PriceOracleV14(Markets())
    # values taken at block 9012401
    oracle.update_price(oracle.maker_usd_oracle_key, 6505757595471992)
    oracle.update_price(oracles.USDC_ORACLE_KEY, 6543771170404755000000000000)
    oracle.update_price(oracles.DAI_ORACLE_KEY, 6509366069108860)
    assert oracle.get_underlying_price(ctoken_address("SAI")) == 6471552357658807
    assert oracle.get_underlying_price(ctoken_address("DAI")) == 6471552357658807


def test_price_oracle_v15():
    oracle = oracles.PriceOracleV15(Markets())
    assert oracle.get_underlying_price(ctoken_address("ETH")) == int(1e18)
    oracle.update_price(oracles.USDC_ORACLE_KEY, 101)
    oracle.update_price(oracles.DAI_ORACLE_KEY, 99)
    assert oracle.get_underlying_price(ctoken_address("USDC")) == 101
    assert oracle.get_underlying_price(ctoken_address("DAI")) == 99


def test_price_oracle_v16():
    oracle = oracles.PriceOracleV16(Markets())
    oracle.update_price(oracles.USDC_ORACLE_KEY, 101)
    assert oracle.get_underlying_price(ctoken_address("USDT")) == 101
    with patch.object(oracles.PriceOracleV15, "get_underlying_price", return_value=10) as mock_method:
        assert oracle.get_underlying_price(ctoken_address("DAI")) == 10
        mock_method.assert_called_once_with(ctoken_address("DAI"))


def ctoken_address(symbol: str) -> str:
    return find_market(symbol)["address"]


def find_market(symbol: str) -> dict:
    return [m for m in COMPOUND_MARKETS if m["underlying_symbol"] == symbol][0]

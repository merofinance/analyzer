from enum import Enum
from dataclasses import dataclass


from ... import constants
from ...entities import Oracle
from ...logger import logger


MARKETS_BY_CTOKEN = {m["address"]: m for m in constants.COMPOUND_MARKETS}

USDC_ORACLE_KEY = "0x0000000000000000000000000000000000000001"
DAI_ORACLE_KEY = "0x0000000000000000000000000000000000000002"

ETH_BASE_UNIT = int(1e18)


def is_token(ctoken: str, symbol: str) -> bool:
    ctoken = ctoken.lower()
    if ctoken not in MARKETS_BY_CTOKEN:
        return False
    return MARKETS_BY_CTOKEN[ctoken]["underlying_symbol"] == symbol


def find_market(symbol: str) -> dict:
    for market in MARKETS_BY_CTOKEN.values():
        if market["underlying_symbol"] == symbol:
            return market
    raise ValueError(f"no such token: {symbol}")


_oracle_prices = {}


@Oracle.register("0x02557a5e05defeffd4cae6d83ea3d173b272c904")
class PriceOracleV1(Oracle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, prices=_oracle_prices, **kwargs)

    def get_underlying_price(self, ctoken: str) -> int:
        if not self.is_listed(ctoken):
            return 0
        market = MARKETS_BY_CTOKEN.get(ctoken.lower(), {})
        return self.get_price(market.get("underlying_address", ""))

    def is_listed(self, ctoken: str) -> bool:
        ctoken = ctoken.lower()
        try:
            market = self.markets.find_by_address(ctoken)
            return market.listed and ctoken in MARKETS_BY_CTOKEN
        except ValueError:
            return False


@Oracle.register("0x28f829f473638ba82710c8404a778f9a66029aad")
class PriceOracleV11(PriceOracleV1):
    def get_underlying_price(self, ctoken: str) -> int:
        if is_token(ctoken, "ETH"):
            return ETH_BASE_UNIT
        return super().get_underlying_price(ctoken)


@Oracle.register("0xe7664229833ae4abf4e269b8f23a86b657e2338d")
class PriceOracleV12(PriceOracleV1):
    def get_underlying_price(self, ctoken: str) -> int:
        if is_token(ctoken, "ETH"):
            return ETH_BASE_UNIT
        if is_token(ctoken, "USDC"):
            return super().get_price(USDC_ORACLE_KEY)
        return super().get_underlying_price(ctoken)


@Oracle.register("0x2c9e6bdaa0ef0284eecef0e0cc102dcdeae4887e")
class PriceOracleV13(PriceOracleV1):
    maker_usd_oracle_key = "0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359"

    def get_underlying_price(self, ctoken: str) -> int:
        if is_token(ctoken, "ETH"):
            return ETH_BASE_UNIT

        if is_token(ctoken, "USDC"):
            return super().get_price(self.maker_usd_oracle_key) * int(1e12)

        if is_token(ctoken, "SAI"):
            return self._compute_dai_price()

        return super().get_underlying_price(ctoken)

    def _compute_dai_price(self) -> int:
        maker_usd_price = super().get_price(self.maker_usd_oracle_key)
        posted_usdc_price = super().get_price(USDC_ORACLE_KEY)
        posted_scaled_dai_price = super().get_price(DAI_ORACLE_KEY) * int(1e12)
        dai_usdc_ratio = posted_scaled_dai_price * ETH_BASE_UNIT // posted_usdc_price

        lower_bound = int(0.95e18)
        upper_bound = int(1.05e18)
        if dai_usdc_ratio < lower_bound:
            return maker_usd_price * lower_bound // ETH_BASE_UNIT
        if dai_usdc_ratio > upper_bound:
            return maker_usd_price * upper_bound // ETH_BASE_UNIT
        return maker_usd_price * dai_usdc_ratio // ETH_BASE_UNIT


@Oracle.register("0x1d8aedc9e924730dd3f9641cdb4d1b92b848b4bd")
class PriceOracleV14(PriceOracleV13):
    def get_underlying_price(self, ctoken: str) -> int:
        if is_token(ctoken, "DAI") or is_token(ctoken, "SAI"):
            return self._compute_dai_price()
        return super().get_underlying_price(ctoken)


@Oracle.register("0xda17fbeda95222f331cb1d252401f4b44f49f7a0")
class PriceOracleV15(PriceOracleV1):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sai_price = 0

    def get_underlying_price(self, ctoken: str) -> int:
        if is_token(ctoken, "ETH"):
            return 1e18

        if is_token(ctoken, "USDC"):
            return self.get_price(USDC_ORACLE_KEY)

        if is_token(ctoken, "DAI"):
            return self.get_price(DAI_ORACLE_KEY)

        if is_token(ctoken, "SAI"):
            if self.sai_price > 0:
                return self.sai_price
            return self.get_price(DAI_ORACLE_KEY)

        return super().get_underlying_price(ctoken)


@Oracle.register("0xddc46a3b076aec7ab3fc37420a8edd2959764ec4")
class PriceOracleV16(PriceOracleV15):
    def get_underlying_price(self, ctoken: str) -> int:
        if is_token(ctoken, "USDT"):
            return self.get_price(USDC_ORACLE_KEY)
        return super().get_underlying_price(ctoken)


class PriceSource(Enum):
    FIXED_ETH = 0
    FIXED_USD = 1
    REPORTER = 2


@dataclass
class TokenConfig:
    ctoken: str
    underlying: str
    symbol_hash: str
    base_unit: int
    price_source: int
    fixed_price: int
    uniswap_market: str
    is_uniswap_reversed: bool


@Oracle.register("0x9b8eb8b3d6e2e0db36f41455185fef7049a35cae")
class UniswapAnchorView(Oracle):
    CDAI_CONFIG = TokenConfig(
        ctoken="0x5d3a536e4d6dbd6114cc1ead35777bab948e3643",
        underlying="0x6b175474e89094c44da98b954eedeac495271d0f",
        symbol_hash="a5e92f3efb6826155f1f728e162af9d7cda33a574a1153b58f03ea01cc37e568",
        base_unit=ETH_BASE_UNIT,
        price_source=PriceSource.REPORTER,
        fixed_price=0,
        uniswap_market="0xa478c2975ab1ea89e8196811f51a7b7ade33eb11",
        is_uniswap_reversed=False,
    )

    CETH_CONFIG = TokenConfig(
        ctoken="0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5",
        underlying="0x0000000000000000000000000000000000000000",
        symbol_hash="aaaebeba3810b1e6b70781f14b2d72c1cb89c0b2b320c43bb67ff79f562f5ff4",
        base_unit=ETH_BASE_UNIT,
        price_source=PriceSource.REPORTER,
        fixed_price=0,
        uniswap_market="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
        is_uniswap_reversed=True,
    )

    CBAT_CONFIG = TokenConfig(
        ctoken="0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e",
        underlying="0x0d8775f648430679a709e98d2b0cb6250d2887ef",
        symbol_hash="3ec6762bdf44eb044276fec7d12c1bb640cb139cfd533f93eeebba5414f5db55",
        base_unit=ETH_BASE_UNIT,
        price_source=PriceSource.REPORTER,
        fixed_price=0,
        uniswap_market="0xb6909b960dbbe7392d405429eb2b3649752b4838",
        is_uniswap_reversed=False,
    )

    CSAI_CONFIG = TokenConfig(
        ctoken="0xf5dce57282a584d2746faf1593d3121fcac444dc",
        underlying="0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359",
        symbol_hash="4dcbfd8d7239a822743634e138b90febafc5720cec2dbdc6a0e5a2118ba2c532",
        base_unit=ETH_BASE_UNIT,
        price_source=PriceSource.FIXED_ETH,
        fixed_price=5285000000000000,
        uniswap_market="0x0000000000000000000000000000000000000000",
        is_uniswap_reversed=False,
    )

    CREP_CONFIG = TokenConfig(
        ctoken="0x158079ee67fce2f58472a96584a73c7ab9ac95c1",
        underlying="0x1985365e9f78359a9b6ad760e32412f4a445e862",
        symbol_hash="91a08135082b0a28b4ad8ecc7749a009e0408743a9d1cdf34dd6a58d60ee9504",
        base_unit=ETH_BASE_UNIT,
        price_source=PriceSource.REPORTER,
        fixed_price=0,
        uniswap_market="0xec2d2240d02a8cf63c3fa0b7d2c5a3169a319496",
        is_uniswap_reversed=False,
    )

    CUSDC_CONFIG = TokenConfig(
        ctoken="0x39aa39c021dfbae8fac545936693ac917d5e7563",
        underlying="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        symbol_hash="d6aca1be9729c13d677335161321649cccae6a591554772516700f986f942eaa",
        base_unit=1_000_000,
        price_source=PriceSource.FIXED_USD,
        fixed_price=1_000_000,
        uniswap_market="0x0000000000000000000000000000000000000000",
        is_uniswap_reversed=False,
    )

    CUSDT_CONFIG = TokenConfig(
        ctoken="0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9",
        underlying="0xdac17f958d2ee523a2206206994597c13d831ec7",
        symbol_hash="8b1a1d9c2b109e527c9134b25b1a1833b16b6594f92daa9f6d9b7a6024bce9d0",
        base_unit=1_000_000,
        price_source=PriceSource.FIXED_USD,
        fixed_price=1_000_000,
        uniswap_market="0x0000000000000000000000000000000000000000",
        is_uniswap_reversed=False,
    )

    CWBTC_CONFIG = TokenConfig(
        ctoken="0xc11b1268c1a384e55c48c2391d8d480264a3a7f4",
        underlying="0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        symbol_hash="e98e2830be1a7e4156d656a7505e65d08c67660dc618072422e9c78053c261e9",
        base_unit=100000000,
        price_source=PriceSource.REPORTER,
        fixed_price=0,
        uniswap_market="0xbb2b8038a1640196fbe3e38816f3e67cba72d940",
        is_uniswap_reversed=False,
    )

    CZRX_CONFIG = TokenConfig(
        ctoken="0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407",
        underlying="0xe41d2489571d322189246dafa5ebde1f4699f498",
        symbol_hash="b8612e326dd19fc983e73ae3bc23fa1c78a3e01478574fa7ceb5b57e589dcebd",
        base_unit=ETH_BASE_UNIT,
        price_source=PriceSource.REPORTER,
        fixed_price=0,
        uniswap_market="0xc6f348dd3b91a56d117ec0071c1e9b83c0996de4",
        is_uniswap_reversed=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token_configs = [
            self.CBAT_CONFIG,
            self.CDAI_CONFIG,
            self.CETH_CONFIG,
            self.CREP_CONFIG,
            self.CSAI_CONFIG,
            self.CUSDC_CONFIG,
            self.CUSDT_CONFIG,
            self.CWBTC_CONFIG,
            self.CZRX_CONFIG,
        ]
        self._config_by_ctoken = {c.ctoken: c for c in self.token_configs}
        self._token_to_underlying = {m["underlying_symbol"]: m["underlying_address"]
                                     for m in constants.COMPOUND_MARKETS}

    def get_underlying_price(self, ctoken: str) -> int:
        # Comptroller needs prices in the format: ${raw price} * 1e(36 - baseUnit)
        # Since the prices in this view have 6 decimals, we must scale them by 1e(36 - 6 - baseUnit)
        config = self._config_by_ctoken.get(ctoken)
        if not config:
            return 0
        return 10 ** 30 * self._get_price(config) // config.base_unit

    def _get_price(self, config: TokenConfig) -> int:
        if config.price_source == PriceSource.REPORTER:
            return self.get_price(config.underlying)
        if config.price_source == PriceSource.FIXED_USD:
            return config.fixed_price

        # if config.price_source == PriceSource.FIXED_ETH:
        usd_per_eth = self.get_price(constants.ETH_ADDRESS)
        if usd_per_eth == 0:
            raise ValueError("ETH price not set, cannot convert to dollars")
        return usd_per_eth * config.fixed_price / ETH_BASE_UNIT

    def update_price(self, token: str, price: int, inverted: bool = False):
        if not token.startswith("0x"):
            token = self._token_to_underlying.get(token)
            if not token:
                logger.warning("no such symbol %s", token)
                return
        super().update_price(token, price, inverted=inverted)

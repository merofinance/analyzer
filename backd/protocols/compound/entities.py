from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Tuple, Union

from ...entities import Market, MarketUser, State
from ...tokens.dai.dsr import DSR
from . import constants
from .interest_rate_models import InterestRateModel

EXP_SCALE = 10 ** 18


class InterestRateModels:
    def __init__(
        self, dsr: DSR, interest_rate_models: Dict[str, InterestRateModel] = None
    ):
        if interest_rate_models is None:
            interest_rate_models = {}
        self.dsr = dsr
        self.interest_rate_models = interest_rate_models

    def __len__(self):
        return len(self.interest_rate_models)

    def get_model(self, address: str) -> InterestRateModel:
        address = address.lower()
        if address not in self.interest_rate_models:
            available = ", ".join(self.interest_rate_models.keys())
            raise KeyError(
                f"no model found at address {address}, " f"available: {available}"
            )
        return self.interest_rate_models[address]

    def create_model(self, address: str):
        address = address.lower()
        if address in self.interest_rate_models:
            return
        class_ = InterestRateModel.get(address)
        model = class_(dsr=self.dsr)
        self.interest_rate_models[address] = model
        return model


@dataclass(eq=False, repr=False)
class CDaiMarket(Market):
    dsr_active: bool = False
    pie: int = 0
    chi: int = 10 ** 27

    def get_cash(self):
        # NOTE: when DSR is activated, value is take from DSR contract
        # otherwise, the regular DAI balance is used
        if self.dsr_active:
            return self.current_pie
        return self.balances.total_underlying

    def transfer_in(self, amount: int):
        self.pie += amount * constants.RAY // self.chi

    def transfer_out(self, amount: int):
        self.pie -= amount * constants.RAY // self.chi + 1

    @property
    def current_pie(self):
        return self.pie * self.chi // constants.RAY


@dataclass
class CompoundState(State):
    protocol_name: str = "compound"
    dsr: DSR = None
    close_factor: Decimal = Decimal("0")
    interest_rate_models: InterestRateModels = None

    def __post_init__(self):
        super().__post_init__()
        if self.dsr is None:
            raise ValueError("dsr must always be set")
        if self.interest_rate_models is None:
            self.interest_rate_models = InterestRateModels(self.dsr)

    @classmethod
    def create(cls):
        return cls(dsr=DSR.create())

    def get_user_positions(self, user: str) -> List[Tuple[Market, MarketUser]]:
        positions = []
        for market in self.markets:
            market_user = market.users[user]
            if (
                market_user.balances.total_borrowed > 0
                or market_user.balances.token_balance > 0
            ):
                positions.append((market, market_user))
        return positions

    def compute_user_position(
        self, user: str, include_collateral_factor: bool = True
    ) -> (int, int):
        sum_collateral = 0
        sum_borrows = 0

        for market, market_user in self.get_user_positions(user):
            user_balances = market_user.balances
            exchange_rate = market.underlying_exchange_rate
            collateral_factor = market.collateral_factor
            underlying_to_usd = self.oracles.current.get_underlying_price(
                market.address
            )

            # allow to simulate prices
            if (
                constants.PRICE_RATIOS_KEY in self.extra
                and market.address in self.extra[constants.PRICE_RATIOS_KEY]
            ):
                price_ratio = self.extra[constants.PRICE_RATIOS_KEY][market.address]
                underlying_to_usd = round(price_ratio * underlying_to_usd)

            ctoken_to_underlying = Decimal(exchange_rate / EXP_SCALE)
            if include_collateral_factor:
                ctoken_to_underlying *= collateral_factor

            ctokens_to_usd = round(ctoken_to_underlying * underlying_to_usd)
            sum_collateral += ctokens_to_usd * user_balances.token_balance // EXP_SCALE
            sum_borrows += (
                underlying_to_usd
                * market_user.borrowed_at(market.borrow_index)
                // EXP_SCALE
            )

        return (sum_collateral, sum_borrows)

    def compute_borrows_per_market(self) -> Dict[str, float]:
        borrows = {}
        for market in self.markets:
            oracle_price = self.oracles.current.get_underlying_price(market.address)
            borrows[market.address] = (
                oracle_price * market.balances.total_borrowed / EXP_SCALE
            )
        return borrows

    def compute_total_borrows(self) -> float:
        return sum(self.compute_borrows_per_market().values())

    def compute_underlying_per_market(self) -> Dict[str, float]:
        underlying = {}
        for market in self.markets:
            oracle_price = self.oracles.current.get_underlying_price(market.address)
            underlying[market.address] = oracle_price * market.get_cash() / EXP_SCALE
        return underlying

    def compute_total_underlying(self) -> float:
        return sum(self.compute_underlying_per_market().values())

    def compute_supply_per_market(self) -> Dict[str, float]:
        markets = {}
        for market in self.markets:
            token_balance = market.balances.token_balance
            markets[market.address] = self.ctoken_to_usd(token_balance, market)
        return markets

    def compute_total_supply(self) -> float:
        return sum(self.compute_supply_per_market().values())

    def ctoken_to_usd(self, amount: int, market: Union[Market, str]) -> float:
        if isinstance(market, str):
            market = self.markets.find_by_address(market)
        exchange_rate = market.underlying_exchange_rate
        oracle_price = self.oracles.current.get_underlying_price(market.address)
        tokens_to_usd = exchange_rate * oracle_price / EXP_SCALE
        return tokens_to_usd * amount / EXP_SCALE

    def token_to_usd(self, amount: int, market: Union[Market, str]) -> float:
        if isinstance(market, Market):
            market = market.address
        oracle_price = self.oracles.current.get_underlying_price(market)
        return oracle_price * amount / EXP_SCALE

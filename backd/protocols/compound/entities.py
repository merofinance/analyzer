from dataclasses import dataclass
from decimal import Decimal
from typing import Dict

from ...entities import Market, State
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


@dataclass
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

    def compute_user_position(self, user: str) -> (int, int):
        sum_collateral = 0
        sum_borrows = 0

        for market in self.markets:
            market_user = market.users[user]
            user_balances = market_user.balances
            exchange_rate = market.underlying_exchange_rate
            collateral_factor = market.collateral_factor
            oracle_price = self.oracles.current.get_underlying_price(market.address)

            tokens_to_ether_left = (
                Decimal(round(collateral_factor * exchange_rate)) / EXP_SCALE
            )
            tokens_to_ether = round(tokens_to_ether_left * oracle_price)
            sum_collateral += tokens_to_ether * user_balances.token_balance // EXP_SCALE
            sum_borrows += (
                oracle_price * market_user.borrowed_at(market.borrow_index) // EXP_SCALE
            )

        return (sum_collateral, sum_borrows)

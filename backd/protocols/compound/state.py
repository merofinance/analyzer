from typing import Dict
from dataclasses import dataclass

from ...entities import State
from ...tokens.dai.dsr import DSR
from .interest_rate_models import InterestRate


class InterestRateModels:
    def __init__(self, dsr: DSR, interest_rate_models: Dict[str, InterestRate] = None):
        if interest_rate_models is None:
            interest_rate_models = {}
        self.dsr = dsr
        self.interest_rate_models = interest_rate_models

    def get_model(self, address: str) -> InterestRate:
        address = address.lower()
        if address not in self.interest_rate_models:
            raise KeyError(f"no model found at address {address}")
        return self.interest_rate_models[address]

    def create_model(self, address: str):
        address = address.lower()
        if address in self.interest_rate_models:
            return
        class_ = InterestRate.get(address)
        model = class_(dsr=self.dsr)


@dataclass
class CompoundState(State):
    dsr: DSR = None
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
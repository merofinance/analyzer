from typing import List
from decimal import Decimal


from ... import constants
from . import utils


DSR_DIVISOR = Decimal(10) ** constants.DSR_DECIMALS


class DSR:
    def __init__(self, dsr_rates: List[dict]):
        self.dsr_rates = sorted(dsr_rates, key=lambda row: -row["blockNumber"])

    def get(self, block_number: int):
        for rate_info in self.dsr_rates:
            if rate_info["blockNumber"] <= block_number:
                return rate_info["rate"]
        return self.dsr_rates[-1]["rate"]

    @classmethod
    def create(cls):
        dsr_rates = utils.fetch_dsr_rates()
        return cls(dsr_rates=dsr_rates)

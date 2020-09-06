from typing import List
from decimal import Decimal


from ... import constants


DSR_DIVISOR = Decimal(10) ** constants.DSR_DECIMALS


class DSR:
    def __init__(self, dsr_rates: List[dict]):
        self.dsr_rates = sorted(dsr_rates, key=lambda row: -row["block"])

    def get(self, block_number: int):
        for rate_info in self.dsr_rates:
            if rate_info["block"] <= block_number:
                return rate_info["rate"] / DSR_DIVISOR
        return self.dsr_rates[-1]["rate"] / DSR_DIVISOR

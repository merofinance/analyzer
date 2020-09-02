from typing import List
from decimal import Decimal

from ...entities import State
from ... import constants


DSR_DIVISOR = Decimal(10) ** constants.DSR_DECIMALS


class DSRHook:
    def __init__(self, dsr_rates: List[dict]):
        self.dsr_rates = sorted(dsr_rates, key=lambda row: -row["block"])

    def run(self, state: State):
        try:
            market = state.markets.find_by_address(constants.CDAI_ADDRESS)
            dsr = self.get_dsr(state.current_event_time.block_number)
            new_total = market.balances.total_supplied * dsr
            market.balances.total_supplied = int(new_total)
        except ValueError:
            pass

    def get_dsr(self, block_number: int):
        for rate_info in self.dsr_rates:
            if rate_info["block"] <= block_number:
                return rate_info["rate"] / DSR_DIVISOR
        return self.dsr_rates[-1]["rate"] / DSR_DIVISOR

from ... import constants
from ...tokens.dai.dsr import DSR_DIVISOR
from .state import State


class DSRHook:
    def run(self, state: State):
        try:
            market = state.markets.find_by_address(constants.CDAI_ADDRESS)
            dsr = state.dsr.get(state.current_event_time.block_number)
            new_total = market.balances.total_supplied * dsr / DSR_DIVISOR
            market.balances.total_supplied = int(new_total)
        except ValueError:
            pass

from ... import constants
from ...tokens.dai.dsr import DSR_DIVISOR
from .entities import State


class DSRHook:
    def run(self, state: State):
        try:
            market = state.markets.find_by_address(constants.CDAI_ADDRESS)
            dsr = state.dsr.get(state.current_event_time.block_number)
            new_total = market.balances.total_underlying * dsr / DSR_DIVISOR
            market.balances.total_underlying = int(new_total)
        except ValueError:
            pass

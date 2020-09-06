from ...entities import State
from ... import constants
from ...tokens.dai.dsr import DSR


class DSRHook:
    def __init__(self, dsr: DSR):
        self.dsr = dsr

    def run(self, state: State):
        try:
            market = state.markets.find_by_address(constants.CDAI_ADDRESS)
            dsr = self.dsr.get(state.current_event_time.block_number)
            new_total = market.balances.total_supplied * dsr
            market.balances.total_supplied = int(new_total)
        except ValueError:
            pass

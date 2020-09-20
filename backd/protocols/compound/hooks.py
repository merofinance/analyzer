from . import constants
from ...tokens.dai.dsr import DSR_DIVISOR
from .entities import State
from ...hook import Hook


class DSRHook(Hook):
    def block_start(self, state: State, block_number: int):
        try:
            market = state.markets.find_by_address(constants.CDAI_ADDRESS)
            dsr = state.dsr.get(state.current_event_time.block_number)
            new_total = market.dsr_amount * dsr / DSR_DIVISOR
            market.dsr_amount = int(new_total)
        except ValueError:
            pass

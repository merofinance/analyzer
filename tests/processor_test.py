from miru.event_processor import Processor
from miru.entities import State
from miru.event_processor import process_event


PROTOCOL_NAME = "dummy"


@Processor.register(PROTOCOL_NAME)
class DummyProcessor(Processor):
    def process_event(self, state, event):
        market = state.markets.find_by_address("0xa234")
        market.balances.total_borrowed = 777


def test_process_event(markets, compound_redeem_event):
    state = State(PROTOCOL_NAME, markets=markets)
    process_event(PROTOCOL_NAME, state, compound_redeem_event)
    assert len(state.markets) == len(markets)
    market = state.markets.find_by_address("0xa234")
    assert market.balances.total_borrowed == 777

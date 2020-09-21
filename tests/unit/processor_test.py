from backd.entities import State
from backd.event_processor import Processor

PROTOCOL_NAME = "dummy"


class DummyProcessor(Processor):
    def _process_event(self, state, event):
        market = state.markets.find_by_address("0xa234")
        market.balances.total_borrowed = 777


def test_process_event(markets, compound_redeem_event):
    state = State(PROTOCOL_NAME, markets=markets)
    processor = DummyProcessor()
    processor.process_event(state, compound_redeem_event)
    assert len(state.markets) == len(markets)
    market = state.markets.find_by_address("0xa234")
    assert market.balances.total_borrowed == 777

    # NOTE: should ignore when "event" is not here
    processor.process_event(state, {})

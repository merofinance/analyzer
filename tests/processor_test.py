from backd.event_processor import Processor
from backd.entities import State


PROTOCOL_NAME = "dummy"


@Processor.register(PROTOCOL_NAME)
class DummyProcessor(Processor):
    def _process_event(self, state, event):
        market = state.markets.find_by_address("0xa234")
        market.balances.total_borrowed = 777

    @classmethod
    def create_empty_state(cls) -> State:
        return State(PROTOCOL_NAME)


def test_process_event(markets, compound_redeem_event):
    state = State(PROTOCOL_NAME, markets=markets)
    processor = Processor.get(PROTOCOL_NAME)()
    processor.process_event(state, compound_redeem_event)
    assert len(state.markets) == len(markets)
    market = state.markets.find_by_address("0xa234")
    assert market.balances.total_borrowed == 777

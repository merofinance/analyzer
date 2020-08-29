from miru.event_processor import Processor
from miru.entities import UserMarkets, State
from miru.event_processor import process_event


PROTOCOL_NAME = "dummy"


@Processor.register(PROTOCOL_NAME)
class DummyProcessor(Processor):
    def update_markets(self, state: State, event: dict) -> UserMarkets:
        market = state.markets.find_by_address("0x1234")
        market.total_borrowed += 5
        return state.markets.replace_or_add_market(market)


def test_process_event(compound_redeem_event):
    state = State.empty(PROTOCOL_NAME, "0x00")
    new_state = process_event(PROTOCOL_NAME, state, compound_redeem_event)
    assert len(new_state.markets) == 1
    market = new_state.markets.find_by_address("0x1234")
    assert market.total_borrowed == 5

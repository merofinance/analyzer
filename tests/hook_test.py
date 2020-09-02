from backd.hook import Hooks
from backd.entities import State, PointInTime


class DummyHook:
    def __init__(self):
        self.num = 0

    def run(self, state: State):
        state.markets.add_market(f"0x1234{self.num}")
        self.num += 1


def test_hooks():
    state = State("dummy")
    hooks = Hooks(prehooks=[DummyHook().run])
    state.current_event_time = PointInTime(100, 1, 1)
    hooks.execute_prehooks(state)
    assert len(state.markets) == 1
    hooks.execute_posthooks(state)
    hooks.execute_prehooks(state)
    assert len(state.markets) == 1
    state.current_event_time = PointInTime(101, 1, 1)
    hooks.execute_prehooks(state)
    assert len(state.markets) == 2

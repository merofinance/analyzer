from backd.hook import Hooks, Hook
from backd.entities import State, PointInTime


class DummyHook(Hook):
    def __init__(self):
        self.num = 0

    def block_start(self, state: State, block_number: int):
        state.markets.add_market(f"0x1234{self.num}")
        self.num += 1


def test_hooks():
    state = State("dummy")
    hooks = Hooks(hooks=[DummyHook()])
    state.current_event_time = PointInTime(100, 1, 1)
    hooks.execute_hooks_start(state, {})
    assert len(state.markets) == 1
    hooks.execute_hooks_end(state, {})
    hooks.execute_hooks_start(state, {})
    assert len(state.markets) == 1
    state.current_event_time = PointInTime(101, 1, 1)
    hooks.execute_hooks_start(state, {})
    assert len(state.markets) == 2

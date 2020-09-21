from backd.entities import PointInTime, State
from backd.hook import Hook, Hooks


@Hook.register("dummy")
class DummyHook(Hook):
    def __init__(self):
        self.num = 0

    def block_start(self, state: State, block_number: int):
        state.markets.add_market(f"0x1234{self.num}")
        self.num += 1


@Hook.register("with-dependencies")
class WithDependenciesHook(Hook):
    def __init__(self):
        self.num = 0

    @classmethod
    def list_dependencies(cls):
        return ["dummy"]


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


def test_hook_dependencies():
    hooks = Hooks(hooks=["with-dependencies"])
    assert len(hooks.hooks_info) == 2
    assert hooks.hook_names[0] == "dummy"

    hooks = Hooks(hooks=["with-dependencies", "dummy", "dummy"])
    assert len(hooks.hooks_info) == 2

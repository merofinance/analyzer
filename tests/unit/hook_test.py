from backd.entities import PointInTime, State
from backd.hook import Hook, Hooks, parse_hook


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


@Hook.register("with-single-arg")
class WithSingleArgHook(Hook):
    def __init__(self, num: int):
        self.num = num


@Hook.register("with-multi-arg")
class WithMultiArgHook(Hook):
    def __init__(self, num: int, label: str):
        self.num = num
        self.label = label


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


def test_parse_hook():
    with_no_arg = parse_hook("dummy")
    assert isinstance(with_no_arg, DummyHook)

    with_no_arg = parse_hook("dummy()")
    assert isinstance(with_no_arg, DummyHook)

    with_single_arg = parse_hook("with-single-arg(5)")
    assert isinstance(with_single_arg, WithSingleArgHook)
    assert with_single_arg.num == 5

    with_multi_arg = parse_hook("with-multi-arg(10, 'hello')")
    assert isinstance(with_multi_arg, WithMultiArgHook)
    assert with_multi_arg.num == 10
    assert with_multi_arg.label == "hello"

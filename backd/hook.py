from typing import Callable, List

from .entities import State


Hook = Callable[[State], None]


class Hooks:
    def __init__(self, prehooks: List[Hook] = None, posthooks: List[Hook] = None):
        if prehooks is None:
            prehooks = []
        self.prehooks = prehooks
        if posthooks is None:
            posthooks = []
        self.posthooks = posthooks
        self.last_block = None

    def execute_prehooks(self, state: State):
        self._execute_hooks(state, self.prehooks)

    def execute_posthooks(self, state: State):
        self._execute_hooks(state, self.posthooks)
        self.last_block = state.current_event_time.block_number

    def _execute_hooks(self, state: State, hooks: List[Hook]):
        for hook in hooks:
            if self.last_block != state.current_event_time.block_number:
                hook(state)

from typing import List, Union, Iterable

from .entities import State
from .base_factory import BaseFactory


class Hook(BaseFactory):
    def block_start(self, state: State, block_number: int):
        pass

    def block_end(self, state: State, block_number: int):
        pass

    def transaction_start(self, state: State, block_number: int, transaction_index: int):
        pass

    def transaction_end(self, state: State, block_number: int, transaction_index: int):
        pass

    def event_start(self, state: State, event: dict):
        pass

    def event_end(self, state: State, event: dict):
        pass


class Hooks:
    def __init__(self, hooks: List[Union[Hook, str]] = None):
        if hooks is None:
            hooks = []
        self.hooks = []
        for hook in hooks:
            if isinstance(hook, str):
                hook = Hook.get(hook)()
            self.hooks.append(hook)
        self._last_block = None
        self._last_transaction = None

    def execute_hooks_start(self, state: State, event: dict):
        for hook in self.hooks:
            if self._last_transaction != state.current_event_time.transaction_index:
                hook.transaction_end(
                    state, self._last_block, self._last_transaction)

            if self._last_block != state.current_event_time.block_number:
                hook.block_end(state, self._last_block)
                self._last_block = state.current_event_time.block_number
                hook.block_start(state, self._last_block)

            if self._last_transaction != state.current_event_time.transaction_index:
                self._last_transaction = state.current_event_time.transaction_index
                hook.transaction_start(
                    state, self._last_block, self._last_transaction)

            hook.event_start(state, event)

    def execute_hooks_end(self, state: State, event: dict):
        for hook in self.hooks:
            hook.event_end(state, event)

    def finalize_hooks(self, state: State):
        for hook in self.hooks:
            hook.transaction_end(state, self._last_block,
                                 self._last_transaction)
            hook.block_end(state, self._last_block)

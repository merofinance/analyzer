from abc import ABC, abstractmethod
from typing import List, Union, Iterable

from .entities import State
from .base_factory import BaseFactory


class Hook(ABC, BaseFactory):
    @abstractmethod
    def run(self, state: State):
        pass


class Hooks:
    def __init__(self,
                 prehooks: List[Union[Hook, str]] = None,
                 posthooks: List[Union[Hook, str]] = None):
        self.prehooks = list(self._get_hooks(prehooks))
        self.posthooks = list(self._get_hooks(posthooks))
        self.last_block = None

    def _get_hooks(self, hooks: Union[Hook, str]) -> Iterable[Hook]:
        if hooks is None:
            return
        for hook in hooks:
            if isinstance(hook, str):
                hook = Hook.get(hook)()
            yield hook

    def execute_prehooks(self, state: State):
        self._execute_hooks(state, self.prehooks)

    def execute_posthooks(self, state: State):
        self._execute_hooks(state, self.posthooks)
        self.last_block = state.current_event_time.block_number

    def _execute_hooks(self, state: State, hooks: List[Hook]):
        for hook in hooks:
            if self.last_block != state.current_event_time.block_number:
                hook.run(state)

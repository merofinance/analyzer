from abc import ABC, abstractmethod
from typing import Iterable

from tqdm import tqdm

from . import normalizer
from .entities import PointInTime, State
from .hook import Hooks


class Processor(ABC):
    def __init__(self, hooks: Hooks = None):
        self.hooks = hooks

    def process_events(self, state: State, events: Iterable[dict], pbar: tqdm = None):
        if self.hooks:
            self.hooks.initialize_hooks(state)
        for event in events:
            self.process_event(state, event)
            if pbar:
                pbar.update()
        if self.hooks:
            self.hooks.finalize_hooks(state)

    def process_event(self, state: State, event: dict):
        if "event" not in event:
            return
        event = normalizer.normalize_event(event)
        state.last_event_time = state.current_event_time
        state.current_event_time = PointInTime.from_event(event)
        if self.hooks:
            self.hooks.execute_hooks_start(state, event)
        self._process_event(state, event)
        if self.hooks:
            self.hooks.execute_hooks_end(state, event)

    @abstractmethod
    def _process_event(self, state: State, event: dict):
        pass

from typing import Iterable
from abc import ABC, abstractmethod

from tqdm import tqdm

from .entities import PointInTime, State
from .base_factory import BaseFactory
from .hook import Hooks


class Processor(ABC, BaseFactory):
    def __init__(self, hooks: Hooks = None):
        self.hooks = hooks

    def process_events(self, state: State, events: Iterable[dict], total_count: int = None):
        for event in tqdm(events, total=total_count):
            self.process_event(state, event)

    def process_event(self, state: State, event: dict):
        if "event" not in event:
            return
        state.last_event_time = state.current_event_time
        state.current_event_time = PointInTime.from_event(event)
        if self.hooks:
            self.hooks.execute_prehooks(state)
        self._process_event(state, event)
        if self.hooks:
            self.hooks.execute_posthooks(state)

    @abstractmethod
    def _process_event(self, state: State, event: dict):
        pass

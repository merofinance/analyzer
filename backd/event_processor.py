from typing import List

from .entities import PointInTime, State
from .base_factory import BaseFactory


class Processor(BaseFactory):
    def process_event(self, state: State, event: dict):
        state.last_event_time = state.current_event_time
        state.current_event_time = PointInTime.from_event(event)

    def process_events(self, state: State, events: List[dict]):
        for event in events:
            self.process_event(state, event)


def process_event(protocol_name: str, state: State, event: dict):
    processor: Processor = Processor.create(protocol_name)
    processor.process_event(state, event)

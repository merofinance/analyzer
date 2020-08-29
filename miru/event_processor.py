from abc import ABC, abstractmethod
from typing import List

from .entities import PointInTime, State, UserMarkets
from .base_factory import BaseFactory


class Processor(ABC, BaseFactory):
    def process_event(self, state: State, event: dict) -> State:
        return State(
            protocol_name=self.__registered_name__, # pylint: disable=no-member
            user_address=state.user_address,
            last_event_time=PointInTime.from_event(event),
            markets=self.update_markets(state, event),
        )

    def process_events(self, state: State, events: List[dict]) -> State:
        for event in events:
            state = self.process_event(state, event)
        return state

    @abstractmethod
    def update_markets(self, state: State, event: dict) -> UserMarkets:
        pass


def process_event(protocol_name: str, state: State, event: dict) -> State:
    processor: Processor = Processor.create(protocol_name)
    return processor.process_event(state, event)

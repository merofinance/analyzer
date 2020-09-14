from typing import Iterable
from abc import ABC, abstractmethod

from .event_processor import Processor
from .base_factory import BaseFactory
from .hook import Hooks
from .entities import State


class Protocol(ABC, BaseFactory):
    @abstractmethod
    def create_processor(self, hooks: Hooks = None) -> Processor:
        pass

    @abstractmethod
    def create_empty_state(self) -> State:
        pass

    @abstractmethod
    def count_events(self, min_block: int = None, max_block: int = None) -> int:
        pass

    @abstractmethod
    def iterate_events(self, min_block: int = None, max_block: int = None) -> Iterable[dict]:
        pass

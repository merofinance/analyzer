from abc import ABC, abstractmethod
from typing import Iterable

from .entities import State
from .event_processor import Processor
from .hook import Hooks
from .utils.base_factory import BaseFactory


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
    def iterate_events(
        self, min_block: int = None, max_block: int = None
    ) -> Iterable[dict]:
        pass

    @abstractmethod
    def get_plots(self):
        pass

    @abstractmethod
    def get_exporter(self):
        pass

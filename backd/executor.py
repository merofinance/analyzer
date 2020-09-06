from typing import List

from .hook import Hooks
from .event_processor import Processor
from .entities import State
from . import db


def process_all_events(protocol: str,
                       prehooks: List[str] = None,
                       posthooks: List[str] = None) -> State:
    hooks = Hooks(prehooks=prehooks, posthooks=posthooks)
    processor_class = Processor.get(protocol)
    processor: Processor = processor_class(hooks=hooks)
    state = processor.create_empty_state()
    events = db.iterate_events()
    processor.process_events(state, events)
    return state

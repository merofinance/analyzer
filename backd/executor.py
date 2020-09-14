from typing import List

from .hook import Hooks
from .protocol import Protocol
from .entities import State


def process_all_events(protocol_name: str,
                       prehooks: List[str] = None,
                       posthooks: List[str] = None,
                       max_block: int = None) -> State:
    hooks = Hooks(prehooks=prehooks, posthooks=posthooks)
    protocol_class = Protocol.get(protocol_name)
    protocol: Protocol = protocol_class()
    processor = protocol.create_processor(hooks=hooks)
    state = protocol.create_empty_state()
    events_count = protocol.count_events(max_block=max_block)
    events = protocol.iterate_events(max_block=max_block)
    processor.process_events(state, events, total_count=events_count)
    return state

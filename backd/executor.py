from typing import List

from .hook import Hooks
from .protocol import Protocol
from .entities import State


def process_all_events(protocol_name: str,
                       hooks: List[str] = None,
                       min_block: int = None,
                       max_block: int = None,
                       state: State = None) -> State:
    hooks = Hooks(hooks=hooks)
    protocol_class = Protocol.get(protocol_name)
    protocol: Protocol = protocol_class()
    processor = protocol.create_processor(hooks=hooks)
    if state is None:
        state = protocol.create_empty_state()
    events_count = protocol.count_events(
        min_block=min_block, max_block=max_block)
    events = protocol.iterate_events(min_block=min_block, max_block=max_block)
    processor.process_events(state, events, total_count=events_count)
    return state

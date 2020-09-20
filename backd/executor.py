from typing import List

from tqdm import tqdm

from .hook import Hooks
from .protocol import Protocol
from .entities import State


def process_all_events(
    protocol_name: str,
    hooks: List[str] = None,
    min_block: int = None,
    max_block: int = None,
    state: State = None,
    pbar: tqdm = None,
) -> State:
    hooks = Hooks(hooks=hooks)
    protocol_class = Protocol.get(protocol_name)
    protocol: Protocol = protocol_class()
    processor = protocol.create_processor(hooks=hooks)
    if state is None:
        state = protocol.create_empty_state()
    if pbar is None:
        events_count = protocol.count_events(min_block=min_block, max_block=max_block)
        pbar = tqdm(total=events_count, unit="event")
    events = protocol.iterate_events(min_block=min_block, max_block=max_block)
    processor.process_events(state, events, pbar=pbar)
    return state

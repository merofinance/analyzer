import pytest

from backd.protocols.compound.protocol import CompoundProtocol
from backd.protocols.compound.processor import CompoundProcessor
from backd.protocols.compound.entities import CompoundState


@pytest.fixture
def protocol():
    return CompoundProtocol()


def test_create_processor(protocol: CompoundProtocol):
    assert isinstance(protocol.create_processor(), CompoundProcessor)


def test_create_empty_state(protocol: CompoundProtocol):
    assert isinstance(protocol.create_empty_state(), CompoundState)


def test_count_events(protocol: CompoundProtocol, compound_dummy_events):
    assert protocol.count_events() == len(compound_dummy_events)

    max_block = 123
    expected = count_events(compound_dummy_events, max_block)
    assert protocol.count_events(max_block=max_block) == expected


def test_iterate_events(protocol: CompoundProtocol, compound_dummy_events):
    events = list(protocol.iterate_events())
    assert len(events) == len(compound_dummy_events)
    assert all(get_timestamp(events[i]) <= get_timestamp(
        events[i + 1]) for i in range(len(events) - 1))

    max_block = 123
    expected = count_events(compound_dummy_events, max_block)
    events = list(protocol.iterate_events(max_block=max_block))
    assert len(events) == expected

    assert all(get_timestamp(events[i]) <= get_timestamp(
        events[i + 1]) for i in range(len(events) - 1))


def count_events(compound_dummy_events, max_block):
    return sum(1 for event in compound_dummy_events if event["blockNumber"] <= max_block)


def get_timestamp(event):
    return (event["blockNumber"], event["transactionIndex"], event["logIndex"])

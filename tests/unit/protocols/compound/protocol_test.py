import pytest

from backd.protocols.compound.entities import CompoundState
from backd.protocols.compound.processor import CompoundProcessor
from backd.protocols.compound.protocol import CompoundProtocol


@pytest.fixture
def protocol():
    return CompoundProtocol()


def test_create_processor(protocol: CompoundProtocol):
    assert isinstance(protocol.create_processor(), CompoundProcessor)


def test_create_empty_state(protocol: CompoundProtocol):
    assert isinstance(protocol.create_empty_state(), CompoundState)


def test_count_events(protocol: CompoundProtocol, compound_dummy_events):
    assert protocol.count_events(max_block=125) == len(compound_dummy_events)

    max_block = 123
    expected = count_events(compound_dummy_events, 0, max_block)
    assert protocol.count_events(max_block=max_block) == expected

    min_block = 123
    expected = count_events(
        compound_dummy_events, min_block=min_block, max_block=max_block
    )
    assert protocol.count_events(min_block=max_block, max_block=max_block) == expected


def test_iterate_events(protocol: CompoundProtocol, compound_dummy_events):
    events = list(protocol.iterate_events(max_block=10 ** 18))
    # all "regular" events and the SaiPriceSet
    assert len(events) == len(compound_dummy_events) + 1
    assert all(
        get_timestamp(events[i]) <= get_timestamp(events[i + 1])
        for i in range(len(events) - 1)
    )

    max_block = 123
    expected = count_events(compound_dummy_events, 0, max_block)
    events = list(protocol.iterate_events(max_block=max_block))
    assert len(events) == expected

    assert all(
        get_timestamp(events[i]) <= get_timestamp(events[i + 1])
        for i in range(len(events) - 1)
    )


def count_events(compound_dummy_events, min_block, max_block):
    return sum(
        1
        for event in compound_dummy_events
        if min_block <= event["blockNumber"] <= max_block
    )


def get_timestamp(event):
    return (event["blockNumber"], event["transactionIndex"], event["logIndex"])

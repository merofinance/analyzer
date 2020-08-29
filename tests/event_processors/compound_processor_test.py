# pylint: disable=redefined-outer-name

import pytest
import dataclasses

from miru.event_processors import CompoundProcessor
from miru.entities import State


@pytest.fixture
def processor():
    return CompoundProcessor()


@pytest.fixture
def initial_state():
    return State.empty("compound", "0x1234")


def test_mint(processor: CompoundProcessor, initial_state: State, compound_dummy_events):
    mint_event = compound_dummy_events[0]
    new_state = processor.process_event(initial_state, mint_event)
    market = new_state.markets.find_by_address("0x1A3B")
    assert market.total_supplied == 100
    assert market.token_balance == 110
    assert market.total_borrowed == 0


def test_borrow(processor: CompoundProcessor, initial_state: State, compound_dummy_events):
    borrow_event = compound_dummy_events[1]
    new_state = processor.process_event(initial_state, borrow_event)
    market = new_state.markets.find_by_address("0xA123")
    assert market.total_supplied == 0
    assert market.token_balance == 0
    assert market.total_borrowed == 80


def test_repay_borrow(processor: CompoundProcessor, initial_state: State, compound_dummy_events):
    repay_borrow_event = compound_dummy_events[2]
    with pytest.raises(AssertionError):
        processor.process_event(initial_state, repay_borrow_event)

    borrow_event = compound_dummy_events[1]
    new_state = processor.process_events(initial_state, [borrow_event, repay_borrow_event])

    market = new_state.markets.find_by_address("0xA123")
    assert market.total_supplied == 0
    assert market.token_balance == 0
    assert market.total_borrowed == 60


def test_redeem_borrow(processor: CompoundProcessor, initial_state: State, compound_dummy_events):
    redeem_event = compound_dummy_events[3]
    with pytest.raises(AssertionError):
        processor.process_event(initial_state, redeem_event)

    mint_event = compound_dummy_events[0]
    new_state = processor.process_events(initial_state, [mint_event, redeem_event])

    market = new_state.markets.find_by_address("0x1A3B")
    assert market.total_supplied == 60
    assert market.token_balance == 65
    assert market.total_borrowed == 0


def test_liquidate_borrow_borrower(processor: CompoundProcessor, initial_state: State, compound_dummy_events):
    liquidate_event = compound_dummy_events[4]
    with pytest.raises(AssertionError):
        processor.process_event(initial_state, liquidate_event)

    new_state = processor.process_events(initial_state, compound_dummy_events)
    collateral_market = new_state.markets.find_by_address("0x1A3B")
    borrow_market = new_state.markets.find_by_address("0xA123")

    assert collateral_market.token_balance == 10
    assert collateral_market.total_supplied == 60
    assert collateral_market.total_borrowed == 0
    assert borrow_market.total_borrowed == 0
    assert borrow_market.token_balance == 0
    assert borrow_market.total_supplied == 0


def test_liquidate_borrow_liquidator(processor: CompoundProcessor, initial_state: State, compound_dummy_events):
    state = dataclasses.replace(initial_state, user_address="0xAB31")
    liquidate_event = compound_dummy_events[4]

    new_state = processor.process_event(state, liquidate_event)
    collateral_market = new_state.markets.find_by_address("0x1A3B")

    assert collateral_market.token_balance == 55
    assert collateral_market.total_supplied == 0
    assert collateral_market.total_borrowed == 0

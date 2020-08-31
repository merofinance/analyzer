# pylint: disable=redefined-outer-name

import pytest

from backd.event_processors import CompoundProcessor
from backd.entities import State


MAIN_USER = "0x1234a"

@pytest.fixture
def processor():
    return CompoundProcessor()


@pytest.fixture
def state(markets):
    return State("compound", markets=markets)


def test_mint(processor: CompoundProcessor, state: State, compound_dummy_events):
    mint_event = compound_dummy_events[0]
    processor.process_event(state, mint_event)
    market = state.markets.find_by_address("0x1A3B")
    assert market.balances.total_supplied == 100
    assert market.balances.token_balance == 110
    assert market.balances.total_borrowed == 0

    user_balances = market.users[MAIN_USER]
    assert user_balances.total_supplied == 100
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 0


def test_borrow(processor: CompoundProcessor, state: State, compound_dummy_events):
    borrow_event = compound_dummy_events[2]
    processor.process_event(state, borrow_event)
    market = state.markets.find_by_address("0xA123")
    assert market.balances.total_supplied == 0
    assert market.balances.token_balance == 0
    assert market.balances.total_borrowed == 80

    user_balances = market.users[MAIN_USER]
    assert user_balances.total_supplied == 0
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 80


def test_repay_borrow(processor: CompoundProcessor, state: State, compound_dummy_events):
    repay_borrow_event = compound_dummy_events[3]
    with pytest.raises(AssertionError):
        processor.process_event(state, repay_borrow_event)

    borrow_event = compound_dummy_events[2]
    processor.process_events(state, [borrow_event, repay_borrow_event])

    market = state.markets.find_by_address("0xA123")
    assert market.balances.total_supplied == 0
    assert market.balances.token_balance == 0
    assert market.balances.total_borrowed == 60

    user_balances = market.users[MAIN_USER]
    assert user_balances.total_supplied == 0
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 60


def test_redeem(processor: CompoundProcessor, state: State, compound_dummy_events):
    redeem_event = compound_dummy_events[4]
    with pytest.raises(AssertionError):
        processor.process_event(state, redeem_event)

    mint_event = compound_dummy_events[0]
    processor.process_events(state, [mint_event, redeem_event])

    market = state.markets.find_by_address("0x1A3B")
    assert market.balances.total_supplied == 60
    assert market.balances.token_balance == 65
    assert market.balances.total_borrowed == 0

    user_balances = market.users[MAIN_USER]
    assert user_balances.total_supplied == 60
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 0


def test_transfer(processor: CompoundProcessor, state: State, compound_dummy_events):
    transfer_event = compound_dummy_events[1]
    processor.process_event(state, transfer_event)
    market = state.markets.find_by_address("0x1A3B")
    user_balances = market.users[MAIN_USER]
    assert user_balances.total_supplied == 0
    assert user_balances.token_balance == 110
    assert user_balances.total_borrowed == 0

    market_balances = market.users["0x1A3b"]
    assert market_balances.total_supplied == 0
    assert market_balances.token_balance == 0
    assert market_balances.total_borrowed == 0


def test_liquidate_borrow(processor: CompoundProcessor, state: State, compound_dummy_events):
    liquidate_event = compound_dummy_events[4]
    with pytest.raises(AssertionError):
        processor.process_event(state, liquidate_event)

    # process everything but the last transfer
    processor.process_events(state, compound_dummy_events[:-1])
    collateral_market = state.markets.find_by_address("0x1A3B")
    borrow_market = state.markets.find_by_address("0xA123")

    assert collateral_market.balances.token_balance == 65
    assert collateral_market.balances.total_supplied == 60
    assert collateral_market.balances.total_borrowed == 0
    assert borrow_market.balances.total_supplied == 0
    assert borrow_market.balances.token_balance == 0
    assert borrow_market.balances.total_borrowed == 0

    collateral_user_balances = collateral_market.users[MAIN_USER]
    borrow_user_balances = borrow_market.users[MAIN_USER]
    assert collateral_user_balances.token_balance == 65
    assert collateral_user_balances.total_supplied == 60
    assert borrow_user_balances.total_borrowed == 0


def test_process_all(processor: CompoundProcessor, state: State, compound_dummy_events):
    liquidate_event = compound_dummy_events[4]
    with pytest.raises(AssertionError):
        processor.process_event(state, liquidate_event)

    # process everything but the last transfer
    processor.process_events(state, compound_dummy_events)
    collateral_market = state.markets.find_by_address("0x1A3B")

    collateral_user_balances = collateral_market.users[MAIN_USER]
    assert collateral_user_balances.token_balance == 10
    assert collateral_user_balances.total_supplied == 60

    liquidator_user_balance = collateral_market.users["0xab31"]
    assert liquidator_user_balance.token_balance == 55

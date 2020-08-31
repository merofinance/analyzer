# pylint: disable=redefined-outer-name

from decimal import Decimal

import pytest

from backd.event_processors import CompoundProcessor
from backd.entities import State, PointInTime


MAIN_USER = "0x1234a"
MAIN_MARKET = "0x1A3B"
BORROW_MARKET = "0xA123"


@pytest.fixture
def processor():
    return CompoundProcessor()


@pytest.fixture
def state(markets):
    return State("compound", markets=markets)


def test_new_comptroller(processor: CompoundProcessor, compound_dummy_events):
    new_comptroller_event = get_event(compound_dummy_events, "NewComptroller")
    state = State("compound")
    assert len(state.markets) == 0
    processor.process_event(state, new_comptroller_event)
    assert state.current_event_time == PointInTime(123, 9, 2)
    assert len(state.markets) == 1
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.comptroller_address == "0xc2a1"
    assert not market.listed
    assert market.reserve_factor == Decimal("0")
    assert market.collateral_factor == Decimal("0")
    assert market.close_factor == Decimal("0")


def test_new_interest_rate_model(processor: CompoundProcessor, compound_dummy_events):
    events = compound_dummy_events[:2]
    state = State("compound")
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.interest_rate_model == "0xbae0"


def test_new_reserve_factor(processor: CompoundProcessor, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "NewReserveFactor")
    state = State("compound")
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.reserve_factor == Decimal("0.1")


def test_new_close_factor(processor: CompoundProcessor, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "NewCloseFactor")
    state = State("compound")
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.close_factor == Decimal("0.5")


def test_new_collateral_factor(processor: CompoundProcessor, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "NewCollateralFactor")
    state = State("compound")
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.collateral_factor == Decimal("0.4")


def test_market_listed(processor: CompoundProcessor, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "MarketListed")
    state = State("compound")
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.listed


def test_market_entered(processor: CompoundProcessor, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "MarketEntered")
    state = State("compound")
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.users[MAIN_USER].entered


def test_market_exited(processor: CompoundProcessor, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "MarketEntered")
    state = State("compound")
    processor.process_events(state, events)
    market_exited_event = get_event(compound_dummy_events, "MarketExited")
    processor.process_event(state, market_exited_event)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert not market.users[MAIN_USER].entered


def test_mint(processor: CompoundProcessor, state: State, compound_dummy_events):
    mint_event = get_event(compound_dummy_events, "Mint")
    processor.process_event(state, mint_event)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.balances.total_supplied == 100
    assert market.balances.token_balance == 110
    assert market.balances.total_borrowed == 0

    user_balances = market.users[MAIN_USER].balances
    assert user_balances.total_supplied == 100
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 0


def test_borrow(processor: CompoundProcessor, state: State, compound_dummy_events):
    borrow_event = get_event(compound_dummy_events, "Borrow")
    processor.process_event(state, borrow_event)
    market = state.markets.find_by_address(BORROW_MARKET)
    assert market.balances.total_supplied == 0
    assert market.balances.token_balance == 0
    assert market.balances.total_borrowed == 80

    user_balances = market.users[MAIN_USER].balances
    assert user_balances.total_supplied == 0
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 80


def test_repay_borrow(processor: CompoundProcessor, state: State, compound_dummy_events):
    repay_borrow_event = get_event(compound_dummy_events, "RepayBorrow")
    with pytest.raises(AssertionError):
        processor.process_event(state, repay_borrow_event)

    borrow_event = get_event(compound_dummy_events, "Borrow")
    processor.process_events(state, [borrow_event, repay_borrow_event])

    market = state.markets.find_by_address(BORROW_MARKET)
    assert market.balances.total_supplied == 0
    assert market.balances.token_balance == 0
    assert market.balances.total_borrowed == 60

    user_balances = market.users[MAIN_USER].balances
    assert user_balances.total_supplied == 0
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 60


def test_redeem(processor: CompoundProcessor, state: State, compound_dummy_events):
    redeem_event = get_event(compound_dummy_events, "Redeem")
    with pytest.raises(AssertionError):
        processor.process_event(state, redeem_event)

    mint_event = get_event(compound_dummy_events, "Mint")
    processor.process_events(state, [mint_event, redeem_event])

    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.balances.total_supplied == 60
    assert market.balances.token_balance == 65
    assert market.balances.total_borrowed == 0

    user_balances = market.users[MAIN_USER].balances
    assert user_balances.total_supplied == 60
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 0


def test_transfer(processor: CompoundProcessor, state: State, compound_dummy_events):
    transfer_event = get_event(compound_dummy_events, "Transfer")
    processor.process_event(state, transfer_event)
    market = state.markets.find_by_address(MAIN_MARKET)
    user_balances = market.users[MAIN_USER].balances
    assert user_balances.total_supplied == 0
    assert user_balances.token_balance == 110
    assert user_balances.total_borrowed == 0

    market_balances = market.users[MAIN_MARKET].balances
    assert market_balances.total_supplied == 0
    assert market_balances.token_balance == 0
    assert market_balances.total_borrowed == 0


def test_liquidate_borrow(processor: CompoundProcessor, state: State, compound_dummy_events):
    liquidate_event = get_event(compound_dummy_events, "LiquidateBorrow")
    with pytest.raises(AssertionError):
        processor.process_event(state, liquidate_event)

    # process everything but the last transfer
    events = get_events_until(compound_dummy_events, "LiquidateBorrow")
    processor.process_events(state, events)
    collateral_market = state.markets.find_by_address(MAIN_MARKET)
    borrow_market = state.markets.find_by_address(BORROW_MARKET)

    assert collateral_market.balances.token_balance == 65
    assert collateral_market.balances.total_supplied == 60
    assert collateral_market.balances.total_borrowed == 0
    assert borrow_market.balances.total_supplied == 0
    assert borrow_market.balances.token_balance == 0
    assert borrow_market.balances.total_borrowed == 0

    collateral_user_balances = collateral_market.users[MAIN_USER].balances
    borrow_user_balances = borrow_market.users[MAIN_USER].balances
    assert collateral_user_balances.token_balance == 65
    assert collateral_user_balances.total_supplied == 60
    assert borrow_user_balances.total_borrowed == 0


def test_reserves_added(processor: CompoundProcessor, state: State, compound_dummy_events):
    reserves_added_event = get_event(compound_dummy_events, "ReservesAdded")
    processor.process_event(state, reserves_added_event)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.reserves == 100


def test_reserves_reduced(processor: CompoundProcessor, state: State, compound_dummy_events):
    reserves_reduced_event = get_event(compound_dummy_events, "ReservesReduced")
    with pytest.raises(AssertionError):
        processor.process_event(state, reserves_reduced_event)

    reserves_added_event = get_event(compound_dummy_events, "ReservesAdded")
    processor.process_events(state, [reserves_added_event, reserves_reduced_event])
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.reserves == 20


def test_process_all(processor: CompoundProcessor, state: State, compound_dummy_events):
    processor.process_events(state, compound_dummy_events)
    collateral_market = state.markets.find_by_address(MAIN_MARKET)

    collateral_user = collateral_market.users[MAIN_USER]
    collateral_user_balances = collateral_user.balances
    assert not collateral_user.entered
    assert collateral_user_balances.token_balance == 10
    assert collateral_user_balances.total_supplied == 60

    liquidator_user_balance = collateral_market.users["0xab31"].balances
    assert liquidator_user_balance.token_balance == 55


def get_event(compound_dummy_events, name, index=0):
    return [v for v in compound_dummy_events if v["event"] == name][index]


def get_events_until(compound_dummy_events, name, index=0):
    indices = [i for i, e in enumerate(compound_dummy_events) if e["event"] == name]
    return compound_dummy_events[:indices[index] + 1]

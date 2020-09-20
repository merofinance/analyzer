# pylint: disable=redefined-outer-name

from decimal import Decimal

import pytest

from backd.protocols.compound.processor import CompoundProcessor
from backd.entities import PointInTime
from backd.protocols.compound.entities import CompoundState as State
from backd.protocols.compound.interest_rate_models import JumpRateModel
from backd.protocols.compound import constants

from tests.fixtures import (
    get_event,
    get_events_until,
    MAIN_MARKET,
    MAIN_USER,
    MAIN_ORACLE,
    BORROW_MARKET,
)


@pytest.fixture
def processor(dummy_markets_meta):
    return CompoundProcessor(markets=dummy_markets_meta)


@pytest.fixture
def state(markets, dsr):
    return State(dsr=dsr, markets=markets)


def test_new_comptroller(processor: CompoundProcessor, dsr, compound_dummy_events):
    new_comptroller_event = get_event(compound_dummy_events, "NewComptroller")
    state = State(dsr=dsr)
    assert len(state.markets) == 0
    processor.process_event(state, new_comptroller_event)
    assert state.current_event_time == PointInTime(123, 9, 1)
    assert state.close_factor == Decimal("0")
    assert len(state.markets) == 1
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.comptroller_address == "0xc2a1"
    assert not market.listed
    assert market.reserve_factor == Decimal("0")
    assert market.collateral_factor == Decimal("0")


def test_new_interest_rate_model(
    processor: CompoundProcessor, dsr, compound_dummy_events
):
    events = get_events_until(compound_dummy_events, "NewMarketInterestRateModel")
    state = State(dsr=dsr)
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.interest_rate_model == "0xbae0"
    assert len(state.interest_rate_models) == 1


def test_new_interest_params(processor: CompoundProcessor, dsr, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "NewInterestParams")
    state = State(dsr=dsr)
    processor.process_events(state, events)
    model = state.interest_rate_models.get_model("0xBAE0")
    assert isinstance(model, JumpRateModel)
    assert model.base_rate_per_block == 0
    assert model.multiplier_per_block == 23782343987
    assert model.kink == 800000000000000000
    assert model.jump_multiplier_per_block == 518455098934


def test_new_reserve_factor(processor: CompoundProcessor, dsr, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "NewReserveFactor")
    state = State(dsr=dsr)
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.reserve_factor == Decimal("0.1")


def test_new_close_factor(processor: CompoundProcessor, dsr, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "NewCloseFactor")
    state = State(dsr=dsr)
    processor.process_events(state, events)
    assert state.close_factor == Decimal("0.5")


def test_new_collateral_factor(
    processor: CompoundProcessor, dsr, compound_dummy_events
):
    events = get_events_until(compound_dummy_events, "NewCollateralFactor")
    state = State(dsr=dsr)
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.collateral_factor == Decimal("0.4")


def test_market_listed(processor: CompoundProcessor, dsr, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "MarketListed")
    state = State(dsr=dsr)
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.listed


def test_market_entered(processor: CompoundProcessor, dsr, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "MarketEntered")
    state = State(dsr=dsr)
    processor.process_events(state, events)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.users[MAIN_USER].entered


def test_market_exited(processor: CompoundProcessor, dsr, compound_dummy_events):
    events = get_events_until(compound_dummy_events, "MarketEntered")
    state = State(dsr=dsr)
    processor.process_events(state, events)
    market_exited_event = get_event(compound_dummy_events, "MarketExited")
    processor.process_event(state, market_exited_event)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert not market.users[MAIN_USER].entered


def test_mint(processor: CompoundProcessor, state: State, compound_dummy_events):
    mint_event = get_event(compound_dummy_events, "Mint")
    transfer_event = get_event(compound_dummy_events, "Transfer", index=1)
    processor.process_events(state, [mint_event, transfer_event])
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.balances.total_underlying == 100
    assert market.balances.token_balance == 110
    assert market.balances.total_borrowed == 0

    user_balances = market.users[MAIN_USER].balances
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 0


def test_borrow(processor: CompoundProcessor, state: State, compound_dummy_events):
    borrow_event = get_event(compound_dummy_events, "Borrow")
    mint_event = get_event(compound_dummy_events, "Mint", 1)
    mint_transfer_event = get_event(compound_dummy_events, "Transfer", 2)
    borrow_transfer_event = get_event(compound_dummy_events, "Transfer", 3)
    market = state.markets.find_by_address(BORROW_MARKET)
    processor.process_events(
        state, [mint_event, mint_transfer_event, borrow_event, borrow_transfer_event]
    )
    assert market.balances.total_underlying == 120
    assert market.balances.token_balance == 250
    assert market.balances.total_borrowed == 80

    user_balances = market.users[MAIN_USER].balances
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 80


def test_accrue_interest(
    processor: CompoundProcessor, state: State, compound_dummy_events
):
    market = state.markets.find_by_address(BORROW_MARKET)
    market.reserve_factor = Decimal("0.1")
    accrue_interest_event = get_event(compound_dummy_events, "AccrueInterest")
    processor.process_event(state, accrue_interest_event)
    market = state.markets.find_by_address(BORROW_MARKET)
    assert market.borrow_index == 1033291579335879146
    assert market.reserves == 100


def test_repay_borrow(
    processor: CompoundProcessor, state: State, compound_dummy_events
):
    repay_borrow_event = get_event(compound_dummy_events, "RepayBorrow")
    with pytest.raises(AssertionError):
        processor.process_event(state, repay_borrow_event)

    mint_event = get_event(compound_dummy_events, "Mint", 1)
    borrow_event = get_event(compound_dummy_events, "Borrow")
    mint_transfer_event = get_event(compound_dummy_events, "Transfer", 2)
    borrow_transfer_event = get_event(compound_dummy_events, "Transfer", 3)
    repay_borrow_transfer_event = get_event(compound_dummy_events, "Transfer", 4)
    processor.process_events(
        state,
        [
            mint_event,
            mint_transfer_event,
            borrow_event,
            borrow_transfer_event,
            repay_borrow_event,
            repay_borrow_transfer_event,
        ],
    )

    market = state.markets.find_by_address(BORROW_MARKET)
    assert market.balances.total_underlying == 140
    assert market.balances.token_balance == 250
    assert market.balances.total_borrowed == 60

    user_balances = market.users[MAIN_USER].balances
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 60


def test_redeem(processor: CompoundProcessor, state: State, compound_dummy_events):
    redeem_event = get_event(compound_dummy_events, "Redeem")
    with pytest.raises(AssertionError):
        processor.process_event(state, redeem_event)

    mint_event = get_event(compound_dummy_events, "Mint")
    mint_transfer_event = get_event(compound_dummy_events, "Transfer", index=1)
    redeem_transfer_event = get_event(compound_dummy_events, "Transfer", index=6)
    processor.process_events(
        state, [mint_event, mint_transfer_event, redeem_event, redeem_transfer_event]
    )

    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.balances.total_underlying == 60
    assert market.balances.token_balance == 65
    assert market.balances.total_borrowed == 0

    user_balances = market.users[MAIN_USER].balances
    assert user_balances.token_balance == 0
    assert user_balances.total_borrowed == 0


def test_transfer(processor: CompoundProcessor, state: State, compound_dummy_events):
    transfer_event = get_event(compound_dummy_events, "Transfer")
    processor.process_event(state, transfer_event)
    market = state.markets.find_by_address(MAIN_MARKET)
    user_balances = market.users[MAIN_USER].balances
    assert user_balances.token_balance == 110
    assert user_balances.total_borrowed == 0

    market_balances = market.users[MAIN_MARKET].balances
    assert market_balances.token_balance == 0
    assert market_balances.total_borrowed == 0


def test_liquidate_borrow(
    processor: CompoundProcessor, state: State, compound_dummy_events
):
    # get liquidation and next repay
    events = get_events_until(compound_dummy_events, "MarketExited")
    borrow_market = state.markets.find_by_address(BORROW_MARKET)
    collateral_market = state.markets.find_by_address(MAIN_MARKET)
    processor.process_events(state, events)

    interests = 80 * 1033291579335879146 // int(1e18) - 80

    assert collateral_market.balances.token_balance == 65
    assert collateral_market.balances.total_underlying == 60
    assert collateral_market.balances.total_borrowed == 0
    assert borrow_market.balances.total_underlying == 200  # fully repaid
    assert borrow_market.balances.token_balance == 250
    assert borrow_market.balances.total_borrowed == interests

    collateral_user_balances = collateral_market.users[MAIN_USER].balances
    borrow_user_balances = borrow_market.users[MAIN_USER].balances
    assert collateral_user_balances.token_balance == 10
    assert borrow_user_balances.total_borrowed == interests


def test_reserves_added(
    processor: CompoundProcessor, state: State, compound_dummy_events
):
    reserves_added_event = get_event(compound_dummy_events, "ReservesAdded")
    processor.process_event(state, reserves_added_event)
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.reserves == 100


def test_reserves_reduced(
    processor: CompoundProcessor, state: State, compound_dummy_events
):
    reserves_reduced_event = get_event(compound_dummy_events, "ReservesReduced")
    with pytest.raises(AssertionError):
        processor.process_event(state, reserves_reduced_event)

    reserves_added_event = get_event(compound_dummy_events, "ReservesAdded")
    processor.process_events(state, [reserves_added_event, reserves_reduced_event])
    market = state.markets.find_by_address(MAIN_MARKET)
    assert market.reserves == 20


def test_price_posted(
    processor: CompoundProcessor, state: State, compound_dummy_events
):
    price_posted_event = get_event(compound_dummy_events, "PricePosted")
    processor.process_event(state, price_posted_event)
    assert len(state.oracles) == 1
    assert state.oracles.get_oracle(MAIN_ORACLE).get_price(MAIN_MARKET) == 200


def test_price_updated(
    processor: CompoundProcessor, state: State, compound_dummy_events
):
    price_posted_event = get_event(compound_dummy_events, "PriceUpdated")
    processor.process_event(state, price_posted_event)
    assert len(state.oracles) == 1
    ceth = "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5"
    oracle = state.oracles.get_oracle("0xabab54")
    assert oracle.get_underlying_price(ceth) == 100 * int(1e12)


def test_sai_price_set(processor: CompoundProcessor, state: State):
    oracle = "0xddc46a3b076aec7ab3fc37420a8edd2959764ec4"
    event = {
        "event": "SaiPriceSet",
        "address": oracle,
        "returnValues": {
            "newPriceMantissa": "100",
        },
        "blockNumber": 120,
        "transactionIndex": -1,
        "logIndex": -2,
    }
    processor.process_event(state, event)
    csai = "0xf5dce57282a584d2746faf1593d3121fcac444dc"
    assert state.oracles.get_oracle(oracle).get_underlying_price(csai) == 100


def test_chi_updated(processor: CompoundProcessor, state: State):
    event = {
        "event": "ChiUpdated",
        "address": "0x1234",
        "returnValues": {"chi": "125"},
        "blockNumber": 100,
        "transactionIndex": -5,
        "logIndex": -5,
    }
    processor.process_event(state, event)
    cdai_market = state.markets.find_by_address(constants.CDAI_ADDRESS)
    assert cdai_market.chi == 125


def test_process_all(processor: CompoundProcessor, state: State, compound_dummy_events):
    processor.process_events(state, compound_dummy_events)
    collateral_market = state.markets.find_by_address(MAIN_MARKET)

    collateral_user = collateral_market.users[MAIN_USER]
    collateral_user_balances = collateral_user.balances
    assert not collateral_user.entered
    assert collateral_user_balances.token_balance == 10

    liquidator_user_balance = collateral_market.users["0xab31"].balances
    assert liquidator_user_balance.token_balance == 55

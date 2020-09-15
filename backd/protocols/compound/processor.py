"""This module handles compound events
"""

# pylint: disable=no-self-use

from decimal import Decimal

import stringcase

from ... import constants
from ... import normalizer
from ...event_processor import Processor
from ...entities import Market
from .entities import CompoundState as State
from ...logger import logger
from ...hook import Hooks
from .hooks import DSRHook
from ...tokens.dai.dsr import DSR


FACTORS_DIVISOR = Decimal(10) ** constants.COMPOUND_FACTORS_DECIMALS


@Processor.register("compound")
class CompoundProcessor(Processor):
    def __init__(self, hooks: Hooks = None):
        if hooks is None:
            hooks = Hooks()
        dsr_hook = DSRHook()
        hooks.prehooks.insert(0, dsr_hook)
        super().__init__(hooks=hooks)

    def _process_event(self, state, event):
        event = normalizer.normalize_event(event)
        event_name = stringcase.snakecase(event["event"])
        func = getattr(self, f"process_{event_name}", None)
        if not func:
            logger.debug("unknown event %s", event_name)
            return

        try:
            func(state, event["address"], event["returnValues"])
        except Exception as e:
            logger.error("error while processing %s", event)
            raise e

    def process_new_comptroller(self, state: State, event_address: str, event_values: dict):
        # NOTE: process_new_comptroller is always the first event emitted in a new market
        try:
            market = state.markets.find_by_address(event_address)
        except ValueError:
            market = Market(event_address)
            state.markets.add_market(market)
        market.comptroller_address = event_values["newComptroller"]

    def process_new_market_interest_rate_model(self, state: State, # pylint: disable=invalid-name
                                               event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        market.interest_rate_model = event_values["newInterestRateModel"]
        state.interest_rate_models.create_model(market.interest_rate_model)

    def process_new_reserve_factor(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        factor = int(event_values["newReserveFactorMantissa"]) / FACTORS_DIVISOR
        assert 0 <= factor <= 1, f"close factor must be between 0 and 1, not {factor}"
        market.reserve_factor = factor

    def process_new_close_factor(self, state: State, _event_address: str, event_values: dict):
        factor = int(event_values["newCloseFactorMantissa"]) / FACTORS_DIVISOR
        assert 0 <= factor <= 1, f"close factor must be between 0 and 1, not {factor}"
        state.close_factor = factor

    def process_new_collateral_factor(self, state: State, _event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_values["cToken"])
        market.collateral_factor = int(event_values["newCollateralFactorMantissa"]) / FACTORS_DIVISOR

    def process_market_listed(self, state: State, _event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_values["cToken"])
        market.listed = True

    def process_market_entered(self, state: State, _event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_values["cToken"])
        market.users[event_values["account"]].entered = True

    def process_market_exited(self, state: State, _event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_values["cToken"])
        market.users[event_values["account"]].entered = False

    def process_mint(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        mint_amount = int(event_values["mintAmount"])
        market.balances.total_underlying += mint_amount

        market.balances.token_balance += int(event_values["mintTokens"])

    def process_redeem(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        redeem_amount = int(event_values["redeemAmount"])
        redeem_tokens = int(event_values["redeemTokens"])

        # NOTE: the following assert could fail for ERC20 based cTokens because
        # someone could transfer the underlying token directly to the cTokens address
        # assert market.balances.total_underlying >= redeem_amount, \
        #         f"supply can never be negative, {market.balances.total_underlying} < {redeem_amount}"
        assert market.balances.token_balance >= redeem_tokens, \
                f"token balance can never be negative, {market.balances.token_balance} < {redeem_tokens}"

        market.balances.total_underlying -= redeem_amount
        market.balances.token_balance -= redeem_tokens

    def process_transfer(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        amount = int(event_values["amount"])

        from_ = event_values["from"]
        from_balances = market.users[from_].balances
        if from_ != event_address:
            assert from_balances.token_balance >= amount, \
                f"token balance can never be negative, {from_balances.token_balance} < {amount}"
            from_balances.token_balance -= amount

        to = event_values["to"]
        if to != event_address:
            market.users[to].balances.token_balance += amount

    def process_borrow(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        amount = int(event_values["borrowAmount"])
        market.balances.total_borrowed = int(event_values["totalBorrows"])

        # NOTE: the following assert could fail for ERC20 based cTokens because
        # someone could transfer the underlying token directly to the cTokens address
        # assert market.balances.total_underlying >= amount, \
        #         f"total supplied can never be negative, {market.balances.total_underlying} < {amount}"
        market.balances.total_underlying -= amount

        borrower = event_values["borrower"]
        self.update_user_borrow(market, borrower)
        market.users[borrower].balances.total_borrowed += int(event_values["borrowAmount"])

    def process_repay_borrow(self, state: State, event_address: str, event_values: dict):
        borrower = event_values["borrower"]
        amount = int(event_values["repayAmount"])
        market = state.markets.find_by_address(event_address)
        self.update_user_borrow(market, borrower)
        user_balances = market.users[borrower].balances
        assert market.balances.total_borrowed >= amount, \
                f"borrow can never be negative, {market.balances.total_borrowed} < {amount}"
        assert user_balances.total_borrowed >= amount, \
                f"borrow can never be negative, {user_balances.total_borrowed} < {amount}"

        market.balances.total_borrowed = int(event_values["totalBorrows"])
        market.balances.total_underlying += amount
        user_balances.total_borrowed -= amount

    def process_liquidate_borrow(self, state: State, event_address: str, event_values: dict):
        # NOTE: repay and transfer will be emitted with each liquidation
        pass

    def process_reserves_added(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        market.reserves += int(event_values["addAmount"])

    def process_reserves_reduced(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        assert market.reserves >= int(event_values["reduceAmount"]), \
            f"reserves can never be negative, {market.reserves} < {event_values['reduceAmount']}"
        market.reserves -= int(event_values["reduceAmount"])

    def process_new_price_oracle(self, state: State, _event_address: str, event_values: dict):
        address = event_values["newPriceOracle"]
        state.oracles.create_oracle(address)
        state.oracles.current_address = address

    def process_price_posted(self, state: State, event_address: str, event_values: dict):
        oracle = state.oracles.get_oracle(event_address)
        value = int(event_values["newPriceMantissa"])
        oracle.update_price(event_values["asset"], value)

    def process_price_updated(self, state: State, event_address: str, event_values: dict):
        oracle = state.oracles.get_oracle(event_address)
        value = int(event_values["price"])
        oracle.update_price(event_values["symbol"], value)

    def process_sai_price_set(self, state: State, event_address: str, event_values: dict):
        oracle = state.oracles.get_oracle(event_address)
        value = int(event_values["newPriceMantissa"])
        oracle.sai_price = value

    def process_inverted_price_posted(self, state: State, _event_address: str, event_values: dict):
        # virtual event generated when Oracle DSValue is updated
        oracle = state.oracles.get_oracle(
            "0x02557a5e05defeffd4cae6d83ea3d173b272c904")  # oracle version 1
        value = int(event_values["newPriceMantissa"])
        for ctoken in event_values["tokens"]:
            oracle.update_price(ctoken, value, inverted=True)

    def process_new_interest_params(self, state: State, event_address: str, event_values: dict):
        try:
            model = state.interest_rate_models.get_model(event_address)
        except KeyError:
            model = state.interest_rate_models.create_model(event_address)
        model.update_params(event_values)

    def process_accrue_interest(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        market.balances.total_borrowed = int(event_values["totalBorrows"])
        market.borrow_index = int(event_values["borrowIndex"])
        market.reserves += int(int(event_values["interestAccumulated"]) * market.reserve_factor)

    def update_user_borrow(self, market: Market, user_address: str):
        user = market.users[user_address]
        new_total_borrowed = user.borrowed_at(market.borrow_index)
        user.balances.total_borrowed = new_total_borrowed
        user.borrow_index = market.borrow_index

    @classmethod
    def create_empty_state(cls) -> State:
        return State(dsr=DSR.create())

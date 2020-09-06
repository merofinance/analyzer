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


FACTORS_DIVISOR = Decimal(10) ** constants.COMPOUND_FACTORS_DECIMALS


@Processor.register("compound")
class CompoundProcessor(Processor):
    def __init__(self):
        dsr_hook = DSRHook()
        hooks = Hooks(prehooks=[dsr_hook.run])
        super().__init__(hooks=hooks)

    def _process_event(self, state, event):
        event = normalizer.normalize_event(event)
        event_name = stringcase.snakecase(event["event"])
        func = getattr(self, f"process_{event_name}", None)
        if not func:
            logger.debug("unknown event %s", event_name)
            return

        func(state, event["address"], event["returnValues"])

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
        assert 0 <= factor <= 1, "close factor must be between 0 and 1"
        market.reserve_factor = factor

    def process_new_close_factor(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        factor = int(event_values["newCloseFactorMantissa"]) / FACTORS_DIVISOR
        assert 0 <= factor <= 1, "close factor must be between 0 and 1"
        market.close_factor = factor

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
        market.balances.total_supplied += mint_amount
        market.users[event_values["minter"]].balances.total_supplied += mint_amount

        market.balances.token_balance += int(event_values["mintTokens"])

    def process_redeem(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        redeem_amount = int(event_values["redeemAmount"])
        redeem_tokens = int(event_values["redeemTokens"])
        user_balances = market.users[event_values["redeemer"]].balances

        assert market.balances.total_supplied >= redeem_amount, "supply can never be negative"
        assert market.balances.token_balance >= redeem_tokens, "token balance can never be negative"
        assert user_balances.total_supplied >= redeem_amount, "supply can never be negative"

        market.balances.total_supplied -= redeem_amount
        market.balances.token_balance -= redeem_tokens
        user_balances.total_supplied -= redeem_amount

    def process_transfer(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        amount = int(event_values["amount"])

        from_ = event_values["from"]
        from_balances = market.users[from_].balances
        if from_ != event_address:
            assert from_balances.token_balance >= amount, "token balance can never be negative"
            from_balances.token_balance -= amount

        to = event_values["to"]
        if to != event_address:
            market.users[to].balances.token_balance += amount

    def process_borrow(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        market.balances.total_borrowed += int(event_values["borrowAmount"])
        borrower = event_values["borrower"]
        market.users[borrower].balances.total_borrowed += int(event_values["borrowAmount"])

    def process_repay_borrow(self, state: State, event_address: str, event_values: dict):
        self._execute_repay(state, event_address, event_values["borrower"],
                            int(event_values["repayAmount"]))

    def process_liquidate_borrow(self, state: State, event_address: str, event_values: dict):
        self._execute_repay(state, event_address, event_values["borrower"],
                            int(event_values["repayAmount"]))

    def process_reserves_added(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        market.reserves += int(event_values["addAmount"])

    def process_reserves_reduced(self, state: State, event_address: str, event_values: dict):
        market = state.markets.find_by_address(event_address)
        assert market.reserves >= int(event_values["reduceAmount"]), "reserves can never be negative"
        market.reserves -= int(event_values["reduceAmount"])

    def _execute_repay(self, state: State, event_address: str, borrower: str, amount: int):
        market = state.markets.find_by_address(event_address)
        user_balances = market.users[borrower].balances
        assert market.balances.total_borrowed >= amount, "borrow can never be negative"
        assert user_balances.total_borrowed >= amount, "borrow can never be negative"

        market.balances.total_borrowed -= amount
        user_balances.total_borrowed -= amount

    def process_price_posted(self, state: State, event_address: str, event_values: dict):
        oracle = state.oracles.get_oracle(event_address)
        value = int(event_values["newPriceMantissa"])
        oracle.update_price(event_values["asset"], value)

    def process_new_interest_params(self, state: State, event_address: str, event_values: dict):
        model = state.interest_rate_models.get_model(event_address)
        model.update_params(event_values)

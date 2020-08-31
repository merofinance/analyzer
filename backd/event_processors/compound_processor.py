# pylint: disable=no-self-use

from decimal import Decimal

import stringcase

from ..event_processor import Processor
from ..entities import State, Market
from ..logger import logger
from .. import normalizer



@Processor.register("compound")
class CompoundProcessor(Processor):
    def process_event(self, state, event):
        super().process_event(state, event)
        event = normalizer.normalize_event(event)
        event_name = stringcase.snakecase(event["event"])
        func = getattr(self, f"process_{event_name}", None)
        if not func:
            logger.debug("unknown event %s", event_name)
            return

        func(state, event["address"], event["returnValues"])

    def process_new_comptroller(self, state: State, market_address: str, event_values: dict):
        # NOTE: process_new_comptroller is always the first event emitted in a new market
        try:
            market = state.markets.find_by_address(market_address)
        except ValueError:
            market = Market(market_address)
            state.markets.add_market(market)
        market.comptroller_address = event_values["newComptroller"]

    def process_new_market_interest_rate_model(self, state: State, # pylint: disable=invalid-name
                                               market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        market.interest_rate_model = event_values["newInterestRateModel"]

    def process_new_reserve_factor(self, state: State, market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        market.reserve_factor = int(event_values["newReserveFactorMantissa"]) / Decimal(1e18)

    def process_new_collateral_factor(self, state: State, _market_address: str, event_values: dict):
        market = state.markets.find_by_address(event_values["cToken"])
        market.collateral_factor = int(event_values["newCollateralFactorMantissa"]) / Decimal(1e18)

    def process_mint(self, state: State, market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        mint_amount = int(event_values["mintAmount"])
        market.balances.total_supplied += mint_amount
        market.users[event_values["minter"]].total_supplied += mint_amount

        market.balances.token_balance += int(event_values["mintTokens"])

    def process_redeem(self, state: State, market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        redeem_amount = int(event_values["redeemAmount"])
        redeem_tokens = int(event_values["redeemTokens"])
        user_balances = market.users[event_values["redeemer"]]

        assert market.balances.total_supplied >= redeem_amount, "supply can never be negative"
        assert market.balances.token_balance >= redeem_tokens, "token balance can never be negative"
        assert user_balances.total_supplied >= redeem_amount, "supply can never be negative"

        market.balances.total_supplied -= redeem_amount
        market.balances.token_balance -= redeem_tokens
        user_balances.total_supplied -= redeem_amount

    def process_transfer(self, state: State, market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        amount = int(event_values["amount"])

        from_ = event_values["from"]
        if from_ != market_address:
            assert market.users[from_].token_balance >= amount, "token balance can never be negative"
            market.users[from_].token_balance -= amount

        to = event_values["to"]
        if to != market_address:
            market.users[to].token_balance += amount

    def process_borrow(self, state: State, market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        market.balances.total_borrowed += int(event_values["borrowAmount"])
        borrower = event_values["borrower"]
        market.users[borrower].total_borrowed += int(event_values["borrowAmount"])

    def process_repay_borrow(self, state: State, market_address: str, event_values: dict):
        self._execute_repay(state, market_address, event_values["borrower"],
                            int(event_values["repayAmount"]))

    def process_liquidate_borrow(self, state: State, market_address: str, event_values: dict):
        self._execute_repay(state, market_address, event_values["borrower"],
                            int(event_values["repayAmount"]))

    def _execute_repay(self, state: State, market_address: str, borrower: str, amount: int):
        market = state.markets.find_by_address(market_address)
        user_balances = market.users[borrower]
        assert market.balances.total_borrowed >= amount, "borrow can never be negative"
        assert user_balances.total_borrowed >= amount, "borrow can never be negative"

        market.balances.total_borrowed -= amount
        user_balances.total_borrowed -= amount

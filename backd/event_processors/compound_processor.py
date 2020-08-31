import stringcase

from ..event_processor import Processor
from ..entities import State
from ..logger import logger



@Processor.register("compound")
class CompoundProcessor(Processor):
    def process_event(self, state, event):
        event_name = stringcase.snakecase(event["event"])
        func = getattr(self, f"process_{event_name}", None)
        if not func:
            logger.debug("unknown event %s", event_name)
            return

        func(state, event["address"].lower(), event["returnValues"])

    def process_mint(self, state: State, market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        market.balances.total_supplied += int(event_values["mintAmount"])
        minter = event_values["minter"].lower()
        market.users[minter].total_supplied += int(event_values["mintAmount"])

        market.balances.token_balance += int(event_values["mintTokens"])

    def process_redeem(self, state: State, market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        redeem_amount = int(event_values["redeemAmount"])
        redeem_tokens = int(event_values["redeemTokens"])
        redeemer = event_values["redeemer"].lower()
        user_balances = market.users[redeemer]

        assert market.balances.total_supplied >= redeem_amount, "supply can never be negative"
        assert market.balances.token_balance >= redeem_tokens, "token balance can never be negative"
        assert user_balances.total_supplied >= redeem_amount, "supply can never be negative"

        market.balances.total_supplied -= redeem_amount
        market.balances.token_balance -= redeem_tokens
        user_balances.total_supplied -= redeem_amount

    def process_transfer(self, state: State, market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        amount = int(event_values["amount"])

        from_ = event_values["from"].lower()
        if from_ != market_address:
            assert market.users[from_].token_balance >= amount, "token balance can never be negative"
            market.users[from_].token_balance -= amount

        to = event_values["to"].lower()
        if to != market_address:
            market.users[to].token_balance += amount

    def process_borrow(self, state: State, market_address: str, event_values: dict):
        market = state.markets.find_by_address(market_address)
        market.balances.total_borrowed += int(event_values["borrowAmount"])
        borrower = event_values["borrower"].lower()
        market.users[borrower].total_borrowed += int(event_values["borrowAmount"])

    def process_repay_borrow(self, state: State, market_address: str, event_values: dict):
        borrower = event_values["borrower"].lower()
        self._execute_repay(state, market_address, borrower,
                            int(event_values["repayAmount"]))

    def process_liquidate_borrow(self, state: State, market_address: str, event_values: dict):
        borrower = event_values["borrower"].lower()
        self._execute_repay(state, market_address, borrower,
                            int(event_values["repayAmount"]))

    def _execute_repay(self, state: State, market_address: str, borrower: str, amount: int):
        market = state.markets.find_by_address(market_address)
        user_balances = market.users[borrower]
        assert market.balances.total_borrowed >= amount, "borrow can never be negative"
        assert user_balances.total_borrowed >= amount, "borrow can never be negative"

        market.balances.total_borrowed -= amount
        user_balances.total_borrowed -= amount

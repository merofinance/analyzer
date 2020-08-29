import stringcase

from ..event_processor import Processor
from ..entities import UserMarkets, UserMarket, State



@Processor.register("compound")
class CompoundProcessor(Processor):
    def update_markets(self, state: State, event: dict) -> UserMarkets:
        event_name = stringcase.snakecase(event["event"])
        func = getattr(self, f"process_{event_name}", None)
        if not func:
            raise ValueError(f"unknown event {event_name}")
        return func(state, event["address"], event["returnValues"])

    def process_mint(self, state: State, market_address: str, event_values: dict) -> UserMarkets:
        def _process(market: UserMarket):
            market.total_supplied += int(event_values["mintAmount"])
            market.token_balance += int(event_values["mintTokens"])
            return market
        return self._update_market(state.markets, market_address, _process)

    def process_redeem(self, state: State, market_address: str, event_values: dict) -> UserMarkets:
        def _process(market: UserMarket):
            market.total_supplied -= int(event_values["redeemAmount"])
            assert market.total_supplied >= 0, "supply can never be negative"
            market.token_balance -= int(event_values["redeemTokens"])
            return market
        return self._update_market(state.markets, market_address, _process)

    def process_borrow(self, state: State, market_address: str, event_values: dict) -> UserMarkets:
        def _process(market: UserMarket):
            market.total_borrowed += int(event_values["borrowAmount"])
            return market
        return self._update_market(state.markets, market_address, _process)

    def process_repay_borrow(self, state: State, market_address: str, event_values: dict) -> UserMarkets:
        def _process(market: UserMarket):
            market.total_borrowed -= int(event_values["repayAmount"])
            assert market.total_borrowed >= 0, "borrow can never be negative"
            return market
        return self._update_market(state.markets, market_address, _process)

    def process_liquidate_borrow(self, state: State, market_address: str, event_values: dict) -> UserMarkets:
        if state.user_address == event_values["borrower"]:
            return self._process_liquidate_borrower(state, market_address, event_values)
        elif state.user_address == event_values["liquidator"]:
            return self._process_liquidate_liquidator(state, event_values)
        raise ValueError("unknown address")

    def _process_liquidate_borrower(self, state: State, market_address: str, event_values: dict) -> UserMarkets:
        def _process_current_market(market: UserMarket):
            market.total_borrowed -= int(event_values["repayAmount"])
            assert market.total_borrowed >= 0, "borrow can never be negative"
            return market

        def _process_collateral_market(market: UserMarket):
            market.token_balance -= int(event_values["seizeTokens"])
            assert market.token_balance >= 0, "token balance can never be negative"
            return market
        collateral_market = event_values["cTokenCollateral"]

        updated_markets = self._update_market(state.markets, market_address, _process_current_market)
        return self._update_market(updated_markets, collateral_market, _process_collateral_market)

    def _process_liquidate_liquidator(self, state: State, event_values: dict) -> UserMarkets:
        def _process(market: UserMarket):
            market.token_balance += int(event_values["seizeTokens"])
            return market
        collateral_market = event_values["cTokenCollateral"]
        return self._update_market(state.markets, collateral_market, _process)

    def _update_market(self, markets: UserMarkets, address: str, callback) -> UserMarkets:
        market = markets.find_by_address(address)
        new_market = callback(market)
        return markets.replace_or_add_market(new_market)

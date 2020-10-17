"""This module handles compound events
"""

# pylint: disable=no-self-use

from decimal import Decimal

import stringcase

from ...entities import Market
from ...event_processor import Processor
from ...hook import Hooks
from ...utils.logger import logger
from . import constants
from .entities import CDaiMarket
from .entities import CompoundState as State

FACTORS_DIVISOR = Decimal(10) ** constants.FACTORS_DECIMALS


def get_any_key(obj, keys):
    for key in keys:
        if key in obj:
            return obj[key]
    raise ValueError("none of {0} in {1}".format(", ".join(keys), obj))


class CompoundProcessor(Processor):
    def __init__(self, hooks: Hooks = None, markets: dict = None):
        if hooks is None:
            hooks = Hooks()
        if markets is None:
            markets = constants.MARKETS
        self.markets_metadata = {
            market["underlying_address"]: market for market in markets
        }
        super().__init__(hooks=hooks)

    def _process_event(self, state, event):
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

    def process_new_comptroller(self, state: State, event_address: str, args: dict):
        # NOTE: process_new_comptroller is always the first event emitted in a new market
        market = self._find_or_add_market(state, event_address)
        market.comptroller_address = args["newComptroller"]

    def process_new_market_interest_rate_model(  # pylint: disable=invalid-name
        self,
        state: State,
        event_address: str,
        args: dict,
    ):
        market = state.markets.find_by_address(event_address)
        market.interest_rate_model = args["newInterestRateModel"]
        state.interest_rate_models.create_model(market.interest_rate_model)

    def process_new_reserve_factor(self, state: State, event_address: str, args: dict):
        market = state.markets.find_by_address(event_address)
        factor = int(args["newReserveFactorMantissa"]) / FACTORS_DIVISOR
        assert 0 <= factor <= 1, f"close factor must be between 0 and 1, not {factor}"
        market.reserve_factor = factor

    def process_new_implementation(self, state: State, event_address: str, args: dict):
        # need to handle DSR
        if event_address != constants.CDAI_ADDRESS:
            return
        market: CDaiMarket = state.markets.find_by_address(event_address)
        new_implementation = args["newImplementation"]
        if new_implementation != constants.CDAI_DSR_IMPLEMENTATION:
            return
        market.dsr_active = True

    def process_new_close_factor(self, state: State, _event_address: str, args: dict):
        factor = int(args["newCloseFactorMantissa"]) / FACTORS_DIVISOR
        assert 0 <= factor <= 1, f"close factor must be between 0 and 1, not {factor}"
        state.close_factor = factor

    def process_new_collateral_factor(
        self, state: State, _event_address: str, args: dict
    ):
        market = state.markets.find_by_address(args["cToken"])
        market.collateral_factor = (
            int(args["newCollateralFactorMantissa"]) / FACTORS_DIVISOR
        )

    def process_market_listed(self, state: State, _event_address: str, args: dict):
        market = state.markets.find_by_address(args["cToken"])
        market.listed = True

    def process_market_entered(self, state: State, _event_address: str, args: dict):
        market = state.markets.find_by_address(args["cToken"])
        market.users[args["account"]].entered = True

    def process_market_exited(self, state: State, _event_address: str, args: dict):
        market = state.markets.find_by_address(args["cToken"])
        market.users[args["account"]].entered = False

    def process_mint(self, state: State, event_address: str, args: dict):
        market = state.markets.find_by_address(event_address)
        mint_amount = int(args["mintAmount"])

        # NOTE: ERC20 tokens are handled through the transfer event
        if event_address == constants.CETH_ADDRESS:
            market.balances.total_underlying += mint_amount

        market.balances.token_balance += int(args["mintTokens"])

    def process_redeem(self, state: State, event_address: str, args: dict):
        market = state.markets.find_by_address(event_address)
        redeem_amount = int(args["redeemAmount"])
        redeem_tokens = int(args["redeemTokens"])

        assert (
            market.balances.token_balance >= redeem_tokens
        ), f"token balance can never be negative, {market.balances.token_balance} < {redeem_tokens}"

        # NOTE: ERC20 tokens are handled through the transfer event
        if event_address == constants.CETH_ADDRESS:
            assert (
                market.balances.total_underlying >= redeem_amount
            ), f"supply can never be negative, {market.balances.total_underlying} < {redeem_amount}"
            market.balances.total_underlying -= redeem_amount

        # NOTE: CDAI uses DSR so Transfer comes from NULL address
        if self._should_handle_dsr(market):
            market.transfer_out(redeem_amount)

        market.balances.token_balance -= redeem_tokens

    def process_transfer(self, state: State, event_address: str, args: dict):
        try:
            market = state.markets.find_by_address(event_address)
        except ValueError:
            return self._process_token_transfer(state, event_address, args)
        amount = int(args["amount"])

        from_ = args["from"]
        from_balances = market.users[from_].balances
        if from_ != event_address:
            assert (
                from_balances.token_balance >= amount
            ), f"token balance can never be negative, {from_balances.token_balance} < {amount}"
            from_balances.token_balance -= amount

        to = args["to"]
        if to != event_address:
            market.users[to].balances.token_balance += amount

    def _process_token_transfer(self, state: State, event_address: str, args: dict):
        address_from = get_any_key(args, ["from", "_from", "src"])
        address_to = get_any_key(args, ["to", "_to", "dst"])
        amount = int(get_any_key(args, ["amount", "value", "wad", "_value"]))

        market_meta = self.markets_metadata.get(event_address)
        if not market_meta:
            return
        cmarket_address = market_meta["address"]
        cmarket = state.markets.find_by_address(cmarket_address)

        if cmarket_address == address_from:
            assert (
                cmarket.balances.total_underlying >= amount
            ), f"total supplied can never be negative, {cmarket.balances.total_underlying} < {amount}"
            cmarket.balances.total_underlying -= amount
            if address_to == constants.NULL_ADDRESS:
                cmarket.transfer_in(amount)

        if cmarket_address == address_to:
            cmarket.balances.total_underlying += amount

    def process_chi_updated(self, state: State, _event_address: str, args: dict):
        market = self._find_or_add_market(state, constants.CDAI_ADDRESS)
        market.chi = int(args["chi"])

    def process_borrow(self, state: State, event_address: str, args: dict):
        market = state.markets.find_by_address(event_address)
        amount = int(args["borrowAmount"])
        market.balances.total_borrowed = int(args["totalBorrows"])

        # NOTE: ERC20 tokens are handled through the transfer event
        if event_address == constants.CETH_ADDRESS:
            assert (
                market.balances.total_underlying >= amount
            ), f"total supplied can never be negative, {market.balances.total_underlying} < {amount}"
            market.balances.total_underlying -= amount

        # NOTE: CDAI uses DSR so Transfer comes from NULL address
        if self._should_handle_dsr(market):
            market.transfer_out(amount)

        borrower = args["borrower"]
        self.update_user_borrow(market, borrower)
        market.users[borrower].balances.total_borrowed += int(args["borrowAmount"])

    def process_repay_borrow(self, state: State, event_address: str, args: dict):
        borrower = args["borrower"]
        amount = int(args["repayAmount"])
        market = state.markets.find_by_address(event_address)
        self.update_user_borrow(market, borrower)
        user_balances = market.users[borrower].balances
        assert (
            market.balances.total_borrowed >= amount
        ), f"borrow can never be negative, {market.balances.total_borrowed} < {amount}"
        assert (
            user_balances.total_borrowed >= amount
        ), f"borrow can never be negative, {user_balances.total_borrowed} < {amount}"

        market.balances.total_borrowed = int(args["totalBorrows"])
        # NOTE: ERC20 tokens are handled through the transfer event
        if event_address == constants.CETH_ADDRESS:
            market.balances.total_underlying += amount

        user_balances.total_borrowed -= amount

    def process_liquidate_borrow(self, state: State, event_address: str, args: dict):
        # NOTE: repay and transfer will be emitted with each liquidation
        pass

    def process_reserves_added(self, state: State, event_address: str, args: dict):
        market = state.markets.find_by_address(event_address)
        market.reserves += int(args["addAmount"])

    def process_reserves_reduced(self, state: State, event_address: str, args: dict):
        market = state.markets.find_by_address(event_address)
        assert market.reserves >= int(
            args["reduceAmount"]
        ), f"reserves can never be negative, {market.reserves} < {args['reduceAmount']}"
        market.reserves -= int(args["reduceAmount"])

    def process_new_price_oracle(self, state: State, _event_address: str, args: dict):
        address = args["newPriceOracle"]
        state.oracles.create_oracle(address)
        state.oracles.current_address = address

    def process_price_posted(self, state: State, event_address: str, args: dict):
        oracle = state.oracles.get_oracle(event_address)
        value = int(args["newPriceMantissa"])
        oracle.update_price(args["asset"], value)

    def process_external_price_updated(
        self, state: State, event_address: str, args: dict
    ):
        oracle = state.oracles.get_oracle(event_address)
        oracle.update_price(args["symbol"], args["price"])

    def process_price_updated(self, state: State, event_address: str, args: dict):
        oracle = state.oracles.get_oracle(event_address)
        value = int(args["price"])
        oracle.update_price(args["symbol"], value)

    def process_sai_price_set(self, state: State, event_address: str, args: dict):
        oracle = state.oracles.get_oracle(event_address)
        value = int(args["newPriceMantissa"])
        oracle.sai_price = value

    def process_inverted_price_posted(
        self, state: State, _event_address: str, args: dict
    ):
        # virtual event generated when Oracle DSValue is updated
        oracle = state.oracles.get_oracle(constants.PRICE_V1_ORACLE_ADDRESS)
        value = int(args["newPriceMantissa"])
        for ctoken in args["tokens"]:
            oracle.update_price(ctoken, value, inverted=True)

    def process_new_interest_params(self, state: State, event_address: str, args: dict):
        try:
            model = state.interest_rate_models.get_model(event_address)
        except KeyError:
            model = state.interest_rate_models.create_model(event_address)
        model.update_params(args)

    def process_accrue_interest(self, state: State, event_address: str, args: dict):
        market = state.markets.find_by_address(event_address)
        market.balances.total_borrowed = int(args["totalBorrows"])
        market.borrow_index = int(args["borrowIndex"])
        market.reserves += int(int(args["interestAccumulated"]) * market.reserve_factor)

    def process_timestamp_updated(self, state: State, _event_address: str, args: dict):
        state.timestamp = args["timestamp"]

    def update_user_borrow(self, market: Market, user_address: str):
        user = market.users[user_address]
        new_total_borrowed = user.borrowed_at(market.borrow_index)
        user.balances.total_borrowed = new_total_borrowed
        user.borrow_index = market.borrow_index

    def _should_handle_dsr(self, market: Market) -> bool:
        return isinstance(market, CDaiMarket) and market.dsr_active

    def _find_or_add_market(self, state: State, address: str) -> Market:
        try:
            market = state.markets.find_by_address(address)
        except ValueError:
            if address == constants.CDAI_ADDRESS:
                market = CDaiMarket(address)
            else:
                market = Market(address)
            state.markets.add_market(market)
        return market

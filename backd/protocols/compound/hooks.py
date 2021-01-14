from __future__ import annotations

from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Set, Tuple, Union

import pandas as pd
import stringcase

from ...hook import Hook
from .constants import CETH_ADDRESS, PRICE_RATIOS_KEY
from .entities import CompoundState


@Hook.register("borrowers")
class Borrowers(Hook):
    extra_key = "borrowers"

    @dataclass
    class HookState:
        current_users: Set[str] = None
        historical_count: Dict[int, int] = None

        def __post_init__(self):
            if self.current_users is None:
                self.current_users = set()
            if self.historical_count is None:
                self.historical_count = OrderedDict()

    def __init__(self):
        self.hook_state = self.__class__.HookState()

    def global_start(self, state: CompoundState):
        if self.extra_key not in state.extra:
            state.extra[self.extra_key] = self.hook_state

    def event_end(self, state: CompoundState, event: dict):
        if event["event"] not in ["RepayBorrow", "Borrow"]:
            return
        user = event["returnValues"]["borrower"]
        for market in state.markets:
            total_borrowed = market.users[user].balances.total_borrowed
            if total_borrowed > 0:
                self.hook_state.current_users.add(user)
                break
        else:
            self.hook_state.current_users.discard(user)

    def block_end(self, state: CompoundState, block_number: int):
        self.hook_state.historical_count[block_number] = len(
            self.hook_state.current_users
        )


class NonZeroUsers:
    HookState = Borrowers.HookState


@Hook.register("suppliers")
class Suppliers(Hook):
    extra_key = "suppliers"

    @dataclass
    class HookState:
        current_users: Set[str] = None
        historical_count: Dict[int, int] = None

        def __post_init__(self):
            if self.current_users is None:
                self.current_users = set()
            if self.historical_count is None:
                self.historical_count = OrderedDict()

    def __init__(self):
        self.hook_state = self.__class__.HookState()

    def global_start(self, state: CompoundState):
        if self.extra_key not in state.extra:
            state.extra[self.extra_key] = self.hook_state

    def event_end(self, state: CompoundState, event: dict):
        args = event["returnValues"]
        if event["event"] == "Mint":
            users = [args["minter"]]
        elif event["event"] == "Redeem":
            users = [args["redeemer"]]
        elif event["event"] == "LiquidateBorrow":
            users = [args["borrower"], args["liquidator"]]
        else:
            return

        for user in users:
            for market in state.markets:
                if market.users[user].balances.token_balance > 0:
                    self.hook_state.current_users.add(user)
                    break
            else:
                self.hook_state.current_users.discard(user)

    def block_end(self, state: CompoundState, block_number: int):
        self.hook_state.historical_count[block_number] = len(
            self.hook_state.current_users
        )


@Hook.register("supply-borrow")
class SupplyBorrow(Hook):
    extra_key = "supply-borrow"

    def __init__(self):
        self.supply_borrows = []

    def global_end(self, state: CompoundState):
        state.extra[self.extra_key] = pd.DataFrame(self.supply_borrows)

    def block_end(self, state: CompoundState, block_number: int):
        supply_per_market = state.compute_supply_per_market()
        borrow_per_market = state.compute_borrows_per_market()
        underlying_per_market = state.compute_underlying_per_market()
        for market in supply_per_market:
            self.supply_borrows.append(
                {
                    "block": block_number,
                    "timestamp": state.timestamp,
                    "market": market,
                    "supply": supply_per_market[market],
                    "borrows": borrow_per_market[market],
                    "underlying": underlying_per_market[market],
                }
            )


@Hook.register("leverage-spirals")
class LeverageSpirals(Hook):
    HANDLED_EVENTS = {"Borrow", "Mint", "RepayBorrow", "Redeem"}

    extra_key = "leverage-spirals"

    @dataclass
    class Balance:
        borrowed: float = 0
        minted: float = 0
        net_borrowed: float = 0
        # net minted is the amount minted from fresh funds in terms of USD
        net_minted: float = 0

        @property
        def minted_recycled(self) -> float:
            return self.minted - self.net_minted

    @dataclass
    class UserStats:
        @staticmethod
        def create_balance():
            return LeverageSpirals.Balance()

        current_balance: LeverageSpirals.Balance = field(
            default_factory=create_balance.__func__
        )
        max_balance: LeverageSpirals.Balance = field(
            default_factory=create_balance.__func__
        )

        def update_max(self):
            if self.current_balance.minted_recycled > self.max_balance.minted_recycled:
                self.current_balance = self.max_balance

    def __init__(self):
        # user -> spiral
        self.users_stats: Dict[str, LeverageSpirals.UserStats] = defaultdict(
            LeverageSpirals.UserStats
        )

    def global_start(self, state: CompoundState):
        if self.extra_key not in state.extra:
            state.extra[self.extra_key] = self.users_stats

    def event_start(self, state: CompoundState, event: dict):
        if event["event"] not in self.HANDLED_EVENTS:
            return
        normalized_event = stringcase.snakecase(event["event"])
        getattr(self, f"_handle_{normalized_event}")(state, event)

    def _handle_mint(self, state: CompoundState, event: dict):
        user_stats = self._get_user_stats("minter", event)
        usd_amount = self._get_usd_amount("mintAmount", state, event)

        user_stats.current_balance.minted += usd_amount
        user_stats.current_balance.net_minted += max(
            0, usd_amount - user_stats.current_balance.net_borrowed
        )
        user_stats.current_balance.net_borrowed -= min(
            user_stats.current_balance.net_borrowed, usd_amount
        )

        user_stats.update_max()

    def _handle_borrow(self, state: CompoundState, event: dict):
        user_stats = self._get_user_stats("borrower", event)
        usd_amount = self._get_usd_amount("borrowAmount", state, event)
        user_stats.current_balance.borrowed += usd_amount
        user_stats.current_balance.net_borrowed += usd_amount

        user_stats.update_max()

    def _handle_repay_borrow(self, state: CompoundState, event: dict):
        user_stats = self._get_user_stats("borrower", event)
        usd_amount = self._get_usd_amount("repayAmount", state, event)
        user_stats.current_balance.borrowed -= min(
            user_stats.current_balance.borrowed, usd_amount
        )
        user_stats.current_balance.net_borrowed -= min(
            user_stats.current_balance.net_borrowed, usd_amount
        )

        user_stats.update_max()

    def _handle_redeem(self, state: CompoundState, event: dict):
        user_stats = self._get_user_stats("redeemer", event)
        usd_amount = self._get_usd_amount("redeemAmount", state, event)

        user_stats.current_balance.minted -= min(
            user_stats.current_balance.minted, usd_amount
        )
        user_stats.current_balance.net_minted -= min(
            user_stats.current_balance.net_minted, usd_amount
        )

        user_stats.update_max()

    def _get_user_stats(self, key: str, event: dict):
        user = event["returnValues"][key]
        return self.users_stats[user]

    def _get_usd_amount(self, key: str, state: CompoundState, event: dict):
        amount = int(event["returnValues"][key])
        return state.token_to_usd(amount, event["address"])


@Hook.register("users-borrow-supply")
class UsersBorrowSupply(Hook):
    extra_key = "users-borrow-supply"

    @classmethod
    def list_dependencies(cls):
        return [Borrowers.registered_name]

    def __init__(self):
        # block -> users -> (supply, borrow)
        self.hook_state: Dict[int, Dict[str, Tuple[int, int]]] = OrderedDict()

    def global_start(self, state: CompoundState):
        if self.extra_key not in state.extra:
            state.extra[self.extra_key] = self.hook_state

    def block_end(self, state: CompoundState, block_number: int):
        if block_number % 100 != 0:
            return
        self.hook_state[block_number] = {}
        current_users = state.extra[Borrowers.extra_key].current_users
        for user in current_users:
            self.hook_state[block_number][user] = state.compute_user_position(user)


@Hook.register("users-borrow-supply-sensitivity")
class UsersBorrowSupplySensitivity(UsersBorrowSupply):
    ratio_key = PRICE_RATIOS_KEY

    def __init__(self, ratios: Dict[str, Union[Decimal, str]] = None):
        super().__init__()
        if ratios is None:
            ratios = {}
        ratios = {market: Decimal(ratio) for market, ratio in ratios.items()}
        self.price_ratios = ratios

    def global_start(self, state: CompoundState):
        super().global_start(state)
        state.extra[self.ratio_key] = self.price_ratios


@Hook.register("liquidation-stats")
class LiquidationAmounts(Hook):
    extra_key = "liquidation-stats"

    def __init__(self):
        self.liquidations = []

    def global_end(self, state: CompoundState):
        state.extra[self.extra_key] = pd.DataFrame(self.liquidations)

    def get_liquidation(self, state: CompoundState, event: dict):
        args = event["returnValues"]
        cmarket = state.markets.find_by_address(args["cTokenCollateral"])
        token_seized = int(args["seizeTokens"])
        usd_seized = state.ctoken_to_usd(token_seized, cmarket)
        return {
            "block_number": event["blockNumber"],
            "timestamp": state.timestamp,
            "market": cmarket.address,
            "transaction_hash": event["transactionHash"],
            "transaction_index": event["transactionIndex"],
            "usd_seized": usd_seized,
            "token_seized": token_seized,
            "eth_price": state.oracles.current.get_underlying_price(CETH_ADDRESS),
        }

    def event_end(self, state: CompoundState, event: dict):
        if event["event"] != "LiquidateBorrow":
            return
        self.liquidations.append(self.get_liquidation(state, event))


@Hook.register("liquidation-with-time")
class LiquidationAmountsWithTime(LiquidationAmounts):
    extra_key = "liquidation-with-time"

    # do not check accounts with > 20% overcollateral unless they are modified
    threshold = 1.2
    ttl = 100  # blocks before removing from above threshold

    _user_mapping = {
        "Borrow": ["borrower"],
        "Mint": ["minter"],
        "Redeem": ["redeemer"],
        "RepayBorrow": ["borrower"],
        "LiquidateBorrow": ["borrower", "liquidator"],
    }

    @classmethod
    def list_dependencies(cls):
        return [Borrowers.registered_name]

    def __init__(self):
        super().__init__()
        self.liquidable = {}
        self.above_threshold = set()
        self.above_threshold_blocks = {}
        self.touched = set()

    def get_liquidation(self, state: CompoundState, event: dict):
        liquidation = super().get_liquidation(state, event)
        block_ellapsed = 0
        borrower = event["returnValues"]["borrower"]
        if borrower in self.liquidable:
            block_ellapsed = event["blockNumber"] - self.liquidable[borrower]
            del self.liquidable[borrower]
        liquidation["block_ellapsed"] = block_ellapsed
        return liquidation

    def block_start(self, state: CompoundState, block_number: int):
        self.touched = set()
        self.above_threshold_blocks[block_number] = []

    def event_start(self, state: CompoundState, event: dict):
        if event["event"] in self._user_mapping:
            self.touched |= self._get_users(event)

    def _get_users(self, event: dict):
        return set(
            event["returnValues"][key] for key in self._user_mapping[event["event"]]
        )

    def block_end(self, state: CompoundState, block_number: int):
        current_users = state.extra[Borrowers.extra_key].current_users
        liquidable = set()

        block_to_remove = block_number - self.ttl
        if block_to_remove in self.above_threshold_blocks:
            for user in self.above_threshold_blocks[block_to_remove]:
                self.above_threshold.discard(user)
            del self.above_threshold_blocks[block_to_remove]

        # avoid going through all the users
        to_check = (current_users - self.above_threshold) | self.touched

        for user in to_check:
            supply, borrow = state.compute_user_position(user)
            if borrow > supply:
                liquidable.add(user)
            elif borrow > 0 and supply / borrow > self.threshold:
                if user not in self.above_threshold:
                    self.above_threshold.add(user)
                    self.above_threshold_blocks[block_number].append(user)

        # add new liquidable
        for user in liquidable:
            self.liquidable.setdefault(user, block_number)

        # remove users not anymore liquidale
        for user in self.liquidable.keys() - liquidable:
            del self.liquidable[user]

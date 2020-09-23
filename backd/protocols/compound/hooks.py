from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

import pandas as pd

from ...hook import Hook
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


@Hook.register("leverage-spirals")
class LeverageSpirals(Hook):
    extra_key = "leverage-spirals"

    @dataclass
    class Spiral:
        transaction_hash: str
        start_position: Tuple[int, int]
        start_market_positions: Dict[str, Dict[str, int]]
        events: List[dict] = field(default_factory=list)

        end_position: Tuple[int, int] = None
        end_market_positions: Dict[str, Dict[str, int]] = None

    def __init__(self):
        # block -> user -> spiral
        self.all_spirals: Dict[int, Dict[str, LeverageSpirals.Spiral]] = OrderedDict()
        self.current_tx_spirals: Dict[str, LeverageSpirals.Spiral] = {}

    def global_start(self, state: CompoundState):
        if self.extra_key not in state.extra:
            state.extra[self.extra_key] = self.all_spirals

    def block_start(self, state: CompoundState, block_number: int):
        self.all_spirals[block_number] = {}

    def transaction_start(
        self, state: CompoundState, block_number: int, transaction_index: int
    ):
        self.current_tx_spirals = {}

    def transaction_end(
        self, state: CompoundState, block_number: int, transaction_index: int
    ):
        for user, spiral in self.current_tx_spirals.items():
            if self._is_spiral(spiral):
                spiral.end_position = state.compute_user_position(user)
                spiral.end_market_positions = state.get_user_positions(user)
                self.all_spirals[block_number][user] = spiral

    def _is_spiral(self, spiral: dict):
        borrow_events = (1 for k in spiral.events if k["event"] == "Borrow")
        if sum(borrow_events) <= 1:
            return False

        mint_events = (1 for k in spiral.events if k["event"] == "Mint")
        if sum(mint_events) <= 1:
            return False
        return True

    def _initialize_user(self, user: str, event: dict, state: CompoundState):
        spiral = self.__class__.Spiral(
            transaction_hash=event["transactionHash"],
            start_position=state.compute_user_position(user),
            start_market_positions=state.get_user_positions(user),
        )
        self.current_tx_spirals[user] = spiral

    def event_start(self, state: CompoundState, event: dict):
        if event["event"] not in ["Borrow", "Mint"]:
            return
        user = self._get_user(event)
        if user not in self.current_tx_spirals:
            self._initialize_user(user, event, state)
        self.current_tx_spirals[user].events.append(event)

    def _get_user(self, event: dict):
        key = {"Borrow": "borrower", "Mint": "minter"}[event["event"]]
        return event["returnValues"][key]


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
        }

    def event_start(self, state: CompoundState, event: dict):
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
        self.liquidatable = {}
        self.above_threshold = set()
        self.above_threshold_blocks = {}
        self.touched = set()

    def get_liquidation(self, state: CompoundState, event: dict):
        liquidation = super().get_liquidation(state, event)
        block_ellapsed = 0
        borrower = event["returnValues"]["borrower"]
        if borrower in self.liquidatable:
            block_ellapsed = event["blockNumber"] - self.liquidatable[borrower]
            del self.liquidatable[borrower]
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
        liquidatable = set()

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
                liquidatable.add(user)
            elif borrow > 0 and supply / borrow > self.threshold:
                if user not in self.above_threshold:
                    self.above_threshold.add(user)
                    self.above_threshold_blocks[block_number].append(user)

        # add new liquidatable
        for user in liquidatable:
            self.liquidatable.setdefault(user, block_number)

        # remove users not anymore liquidatable
        for user in self.liquidatable.keys() - liquidatable:
            del self.liquidatable[user]

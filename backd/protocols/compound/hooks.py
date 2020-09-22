from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from ...hook import Hook
from .entities import CompoundState


@Hook.register("non-zero-users")
class NonZeroUsers(Hook):
    extra_key = "non_zero_users"

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
        return ["non-zero-users"]

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
        current_users = state.extra[NonZeroUsers.extra_key].current_users
        for user in current_users:
            self.hook_state[block_number][user] = state.compute_user_position(user)

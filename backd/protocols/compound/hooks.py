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
        end_position: Tuple[int, int]
        events: List[dict]

        def __post_init__(self):
            self.events = []

    @dataclass
    class HookState:
        # all_spirals: Dict[int, Dict[str, Dict]] = None
        all_spirals: Dict[int, Dict[str, Spiral]]
        seen_tx_users: Set[str] = None

        def __post_init__(self):
            if self.all_spirals is None:
                self.all_spirals = {}

    def __init__(self):
        self.hook_state = self.__class__.HookState()

    def transaction_start(
        self, state: CompoundState, block_number: int, transaction_index: int
    ):
        self.hook_state.seen_tx_users = set()

    def transaction_end(
        self, state: CompoundState, block_number: int, transaction_index: int
    ):
        # compute the latest balances for all seen users in spirals
        for user in self.hook_state.seen_tx_users:
            total_collateral, total_borrows = state.compute_user_position(user)
            self.hook_state.all_spirals[block_number][user]["end_position"] = (
                total_borrows,
                total_collateral,
            )

            # check if this TX is a spiral and remove if not
            if not self._is_spiral(self.hook_state.all_spirals[block_number][user]):
                del self.hook_state.all_spirals[block_number][user]

    def _is_spiral(self, spiral: dict):
        borrow_events = (1 for k in spiral["events"] if k["event"] == "Borrow")
        if sum(borrow_events) <= 1:
            return False

        mint_events = (1 for k in spiral["events"] if k["event"] == "Mint")
        if sum(mint_events) <= 1:
            return False
        return True

    def _seen_user(self, user: str, event: dict, state: CompoundState):
        self.hook_state.seen_tx_users.add(user)
        total_collateral, total_borrows = state.compute_user_position(user)
        print("here")
        blockNumber = event["blockNumber"]
        self.hook_state.all_spirals[blockNumber] = {
            user: {"transaction_hash": event["transactionHash"]}
        }
        print("there")
        self.hook_state.all_spirals[blockNumber][user]["start_position"][
            0
        ] = total_borrows
        self.hook_state.all_spirals[blockNumber][user]["start_position"][
            1
        ] = total_collateral

    def event_start(self, state: CompoundState, event: dict):
        blockNumber = event["blockNumber"]
        if event["event"] == "Borrow":
            user = event["returnValues"]["borrower"]
            if user not in self.hook_state.seen_tx_users:
                self._seen_user(user, event, state)
            self.hook_state.all_spirals[blockNumber][user]["events"].append(event)
        elif event["event"] == "Mint":
            user = event["returnValues"]["minter"]
            if user not in self.hook_state.seen_tx_users:
                self._seen_user(user, event, state)
            self.hook_state.all_spirals[blockNumber][user]["events"].append(event)

    def event_end(self, state: CompoundState, event: dict):
        pass

    def global_start(self, state: CompoundState):
        pass

    def global_end(self, state: CompoundState):
        pass


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

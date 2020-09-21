from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Set, Tuple

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
            else:
                self.hook_state.current_users.discard(user)

    def block_end(self, state: CompoundState, block_number: int):
        self.hook_state.historical_count[block_number] = len(
            self.hook_state.current_users
        )


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
        self.hook_state[block_number] = {}
        current_users = state.extra[NonZeroUsers.extra_key].current_users
        for user in current_users:
            self.hook_state[block_number][user] = state.compute_user_position(user)

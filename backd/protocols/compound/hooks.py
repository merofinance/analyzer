from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Set

from ...entities import State
from ...hook import Hook


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
        self.state = NonZeroUsers.HookState()

    def global_start(self, state: State):
        if self.extra_key not in state.extra:
            state.extra[self.extra_key] = self.state

    def event_end(self, state: State, event: dict):
        if event["event"] not in ["RepayBorrow", "Borrow"]:
            return
        user = event["returnValues"]["borrower"]
        for market in state.markets:
            total_borrowed = market.users[user].balances.total_borrowed
            if total_borrowed > 0:
                self.state.current_users.add(user)
            else:
                self.state.current_users.discard(user)

    def block_end(self, state: State, block_number: int):
        self.state.historical_count[block_number] = len(self.state.current_users)

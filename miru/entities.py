from typing import List
import dataclasses
from dataclasses import dataclass


@dataclass
class PointInTime:
    block_number: int
    transaction_index: int
    log_index: int

    @classmethod
    def from_event(cls, event: dict) -> "PointInTime":
        return cls(
            block_number=event["blockNumber"],
            transaction_index=event["transactionIndex"],
            log_index=event["logIndex"]
        )


@dataclass
class UserMarket:
    address: str
    total_borrowed: int = 0
    total_supplied: int = 0
    token_balance: int = 0

    def __init__(self,
                 address: str,
                 total_borrowed: int = 0,
                 total_supplied: int = 0,
                 token_balance: int = 0):
        self.address = address.lower()
        self.total_borrowed = total_borrowed
        self.total_supplied = total_supplied
        self.token_balance = token_balance

    def replace(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self


@dataclass
class UserMarkets:
    markets: List[UserMarket]

    def __init__(self, markets: List[UserMarket] = None):
        if markets is None:
            markets = []
        self.markets = markets

    def find_by_address(self, address: str) -> UserMarket:
        normalized_address = address.lower()
        for market in self.markets:
            if market.address == normalized_address:
                # return a copy
                return dataclasses.replace(market)
        return UserMarket(normalized_address)

    def replace_or_add_market(self, new_market: UserMarket) -> "UserMarkets":
        markets = []
        is_added = False
        for market in self.markets:
            if market.address == new_market.address:
                markets.append(new_market)
                is_added = True
            else:
                markets.append(market)
        if not is_added:
            markets.append(new_market)
        return UserMarkets(markets)

    def __len__(self):
        return len(self.markets)


@dataclass
class State:
    protocol_name: str
    user_address: str
    last_event_time: PointInTime
    markets: UserMarkets

    @classmethod
    def empty(cls, protocol_name: str, user_address: str):
        return cls(protocol_name, user_address, PointInTime(0, 0, 0), UserMarkets())

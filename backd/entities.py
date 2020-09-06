from typing import List, Dict
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal


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
class Balances:
    total_borrowed: int = 0
    total_supplied: int = 0
    token_balance: int = 0


@dataclass
class MarketUser:
    balances: Balances = None
    entered: bool = False

    def __post_init__(self):
        if self.balances is None:
            self.balances = Balances()


@dataclass(eq=False, repr=False)
class Market:
    address: str
    interest_rate_model: str = None
    balances: Balances = None
    reserve_factor: Decimal = Decimal("0")
    collateral_factor: Decimal = Decimal("0")
    close_factor: Decimal = Decimal("0")
    users: Dict[str, MarketUser] = None
    listed: bool = False
    comptroller_address: str = None
    reserves: int = 0

    def __post_init__(self):
        self.address = self.address.lower()
        if self.balances is None:
            self.balances = Balances()
        if self.users is None:
            self.users = defaultdict(MarketUser)

    def __eq__(self, other):
        return self.address == other.address

    def __hash__(self):
        return hash(self.address)

    def __repr__(self):
        return f"Market(address='{self.address}')"


@dataclass
class Markets:
    markets: List[Market]

    def __init__(self, markets: List[Market] = None):
        if markets is None:
            markets = []
        self.markets = markets

    def find_by_address(self, address: str) -> Market:
        normalized_address = address.lower()
        for market in self.markets:
            if market.address == normalized_address:
                return market
        raise ValueError(f"could not find market with address {address}")

    def add_market(self, new_market: Market):
        if any(market == new_market for market in self.markets):
            raise ValueError(f"market {new_market} already exists")
        self.markets.append(new_market)

    def __getitem__(self, key):
        return self.markets[key]

    def __len__(self):
        return len(self.markets)


@dataclass
class Oracle:
    prices: Dict[str, int] = None

    def __post_init__(self):
        if self.prices is None:
            self.prices = {}

    def update_price(self, token: str, price: int):
        self.prices[token.lower()] = price

    def get_price(self, token: str) -> int:
        return self.prices.get(token.lower(), 0)


@dataclass
class Oracles:
    oracles: Dict[str, Oracle] = None

    def __post_init__(self):
        if self.oracles is None:
            self.oracles = {}

    def get_oracle(self, oracle_address: str):
        oracle_address = oracle_address.lower()
        if oracle_address not in self.oracles:
            self.oracles[oracle_address] = Oracle()
        return self.oracles[oracle_address]

    def __len__(self):
        return len(self.oracles)



@dataclass
class State:
    protocol_name: str
    current_event_time: PointInTime = None
    last_event_time: PointInTime = None
    markets: Markets = None
    oracles: Oracles = None

    def __post_init__(self):
        if self.markets is None:
            self.markets = Markets()
        if self.oracles is None:
            self.oracles = Oracles()

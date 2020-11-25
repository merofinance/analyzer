import json
from decimal import Decimal as D
from os import path

import pytest
from hexbytes import HexBytes
from web3.datastructures import AttributeDict

from backd import constants, settings
from backd.entities import Balances, Market, Markets, Oracle
from backd.protocols.compound.interest_rate_models import (
    InterestRateModel,
    JumpRateModel,
)
from backd.protocols.compound.oracles import UniswapAnchorView
from backd.tokens.dai.dsr import DSR

MAIN_USER = "0x1234a"
MAIN_MARKET = "0x1A3B"
MAIN_TOKEN = "0xBA13"
MAIN_ORACLE = "0xAB23"
BORROW_MARKET = "0xA123"
BORROW_TOKEN = "0xB123"

FIXTURES_PATH = path.join(settings.PROJECT_ROOT, "tests", "fixtures")
DUMMY_MARKETS_META = [
    {
        "address": MAIN_MARKET.lower(),
        "underlying_address": MAIN_TOKEN.lower(),
        "underlying_symbol": "MAIN",
    },
    {
        "address": BORROW_MARKET.lower(),
        "underlying_address": BORROW_TOKEN.lower(),
        "underlying_symbol": "BOR",
    },
]


@pytest.fixture
def compound_redeem_event():
    with open(path.join(FIXTURES_PATH, "compound-redeem-event.json")) as f:
        return json.load(f)


@pytest.fixture
def markets():
    return Markets(
        [
            Market("0xa234", balances=Balances(total_borrowed=1, total_underlying=2)),
            Market("0x1A3B"),
            Market("0xA123"),
        ]
    )


@pytest.fixture
def dummy_markets_meta():
    return DUMMY_MARKETS_META


@pytest.fixture
def compound_dummy_events():
    with open(path.join(FIXTURES_PATH, "compound-dummy-events.jsonl")) as f:
        return [json.loads(line) for line in f]


@pytest.fixture
def dummy_dsr_rates():
    return [
        {"blockNumber": 100, "rate": D("1.0") * 10 ** constants.DSR_DECIMALS},
        {"blockNumber": 105, "rate": D("1.1") * 10 ** constants.DSR_DECIMALS},
        {"blockNumber": 110, "rate": D("1.5") * 10 ** constants.DSR_DECIMALS},
    ]


@pytest.fixture
def web3_event():
    return AttributeDict(
        {
            "args": AttributeDict(
                {
                    "from": "0xD3921fead48A2B58d28c0Ac658D5b53e2AEEC347",
                    "to": "0x995E9ADA66D5f3fdEaa3Bb9E3a4d81485563Eb81",
                    "value": 55000000,
                }
            ),
            "event": "Transfer",
            "logIndex": 116,
            "transactionIndex": 80,
            "transactionHash": HexBytes(
                "0x8a582772dd73ca46eae762091379b69df8908272e58e0b2f7b709820fa971a50"
            ),
            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "blockHash": HexBytes(
                "0x7d66485c9f4178b3a631d56cb2d4cc3ba810c98205a8796db4ec7fe7291ed684"
            ),
            "blockNumber": 11329760,
        }
    )


@pytest.fixture
def dsr_rates():
    with open(path.join(settings.PROJECT_ROOT, "data", "dsr-rates.json")) as f:
        rates = []
        for line in f:
            rate = json.loads(line)
            rate["rate"] = D(rate["rate"])
            rates.append(rate)
        return rates


@pytest.fixture
def dsr(dummy_dsr_rates):
    return DSR(dummy_dsr_rates)


def get_event(compound_dummy_events, name, index=0):
    return [v for v in compound_dummy_events if v["event"] == name][index]


def get_events_until(compound_dummy_events, name, index=0):
    indices = [i for i, e in enumerate(compound_dummy_events) if e["event"] == name]
    return compound_dummy_events[: indices[index] + 1]


@InterestRateModel.register("0xbae0")
class DummyInterestRateModel(JumpRateModel):
    pass


@Oracle.register("0xab23")
class DummyOracle(Oracle):
    pass


@Oracle.register("0xabab54")
class DummyUniswapOracle(UniswapAnchorView):
    pass

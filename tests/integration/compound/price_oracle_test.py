import json
from os import path

import pytest
from tqdm import tqdm

from backd import executor, settings
from backd.entities import Oracle
from backd.protocols.compound.oracles import UniswapAnchorView
from backd.protocols.compound.protocol import CompoundProtocol
from tests.fixtures import FIXTURES_PATH


@pytest.fixture
def sample_prices():
    with open(path.join(FIXTURES_PATH, "sample-prices.jsonl")) as f:
        return [json.loads(line) for line in f]


@pytest.mark.skipif(settings.BACKD_ENV == "test", reason="requires full database")
def test_prices(sample_prices):
    protocol = CompoundProtocol()
    state = protocol.create_empty_state()
    last_block_seen = 0
    min_block = sample_prices[0]["block"]
    max_block = sample_prices[-1]["block"]
    events_count = protocol.count_events(min_block, max_block)
    pbar = tqdm(total=events_count, unit="pbar")

    last_block_seen = 0
    for line in sample_prices:
        block = line["block"]
        executor.process_all_events(
            "compound",
            min_block=last_block_seen + 1,
            max_block=block,
            state=state,
            pbar=pbar,
        )
        last_block_seen = block

        for price in line["prices"]:
            oracle = Oracle.get(price["address"].lower())(markets=state.markets)
            usd_price = isinstance(oracle, UniswapAnchorView)
            expected_price = price["price"]
            actual = oracle.get_underlying_price(price["asset"], usd_price=usd_price)
            assert actual == expected_price, f"price oracle divereged at block {block}"

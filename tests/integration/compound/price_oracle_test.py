from os import path
import json

import pytest

from tests.conftest import FIXTURES_PATH
from backd.protocols.compound.entities import CompoundState
from backd import executor
from backd.entities import Oracle


@pytest.fixture
def sample_prices():
    with open(path.join(FIXTURES_PATH, "sample-prices.jsonl")) as f:
        return [json.loads(line) for line in f]


def test_prices(sample_prices):
    state = CompoundState.create()
    last_block_seen = 0
    for i, line in enumerate(sample_prices):
        block = line["block"]
        print(f"progress (block = {block}): {i}/{len(sample_prices)}")
        executor.process_all_events(
            "compound", min_block=last_block_seen + 1, max_block=block, state=state)
        last_block_seen = block

        for price in line["prices"]:
            oracle = Oracle.get(price["address"].lower())(
                markets=state.markets)
            expected_price = price["price"]
            assert oracle.get_underlying_price(
                price["asset"]) == expected_price

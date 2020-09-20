from os import path
import json
import gzip

import pytest

from tests.conftest import FIXTURES_PATH
from backd import settings
from backd import executor
from backd.protocols.compound.entities import CompoundState
from backd.protocols.compound.constants import CDAI_ADDRESS


@pytest.fixture
def cdai_cash():
    with gzip.open(path.join(FIXTURES_PATH, "cdai-cash.jsonl.gz")) as f:
        return [json.loads(line) for line in f]


@pytest.mark.skipif(settings.BACKD_ENV == "test", reason="requires full database")
def test_cdai_cash(cdai_cash):
    state = CompoundState.create()
    last_block_seen = 0
    market = None
    for i, line in enumerate(cdai_cash):
        block = line["block"]
        if i % 100 == 0:
            print(f"progress (block = {block}): {i}/{len(cdai_cash)}")
        executor.process_all_events(
            "compound", min_block=last_block_seen + 1, max_block=block, state=state
        )
        last_block_seen = block
        if market is None:
            market = state.markets.find_by_address(CDAI_ADDRESS)
        assert line["result"] / 10 ** 18 == pytest.approx(market.get_cash() / 10 ** 18)

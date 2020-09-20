from os import path
import json
import gzip

import pytest
from tqdm import tqdm

from tests.fixtures import FIXTURES_PATH

from backd import settings
from backd import executor
from backd.protocols.compound.protocol import CompoundProtocol
from backd.protocols.compound.constants import CDAI_ADDRESS


@pytest.fixture
def cdai_cash():
    with gzip.open(path.join(FIXTURES_PATH, "cdai-cash.jsonl.gz")) as f:
        return [json.loads(line) for line in f]


@pytest.mark.skipif(settings.BACKD_ENV == "test", reason="requires full database")
def test_cdai_cash(cdai_cash):
    protocol = CompoundProtocol()
    state = protocol.create_empty_state()
    last_block_seen = 0
    market = None
    min_block = cdai_cash[0]["block"]
    max_block = min(cdai_cash[-1]["block"], protocol.get_max_block())
    events_count = protocol.count_events(min_block, max_block)
    pbar = tqdm(total=events_count, unit="event")

    for line in cdai_cash:
        block = line["block"]
        if block > max_block:
            break
        executor.process_all_events(
            "compound",
            min_block=last_block_seen + 1,
            max_block=block,
            state=state,
            pbar=pbar,
        )
        last_block_seen = block
        if market is None:
            market = state.markets.find_by_address(CDAI_ADDRESS)
        # FIXME: should not need pytest.approx so we probably have a rounding
        # issue somewhere
        assert line["result"] / 10 ** 18 == pytest.approx(
            market.get_cash() / 10 ** 18
        ), f"get_cash diverged at block {block}"

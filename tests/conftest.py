from os import path
import json

import pytest


from backd import settings
from backd.entities import Market, Balances, Markets


FIXTURES_PATH = path.join(settings.PROJECT_ROOT, "tests", "fixtures")


@pytest.fixture
def compound_redeem_event():
    with open(path.join(FIXTURES_PATH, "compound-redeem-event.json")) as f:
        return json.load(f)


@pytest.fixture
def markets():
    return Markets(
        [Market("0xa234", balances=Balances(1, 2)),
         Market("0x1A3B"),
         Market("0xA123")])


@pytest.fixture
def compound_dummy_events():
    with open(path.join(FIXTURES_PATH, "compound-dummy-events.jsonl")) as f:
        return [json.loads(line) for line in f]

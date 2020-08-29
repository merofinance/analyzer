from os import path
import json

import pytest


from miru import settings
from miru.entities import UserMarket


FIXTURES_PATH = path.join(settings.PROJECT_ROOT, "tests", "fixtures")


@pytest.fixture
def compound_redeem_event():
    with open(path.join(FIXTURES_PATH, "compound-redeem-event.json")) as f:
        return json.load(f)


@pytest.fixture
def markets():
    return [UserMarket("0xa234", 1, 2), UserMarket("0xb345", 2, 5)]


@pytest.fixture
def compound_dummy_events():
    with open(path.join(FIXTURES_PATH, "compound-dummy-events.jsonl")) as f:
        return [json.loads(line) for line in f]

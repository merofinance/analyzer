import os
from os import path
import json

os.environ.setdefault("BACKD_ENV", "test")

from backd import settings # pylint: disable=wrong-import-position
from backd.db import db # pylint: disable=wrong-import-position
from scripts.store_dsr import import_dsr_data # pylint: disable=wrong-import-position


FIXTURES_PATH = path.join(settings.PROJECT_ROOT, "tests", "fixtures")

import_dsr_data(path.join(settings.PROJECT_ROOT, "data", "dsr-rates.json"), "dsr")

with open(path.join(FIXTURES_PATH, "compound-dummy-events.jsonl")) as f:
    for line in f:
        event = json.loads(line)
        db.events.insert_one(event)

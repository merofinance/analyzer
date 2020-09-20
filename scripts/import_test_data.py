import os
from os import path
import json

os.environ.setdefault("BACKD_ENV", "test")

from backd import settings  # pylint: disable=wrong-import-position
from backd.db import db  # pylint: disable=wrong-import-position
from scripts.store_int_results import (  # pylint: disable=wrong-import-position
    import_int_values,
)


FIXTURES_PATH = path.join(settings.PROJECT_ROOT, "tests", "fixtures")

db.command("dropDatabase")
import_int_values(
    path.join(settings.PROJECT_ROOT, "data", "dsr-rates.json"), "dsr", "rate"
)

with open(path.join(FIXTURES_PATH, "compound-dummy-events.jsonl")) as f:
    for line in f:
        event = json.loads(line)
        db.events.insert_one(event)

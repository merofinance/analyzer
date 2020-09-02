import argparse
import json
from decimal import Decimal

from bson import Decimal128

from smart_open import open as smart_open

from backd.db import db


parser = argparse.ArgumentParser(prog="store-dsr")
parser.add_argument("input", help="path to the jsonl file with DSR rates")
parser.add_argument("-c", "--collection", required=True, help="collection to store rates")

args = parser.parse_args()

collection = db[args.collection]

current_rate = None
with smart_open(args.input) as f:
    for line in f:
        parsed = json.loads(line)
        if parsed["result"] != current_rate:
            current_rate = parsed["result"]
            collection.insert_one({
                "block": parsed["block"],
                "rate": Decimal128(Decimal(current_rate))
            })

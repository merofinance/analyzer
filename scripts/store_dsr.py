import argparse
import json
from decimal import Decimal

from bson import Decimal128

from smart_open import open as smart_open

from backd.db import db


parser = argparse.ArgumentParser(prog="store-dsr")
parser.add_argument("input", help="path to the jsonl file with DSR rates")
parser.add_argument("-c", "--collection", default="dsr", help="collection to store rates")


def import_dsr_data(input_file, collection):
    collection = db[collection]

    current_rate = None
    with smart_open(input_file) as f:
        for line in f:
            parsed = json.loads(line)
            rate = parsed.get("result", parsed.get("rate"))
            if not rate:
                raise ValueError("invalid format, rate not found")
            if rate != current_rate:
                current_rate = rate
                collection.insert_one({
                    "block": parsed["block"],
                    "rate": Decimal128(Decimal(current_rate))
                })


def main():
    args = parser.parse_args()
    import_dsr_data(args.input, args.collection)


if __name__ == "__main__":
    main()

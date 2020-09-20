import argparse
import json
from decimal import Decimal

from bson import Decimal128

from smart_open import open as smart_open

from backd.db import db


parser = argparse.ArgumentParser(prog="store-int-result")
parser.add_argument("input", help="path to the jsonl file with DSR rates")
parser.add_argument(
    "-c", "--collection", required=True, help="collection to store int results"
)
parser.add_argument("-f", "--field", required=True, help="field to store int results")


def import_int_values(input_file, collection, field):
    collection = db[collection]

    current_value = None
    with smart_open(input_file) as f:
        for line in f:
            parsed = json.loads(line)
            value = parsed.get("result", parsed.get(field))
            if not value:
                raise ValueError(f"invalid format, {field} not found")
            block = parsed.get("block", parsed.get("blockNumber"))
            if not block:
                raise ValueError("invalid format, block number not found")
            if value != current_value:
                current_value = value
                collection.insert_one(
                    {
                        "blockNumber": block,
                        field: Decimal128(Decimal(current_value)),
                    }
                )


def main():
    args = parser.parse_args()
    import_int_values(args.input, args.collection, args.field)


if __name__ == "__main__":
    main()

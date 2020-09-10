import argparse
import json
from decimal import Decimal

from bson import Decimal128

from smart_open import open as smart_open

from backd.db import db


parser = argparse.ArgumentParser(prog="store-usdc-prices")
parser.add_argument("input", help="path to the jsonl file with USDC prices")
parser.add_argument("-c", "--collection", default="usdc", help="collection to store rates")


def import_usdc_price(input_file, collection):
    collection = db[collection]

    current_price = None
    with smart_open(input_file) as f:
        for line in f:
            parsed = json.loads(line)
            price, is_set = parsed.get("result", [parsed.get("rate"), True])
            if not price:
                raise ValueError("invalid format, rate not found")
            if not is_set:
                price = "0"
            if price != current_price:
                current_price = price
                collection.insert_one({
                    "block": parsed["block"],
                    "rate": Decimal128(Decimal(int(current_price, 16))),
                })

def main():
    args = parser.parse_args()
    import_usdc_price(args.input, args.collection)


if __name__ == "__main__":
    main()

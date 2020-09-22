import argparse
import csv
import datetime as dt
from decimal import Decimal

from bson import Decimal128

from backd import db

parser = argparse.ArgumentParser(prog="store-prices")
parser.add_argument("input", help="CSV input file")

args = parser.parse_args()

prices = []
with open(args.input) as f:
    for row in csv.DictReader(f):
        close_time = row["close_time"]
        # workaround %z in strptime
        if close_time.endswith("+00"):
            close_time += "00"
        prices.append(
            {
                "symbol": row["symbol"],
                "price": Decimal128(Decimal(row["close"])),
                "timestamp": dt.datetime.strptime(close_time, "%Y-%m-%d %H:%M:%S%z"),
            }
        )

prices = sorted(prices, key=lambda v: v["timestamp"])

block_dates = db.get_block_dates()
block_dates_iter = iter(block_dates.items())
block, block_date = next(block_dates_iter)
prices_to_insert = {}
for price in prices:
    while block_date < price["timestamp"]:
        block, block_date = next(block_dates_iter)
    price["blockNumber"] = block
    prices_to_insert[block] = price

db.prices().insert_many(list(prices_to_insert.values()))

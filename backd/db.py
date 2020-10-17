import datetime as dt

import pymongo
from bson.codec_options import CodecOptions

from . import constants, settings
from .utils.caching import cache

SORT_KEY = [
    ("blockNumber", pymongo.ASCENDING),
    ("transactionIndex", pymongo.ASCENDING),
    ("logIndex", pymongo.ASCENDING),
]


client = pymongo.MongoClient(settings.DATABASE_URL)
db = client.get_database()


def create_indices():
    db.events.create_index("event")
    db.events.create_index("address")

    db.events.create_index(SORT_KEY, unique=True)

    for key in ["minter", "redeemer", "borrower"]:
        db.events.create_index(f"returnValues.{key}")

    db.dsr.create_index("blockNumber", unique=True)

    db.ds_values.create_index("blockNumber", unique=True)
    db.ds_values.create_index("address")

    db.chi_values.create_index("blockNumber", unique=True)

    db.blocks.create_index("blockNumber", unique=True)

    db.prices.create_index("blockNumber", unique=True)


def iterate_events():
    return db.events.find().sort(SORT_KEY)


def count_events():
    return db.events.count_documents({})


@cache(constants.DAY)
def get_block_dates():
    projection = {"_id": False, "blockNumber": True, "timestamp": True}
    return {
        b["blockNumber"]: dt.datetime.fromtimestamp(
            int(b["timestamp"]), dt.timezone.utc
        )
        for b in db.blocks.find(projection=projection)
    }


def prices():
    options = CodecOptions(tz_aware=True)
    return db.get_collection("prices", codec_options=options)

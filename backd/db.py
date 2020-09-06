import pymongo

from . import settings


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

    db.dsr.create_index("block", unique=True)


def iterate_events():
    return db.events.find().sort(SORT_KEY)

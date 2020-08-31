import pymongo

from . import settings


client = pymongo.MongoClient(settings.DATABASE_URL)
db = client.get_database()


def create_indices():
    db.events.create_index("event")

    db.events.create_index([
        ("blockNumber", pymongo.ASCENDING),
        ("transactionIndex", pymongo.ASCENDING),
        ("logIndex", pymongo.ASCENDING),
    ])

    for key in ["minter", "redeemer", "borrower"]:
        db.events.create_index(f"returnValues.{key}")

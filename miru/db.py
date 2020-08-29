from pymongo import MongoClient

from . import settings


client = MongoClient(settings.DATABASE_URL)
db = client.get_database()


def create_indices():
    db.events.create_index("event")
    for key in ["minter", "redeemer", "borrower"]:
        db.events.create_index(f"returnValues.{key}")

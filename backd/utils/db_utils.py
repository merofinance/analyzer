from typing import List

import pymongo

from ..db import db


def fetch_user_events(address: str) -> List[dict]:
    return db.events.find(
        {
            "$or": [
                {"event": "Mint", "returnValues.minter": address},
                {"event": "Redeem", "returnValues.redeemer": address},
                {"event": "Borrow", "returnValues.borrower": address},
                {"event": "RepayBorrow", "returnValues.borrower": address},
                {"event": "LiquidateBorrow", "returnValues.borrower": address},
                {"event": "LiquidateBorrow", "returnValues.liquidator": address},
            ]
        }
    ).sort(
        [
            ("blockNumber", pymongo.ASCENDING),
            ("transactionIndex", pymongo.ASCENDING),
            ("logIndex", pymongo.ASCENDING),
        ]
    )

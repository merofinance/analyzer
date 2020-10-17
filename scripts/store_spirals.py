import argparse
import dataclasses
import json
import os
from dataclasses import dataclass
from typing import List

import pymongo
import stringcase
from backd.db import db
from backd.utils.logger import logger

# use cETH as the default asset for which to get all spirals
DEFAULT_ASSET = "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5"

MIN_BLOCK = int(
    db.events.find_one(sort=[("blockNumber", pymongo.ASCENDING)])["blockNumber"]
)
MAX_BLOCK = int(
    db.events.find_one(sort=[("blockNumber", pymongo.DESCENDING)])["blockNumber"]
)

parser = argparse.ArgumentParser(prog="store-leverage-spirals")
parser.add_argument(
    "-m",
    "--market",
    required=True,
    type=str,
    help="path to the jsonl file with DSR rates",
)
parser.add_argument(
    "-f",
    "--file",
    required=True,
    type=str,
    help="output json file to store leverage spiral results",
)
parser.add_argument(
    "-min",
    "--minimum",
    required=False,
    default=MIN_BLOCK,
    type=int,
    help="minimum block from which spirals should be computed",
)
parser.add_argument(
    "-max",
    "--maximum",
    required=False,
    default=MAX_BLOCK,
    type=int,
    help="maximum block from which spirals should be computed",
)
parser.add_argument(
    "-a",
    "--address",
    required=False,
    type=str,
    help="address for which spirals should be computed",
)


@dataclass
class SpiralEvent:
    address: str
    event: str
    log_index: int


@dataclass
class SpiralMintEvent(SpiralEvent):
    mint_amount: int


@dataclass
class SpiralBorrowEvent(SpiralEvent):
    borrow_market: str
    borrow_amount: int
    account_borrows: int


@dataclass
class Spiral:
    collateral_asset: str
    block_number: int
    transaction_index: int
    transaction_hash: str
    events: List[SpiralEvent]


def store_leverage_spirals(
    market: int, file: str, start_block: int = MIN_BLOCK, end_block: int = MAX_BLOCK
):
    """
    Iterates over all events for a given block range and records all leverage
    spirals that occur within a single transaction. The state of a spiral is
    updated to contain all of the spiral events until the Transaction Index or
    the Block Number changes. A spiral has to contain the 'market' asset as
    collateral. Note: no repays of leverage spirals are recorded at the moment.
    """
    spiral_events = []
    cursor = db.events.find(
        {"blockNumber": {"$gte": start_block, "$lte": end_block}}
    ).sort(
        [
            ("blockNumber", pymongo.ASCENDING),
            ("transactionIndex", pymongo.ASCENDING),
            ("logIndex", pymongo.ASCENDING),
        ]
    )
    event = cursor.next()
    assert event["blockNumber"] >= start_block
    candidate_spiral = Spiral(
        collateral_asset=market,
        block_number=event["blockNumber"],
        transaction_index=event["transactionIndex"],
        transaction_hash=event["transactionHash"],
        events=[],
    )
    last_block_number = event["blockNumber"]
    last_tx_index = event["transactionIndex"]

    for event in cursor:
        if "event" not in event.keys():
            candidate_spiral = Spiral(
                collateral_asset=market,
                block_number=event["blockNumber"],
                transaction_index=event["transactionIndex"],
                transaction_hash=event["transactionHash"],
                events=[],
            )
            continue
        if (event["blockNumber"] != last_block_number) or (
            (event["transactionIndex"] != last_tx_index)
            and (event["blockNumber"] == last_block_number)
        ):
            # check if it is a spiral
            if is_spiral(candidate_spiral):
                print("Spiral: ", candidate_spiral)
                spiral_events.append(dataclasses.asdict(candidate_spiral))
            last_block_number = event["blockNumber"]
            last_tx_index = event["transactionIndex"]
            candidate_spiral = Spiral(
                collateral_asset=market,
                block_number=event["blockNumber"],
                transaction_index=event["transactionIndex"],
                transaction_hash=event["transactionHash"],
                events=[],
            )
        if (event["event"] == "Mint") and (event["address"].lower() == market.lower()):
            spiral_event = process_mint_event(event)
            candidate_spiral.events.append(spiral_event)
        elif event["event"] == "Borrow":
            spiral_event = process_borrow_event(event)
            candidate_spiral.events.append(spiral_event)
    with open(file, "w") as f:
        json.dump(spiral_events, f)


def process_mint_event(event: dict) -> SpiralEvent:
    return SpiralMintEvent(
        event=event["event"],
        log_index=event["logIndex"],
        address=event["returnValues"]["minter"],
        mint_amount=int(event["returnValues"]["mintAmount"]) / 1e18,
    )


def process_borrow_event(event: dict) -> SpiralEvent:
    return SpiralBorrowEvent(
        event=event["event"],
        log_index=event["logIndex"],
        borrow_market=event["address"].lower(),
        address=event["returnValues"]["borrower"],
        borrow_amount=int(event["returnValues"]["borrowAmount"]) / 1e18,
        account_borrows=int(event["returnValues"]["accountBorrows"]) / 1e18,
    )


def is_spiral(candidate: Spiral) -> bool:
    """
    Checks whether the 'candidate' Spiral is a an actual spiral
    (i.e. if it has >1 "mint" and >1 "borrow" events). If so
    it returns true, else it is not a spiral and it returns
    false.
    """
    borrow_events = (1 for k in candidate.events if k.event == "Borrow")
    if sum(borrow_events) <= 1:
        return False

    mint_events = (1 for k in candidate.events if k.event == "Mint")
    if sum(mint_events) <= 1:
        return False
    return True


def main():
    args = parser.parse_args()
    store_leverage_spirals(args.market, args.file, args.minimum, args.maximum)


if __name__ == "__main__":
    main()

from backd.db import db
from dataclasses import dataclass
from backd.logger import logger
from typing import List

import pymongo
import argparse
import stringcase
import json


# https://etherscan.io/address/0x2c8efb2d27c77fed8f6ec911cf534685649e83c7#code

# use cETH as the default asset for which to get all spirals
DEFAULT_ASSET = "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5"

MIN_BLOCK = db.events.find_one(sort=[("blockNumber", pymongo.ASCENDING)])
MAX_BLOCK = db.events.find_one(sort=[("blockNumber", pymongo.DESCENDING)])

parser = argparse.ArgumentParser(prog="store-leverage-spirals")
parser.add_argument("-m", "--market", required=True, help="path to the jsonl file with DSR rates")
parser.add_argument(
    "-f", "--file", required=True, help="output gzip file to store leverage spiral results"
)
parser.add_argument("-min", "--minimum", required=False, help="minimum block from which spirals should be computed") 
parser.add_argument("-max", "--maximum", required=False, help="maximum block from which spirals should be computed") 
parser.add_argument("-a", "--address", required=False, help="address for which spirals should be computed")


@dataclass
class SpiralEvent:
    address: str
    event: str
    log_index: int

@dataclass
class SpiralMintEvent:
    mint_amount: int


@dataclass
class SpiralBorrowEvent:
    borrow_amount: int
    account_borrows: int

@dataclass
class Spiral:
    collateral_asset: str
    block_number: int
    transaction_index: int
    transaction_hash: str
    events: List[SpiralEvent]

def store_leverage_spirals(market: int, 
                            file: str, 
                            start_block: int = MIN_BLOCK,
                            end_block: int = MAX_BLOCK):
    '''
    Iterates over all events for a given block range and records all leverage 
    spirals that occur within a single transaction. The state of a spiral is 
    updated to contain all of the spiral events until the Transaction Index or
    the Block Number changes. A spiral has to contain the 'market' asset as 
    collateral. Note: no repays of leverage spirals are recorded at the moment.
    '''
    print(start_block)
    cursor = db.events.find({"blockNumber": {"$gte": start_block}}).sort(
        [("blockNumber", pymongo.ASCENDING), ("transactionIndex", pymongo.ASCENDING),("logIndex", pymongo.ASCENDING)])
    current_event = cursor.next()
    assert current_event["blockNumber"] >= start_block
    candidate_spiral = Spiral(
                collateral_asset = market,
                block_number = current_event["blockNumber"],
                transaction_index = current_event["transactionIndex"],
                transaction_hash = current_event["transactionHash"]
            )
    last_block_number = start_block
    last_tx_index = current_event["transactionIndex"]

    while current_event['blockNumber'] <= end_block:
        if "event" not in cursor.keys():
            current_event = cursor.next()
            candidate_spiral = Spiral(
                collateral_asset = market,
                block_number = current_event["blockNumber"],
                transaction_index = current_event["transactionIndex"],
                transaction_hash = current_event["transactionHash"]
            )
            continue
        
        if (current_event["blockNumber"] != last_block_number) or ((current_event["transactionIndex"] != last_tx_index) 
            and (current_event["blockNumber"] == last_block_number)):
            # check if it is a spiral
            if is_spiral(candidate_spiral):
                with open(file+'.json', 'a') as f:
                    json.dump(candidate_spiral, f)
            last_block_number = current_event["blockNumber"]
            last_tx_index = current_event["transactionIndex"]
            candidate_spiral = Spiral(
                collateral_asset = market,
                block_number = current_event["blockNumber"],
                transaction_index = current_event["transactionIndex"],
                transaction_hash = current_event["transactionHash"]
            )

        # process current event    
        if (current_event["event"] == "mint") and (current_event["address"].to_lower() == market.to_lower()):
            spiral_event = process_mint_event(current_event)
            candidate_spiral.events.append(spiral_event)
        elif current_event["event"] == "borrow":
            spiral_event = process_borrow_event(current_event)
            candidate_spiral.events.append(spiral_event)
        current_event = cursor.next()

def process_mint_event(event: dict) -> SpiralEvent:
    return SpiralMintEvent(
        event = event["event"],
        log_index = event["resultValues"]["minter"],
        address= event["minter"],
        mint_amount = event['mintAmount'] / 1e18
    )

def process_borrow_event(event: dict) -> SpiralEvent:
    return SpiralBorrowEvent(
        event = event["event"],
        log_index = event['logIndex'],
        borrow_amount = event['borrowAmount'] / 1e18,
        account_borrows = event['accountBorrows'] / 1e18
    )

def is_spiral(candidate: Spiral) -> bool:
    '''
    Checks whether the 'candidate' Spiral is a an actual spiral 
    (i.e. if it has >1 "mint" and >1 "borrow" events). If so 
    it returns true, else it is not a spiral and it returns
    false. 
    '''
    borrow_events = (1 for k in candidate.events if k['event'] == 'Borrow') 
    if sum(borrow_events) <= 1:
        return False

    mint_events = (1 for k in candidate.events if k['event'] == 'Mint') 
    if sum(mint_events) <= 1:
        return False
    return True

def main():
    args = parser.parse_args()
    store_leverage_spirals(args.market, args.file, args.minimum, args.maximum)

if __name__ == "__main__":
    main()

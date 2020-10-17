import argparse
import json
import os
import random

import pymongo
from backd.db import db
from backd.entities import Oracle
from backd.protocols.compound import constants
from backd.utils.logger import logger
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput
from web3.providers.auto import load_provider_from_uri

GET_UNDERLYING_PRICE_ABI = {
    "constant": True,
    "inputs": [{"name": "cToken", "type": "address"}],
    "name": "getUnderlyingPrice",
    "outputs": [{"name": "", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}
CTOKENS = [Web3.toChecksumAddress(market["address"]) for market in constants.MARKETS]


WEB3_URI = os.environ.get("WEB3_PROVIDER_URI", "http://satoshi.doc.ic.ac.uk:8545")


DEFAULT_SAMPLES_COUNT = 50

web3 = Web3(provider=load_provider_from_uri(WEB3_URI))

first_block = list(
    db.events.find({"event": "NewComptroller"})
    .sort([("blockNumber", pymongo.ASCENDING)])
    .limit(1)
)[0]["blockNumber"]
last_block = list(
    db.events.find().sort([("blockNumber", pymongo.DESCENDING)]).limit(1)
)[0]["blockNumber"]


oracles = Oracle.registered()
# contract does not have getUnderlyingPrice
oracles.remove("0x02557a5e05defeffd4cae6d83ea3d173b272c904")
oracles = [web3.toChecksumAddress(address) for address in oracles]


def call_contract(address, block, asset):
    contract = web3.eth.contract(address=address, abi=[GET_UNDERLYING_PRICE_ABI])
    try:
        result = contract.functions.getUnderlyingPrice(asset).call(
            block_identifier=block
        )
        return int(result)
    except BadFunctionCallOutput:
        return None


def fetch_results(fout, samples_count):
    sample_blocks = sorted(random.sample(range(first_block, last_block), samples_count))

    for i, block in enumerate(sample_blocks):
        if i % 5 == 0:
            logger.info("progress: %s/%s", i, len(sample_blocks))
        prices = []
        for address in oracles:
            for asset in CTOKENS:
                result = call_contract(address, block, asset)
                if result:
                    price = {"address": address, "asset": asset, "price": result}
                    prices.append(price)
        row = {"block": block, "prices": prices}
        print(json.dumps(row), file=fout)


def main():
    parser = argparse.ArgumentParser(prog="fetch-sample-prices")
    parser.add_argument(
        "-n",
        "--sample-count",
        default=DEFAULT_SAMPLES_COUNT,
        help="number of blocks to sample",
    )
    parser.add_argument("-o", "--output", required=True, help="output JSON file")
    args = parser.parse_args()

    with open(args.output, "w") as f:
        fetch_results(f, args.sample_count)


if __name__ == "__main__":
    main()

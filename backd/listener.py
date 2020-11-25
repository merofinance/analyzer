import json
from glob import glob
from os import path

from web3.main import Web3

from backd.utils.normalizer import normalize_web3_event

from . import settings
from .db import db
from .fetcher.event_listener import EventListener


async def run(_args):
    abis_path = path.join(settings.PROJECT_ROOT, "data", "abis")
    web3 = Web3()
    contracts = []
    for abi_path in glob(path.join(abis_path, "*.json")):
        with open(abi_path) as f:
            abi = json.load(f)
        address = web3.toChecksumAddress(path.splitext(path.basename(abi_path))[0])
        contracts.append(web3.eth.contract(address=address, abi=abi))  # type: ignore

    async with EventListener() as event_listener:
        await event_listener.listen_contracts_logs(contracts)
        async for event in event_listener.stream_events():
            db.events.insert_one(normalize_web3_event(event))

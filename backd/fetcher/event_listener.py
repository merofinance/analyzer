from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

import websockets
from eth_tools.event_fetcher import ContractFetcher
from eth_typing import BlockNumber
from hexbytes import HexBytes
from web3.contract import Contract
from web3.types import LogReceipt

from .. import settings
from ..utils.logger import logger


def normalize_event(raw_event: dict) -> LogReceipt:
    topics = [HexBytes(v) for v in raw_event["topics"]]
    return LogReceipt(
        address=raw_event["address"],
        blockHash=HexBytes(raw_event["blockHash"]),
        blockNumber=BlockNumber(int(raw_event["blockNumber"], 16)),
        data=raw_event["data"],
        logIndex=int(raw_event["logIndex"], 16),
        payload=HexBytes(raw_event.get("payload", "")),
        removed=raw_event["removed"],
        topic=topics[0],
        topics=topics,
        transactionHash=HexBytes(raw_event["transactionHash"]),
        transactionIndex=int(raw_event["transactionIndex"], 16),
    )


class EventListener:
    def __init__(self, endpoint: str = settings.INFURA_WS_ENDPOINT):
        self.endpoint = endpoint
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.contract_fetchers: Dict[str, ContractFetcher] = {}
        self._listened: Dict[str, Contract] = {}
        self._running = False

    async def __aenter__(self) -> EventListener:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        self._running = False
        await self.websocket.close()

    async def connect(self):
        self._running = True
        self.websocket = await websockets.connect(self.endpoint)

    async def _send_request(self, method: str, params: List[Any] = None):
        if params is None:
            params = []
        request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        await self.websocket.send(json.dumps(request))

    async def listen_contracts_logs(self, contracts: List[Contract]):
        addresses = []
        for contract in contracts:
            if contract.address in self._listened:
                continue
            addresses.append(contract.address)
            self._listened[contract.address] = contract
            self.contract_fetchers[contract.address] = ContractFetcher(contract)
        options: Dict[str, Any] = {"address": addresses}
        await self._send_request("eth_subscribe", ["logs", options])

    async def stream_events(self):
        while self._running:
            try:
                result = await asyncio.wait_for(self.websocket.recv(), 1)
                parsed = json.loads(result)
                if event := parsed.get("params", {}).get("result"):
                    fetcher = self.contract_fetchers.get(event["address"])
                    if fetcher:
                        yield fetcher.process_log(normalize_event(event))
            except asyncio.TimeoutError:
                continue
            except websockets.ConnectionClosedError as ex:
                logger.warning("disconnected: %s, trying to reconnect", ex)
                await self.connect()

    def stop(self):
        self._running = False

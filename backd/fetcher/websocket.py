import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any, List

import websockets

from ..protocols.compound import constants


class EventListener:
    def __init__(self, websocket: websockets.WebSocketClientProtocol):
        self.websocket = websocket
        self._running = True

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

    async def listen_address_logs(self, addresses: List[str]):
        await self._send_request("eth_subscribe", ["logs", {"address": addresses}])

    async def stream_events(self):
        while self._running:
            try:
                result = await asyncio.wait_for(self.websocket.recv(), 1)
                parsed = json.loads(result)
                event = parsed["params"]["result"]
                yield event
            except asyncio.TimeoutError:
                continue

    def stop(self):
        self._running = False

    @classmethod
    @asynccontextmanager
    async def create(cls, endpoint: str):
        websocket = await websockets.connect(endpoint)
        try:
            yield EventListener(websocket)
        finally:
            await websocket.close()

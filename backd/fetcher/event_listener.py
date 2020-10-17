import asyncio
import json
from typing import Any, List

import websockets

from .. import settings
from ..utils.logger import logger


class EventListener:
    def __init__(self, endpoint: str = settings.INFURA_WS_ENDPOINT):
        self.endpoint = endpoint
        self.websocket: websockets.WebSocketClientProtocol = None
        self._running = False

    async def __aenter__(self):
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
            except websockets.ConnectionClosedError as ex:
                logger.warning("disconnected: %s, trying to reconnect", ex)
                await self.connect()

    def stop(self):
        self._running = False

"""
Binance C2C Chat WebSocket Handler
Connects using listenKey + token from chat credentials endpoint.
"""
import asyncio
import json
import logging
from typing import Callable, Optional
import websockets

logger = logging.getLogger(__name__)

C2C_WS_BASE = "wss://ws.binance.com/c2c/chat"


class BinanceChatWebSocket:
    def __init__(self, listen_key: str, token: str, on_message: Callable):
        self.listen_key = listen_key
        self.token = token
        self.on_message = on_message
        self._ws = None
        self._running = False

    async def connect(self):
        uri = f"{C2C_WS_BASE}?listenKey={self.listen_key}&token={self.token}"
        self._running = True
        try:
            async with websockets.connect(uri, ping_interval=30, ping_timeout=10) as ws:
                self._ws = ws
                logger.info("Binance C2C Chat WebSocket connected")
                async for raw_msg in ws:
                    if not self._running:
                        break
                    try:
                        data = json.loads(raw_msg)
                        await self.on_message(data)
                    except Exception as e:
                        logger.error(f"Chat WS message error: {e}")
        except Exception as e:
            logger.error(f"Chat WebSocket disconnected: {e}")
            self._ws = None

    async def send(self, payload: dict):
        if self._ws:
            await self._ws.send(json.dumps(payload))

    def stop(self):
        self._running = False

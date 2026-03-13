"""
Binance C2C/SAPI Merchant Client
Handles signed requests per Binance API documentation.
"""
import hashlib
import hmac
import time
from typing import Optional, Any
import httpx


BINANCE_BASE_URL = "https://api.binance.com"
C2C_BASE_URL = "https://c2c.binance.com"


class BinanceClient:
    def __init__(self, api_key: str, secret_key: str, account_id: str = "default"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.account_id = account_id

    def _sign(self, params: dict) -> str:
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _get_headers(self) -> dict:
        return {
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/json",
        }

    def _build_signed_params(self, extra: dict) -> dict:
        params = {"timestamp": int(time.time() * 1000), **extra}
        params["signature"] = self._sign(params)
        return params

    async def _get(self, url: str, params: dict = None, signed: bool = True) -> Any:
        async with httpx.AsyncClient(timeout=30) as client:
            if signed:
                params = self._build_signed_params(params or {})
            response = await client.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def _post(self, url: str, payload: dict = None, signed: bool = True) -> Any:
        async with httpx.AsyncClient(timeout=30) as client:
            data = payload or {}
            query_params = {}
            if signed:
                ts = int(time.time() * 1000)
                # Signature covers timestamp + all payload fields (query-string format)
                sign_parts = {"timestamp": ts, **data}
                query_string = "&".join([f"{k}={v}" for k, v in sign_parts.items()])
                sig = hmac.new(
                    self.secret_key.encode("utf-8"),
                    query_string.encode("utf-8"),
                    hashlib.sha256,
                ).hexdigest()
                query_params = {"timestamp": ts, "signature": sig}
            response = await client.post(
                url,
                params=query_params,
                json=data,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    # -------------------------------------------------------------------------
    # Orders
    # -------------------------------------------------------------------------

    async def get_open_orders(self, page: int = 1, rows: int = 15) -> dict:
        """Fetch active P2P C2C orders."""
        url = f"{C2C_BASE_URL}/bapi/c2c/v2/private/c2c/order-match/order-list"
        return await self._post(url, {"page": page, "rows": rows, "orderStatusList": "1,2,3"})

    async def get_order_detail(self, order_id: str) -> dict:
        url = f"{C2C_BASE_URL}/bapi/c2c/v2/private/c2c/order-match/get-order-info"
        return await self._post(url, {"orderNo": order_id})

    async def get_order_history(self, trade_type: str = "BUY", page: int = 1, rows: int = 20) -> dict:
        url = f"{C2C_BASE_URL}/bapi/c2c/v2/private/c2c/order-match/order-list"
        return await self._post(url, {
            "page": page,
            "rows": rows,
            "orderStatusList": "4,5",
            "tradeType": trade_type,
        })

    async def release_order(self, order_id: str) -> dict:
        """Release / confirm payment for a P2P order."""
        url = f"{C2C_BASE_URL}/bapi/c2c/v2/private/c2c/order-match/release-confirm"
        return await self._post(url, {"orderNo": order_id})

    # -------------------------------------------------------------------------
    # Chat
    # -------------------------------------------------------------------------

    async def get_chat_credentials(self) -> dict:
        """Get listenKey + token for C2C WebSocket chat."""
        url = f"{C2C_BASE_URL}/bapi/c2c/v2/private/c2c/chat/retrieve-credential"
        return await self._post(url, {})

    async def get_chat_messages(self, order_id: str) -> dict:
        url = f"{C2C_BASE_URL}/bapi/c2c/v2/private/c2c/chat/get-messages"
        return await self._post(url, {"orderNo": order_id})

    async def send_chat_message(self, order_id: str, message: str) -> dict:
        url = f"{C2C_BASE_URL}/bapi/c2c/v2/private/c2c/chat/send-message"
        return await self._post(url, {"orderNo": order_id, "message": message, "msgType": "TEXT"})


async def get_binance_client_from_db() -> Optional[BinanceClient]:
    """Build a BinanceClient from secrets stored in MongoDB."""
    from app.services.secrets_service import get_secret
    api_key = await get_secret("BINANCE_API_KEY")
    secret_key = await get_secret("BINANCE_SECRET_KEY")
    if not api_key or not secret_key:
        return None
    return BinanceClient(api_key=api_key, secret_key=secret_key)

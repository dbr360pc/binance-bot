"""
Binance C2C/SAPI Merchant Client

NOTE: c2c.binance.com/bapi/... endpoints are internal web APIs that use
browser-session cookie authentication, NOT API-key + HMAC signing.
Store the full Cookie header string from a logged-in Binance browser
session as the BINANCE_COOKIES secret.

How to get cookies:
  1. Log into https://www.binance.com in Chrome/Firefox
  2. Open DevTools → Network → reload any page
  3. Click any request to binance.com → Headers → Request Headers
  4. Copy the entire Cookie: ... value
  5. Paste it into the BINANCE_COOKIES secret in the app
"""
import logging
import re
from typing import Optional, Any
import httpx

logger = logging.getLogger(__name__)

C2C_BASE_URL = "https://c2c.binance.com"


class BinanceClient:
    def __init__(self, cookies: str, account_id: str = "default"):
        """
        :param cookies: Raw Cookie header string copied from a logged-in
                        Binance browser session, e.g.
                        "csrftoken=abc; BNC-Location=xxx; p20t=yyy; ..."
        """
        self.cookies = cookies
        self.account_id = account_id
        # Extract csrftoken for the Csrftoken header Binance requires
        m = re.search(r'(?:^|;\s*)csrftoken=([^;]+)', cookies)
        self.csrf_token = m.group(1) if m else ""

    def _get_headers(self) -> dict:
        return {
            "Cookie": self.cookies,
            "Csrftoken": self.csrf_token,
            "Content-Type": "application/json",
            "clienttype": "web",
            "lang": "en-US",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }

    async def _post(self, url: str, payload: dict = None) -> Any:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                json=payload or {},
                headers=self._get_headers(),
            )
            self._raise_for_status(response)
            return response.json()

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        """Raise an error that includes the Binance JSON body for easier debugging."""
        if response.is_error:
            try:
                body = response.json()
            except Exception:
                body = response.text
            logger.error("Binance API error %s %s – body: %s", response.status_code, response.url, body)
            raise httpx.HTTPStatusError(
                f"Binance {response.status_code}: {body}",
                request=response.request,
                response=response,
            )

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
    cookies = await get_secret("BINANCE_COOKIES")
    if not cookies:
        return None
    return BinanceClient(cookies=cookies)

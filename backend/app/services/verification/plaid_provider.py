"""
Plaid verification provider.
Checks bank transactions to confirm payment for a P2P order.
Compatible with plaid-python >= 8.x (new API style).
"""
import json
from datetime import datetime, timedelta
from typing import Optional
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

from app.services.verification.base_provider import VerificationResult


def build_plaid_client(client_id: str, secret: str, env: str = "sandbox") -> plaid_api.PlaidApi:
    env_map = {
        "sandbox": plaid.Environment.Sandbox,
        "production": plaid.Environment.Production,
    }
    config = plaid.Configuration(
        host=env_map.get(env, plaid.Environment.Sandbox),
        api_key={"clientId": client_id, "secret": secret},
    )
    api_client = plaid.ApiClient(config)
    return plaid_api.PlaidApi(api_client)


class PlaidProvider:
    name = "plaid"

    def __init__(self, client_id: str, secret: str, env: str = "sandbox"):
        self.client = build_plaid_client(client_id, secret, env)

    async def create_link_token(self, user_id: str) -> str:
        request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="Binance P2P Bot",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            webhook="https://your-server.com/api/plaid/webhook",
        )
        response = self.client.link_token_create(request)
        return response["link_token"]

    async def exchange_public_token(self, public_token: str) -> dict:
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        return {"access_token": response["access_token"], "item_id": response["item_id"]}

    async def sync_transactions(self, access_token: str, cursor: Optional[str] = None) -> dict:
        request = TransactionsSyncRequest(access_token=access_token)
        if cursor:
            request.cursor = cursor
        response = self.client.transactions_sync(request)
        return {
            "added": [t.to_dict() for t in response["added"]],
            "modified": [t.to_dict() for t in response["modified"]],
            "removed": response["removed"],
            "next_cursor": response["next_cursor"],
            "has_more": response["has_more"],
        }

    async def verify(
        self,
        order_id: str,
        expected_amount: float,
        access_token: str,
        cursor: Optional[str] = None,
        counterparty_name: Optional[str] = None,
        created_time: Optional[datetime] = None,
        time_window_hours: int = 24,
    ) -> VerificationResult:
        try:
            sync_data = await self.sync_transactions(access_token, cursor)
            transactions = sync_data["added"] + sync_data["modified"]

            window_start = (created_time or datetime.utcnow()) - timedelta(hours=time_window_hours)
            window_end = datetime.utcnow()

            matching = []
            for txn in transactions:
                txn_date = txn.get("date")
                txn_amount = abs(txn.get("amount", 0))
                txn_name = txn.get("name", "").lower()

                if txn_date and not isinstance(txn_date, datetime):
                    # plaid returns date objects
                    import datetime as dt
                    txn_datetime = dt.datetime.combine(txn_date, dt.time.min)
                else:
                    txn_datetime = txn_date or datetime.utcnow()

                amount_ok = abs(txn_amount - expected_amount) < 0.01
                time_ok = window_start <= txn_datetime <= window_end
                name_ok = True
                if counterparty_name:
                    name_ok = any(
                        part.lower() in txn_name
                        for part in counterparty_name.lower().split()
                        if len(part) > 2
                    )

                if amount_ok and time_ok:
                    matching.append({"txn": txn, "name_ok": name_ok})

            if not matching:
                return VerificationResult(
                    passed=False,
                    provider=self.name,
                    detail=f"No matching transaction found for amount {expected_amount} within time window.",
                    raw={"transactions_checked": len(transactions)},
                )

            best = matching[0]
            if counterparty_name and not best["name_ok"]:
                return VerificationResult(
                    passed=False,
                    provider=self.name,
                    detail=f"Amount matched but counterparty name '{counterparty_name}' did not match transaction.",
                    raw=best["txn"],
                )

            return VerificationResult(
                passed=True,
                provider=self.name,
                detail="Payment verified via Plaid. Amount, name, and time window checks passed.",
                raw=best["txn"],
            )
        except Exception as e:
            return VerificationResult(
                passed=False,
                provider=self.name,
                detail=f"Plaid verification error: {str(e)}",
            )

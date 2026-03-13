from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.utils.jwt import get_current_user
from app.models.models import PlaidItem
from app.services.secrets_service import get_secret
from app.utils.crypto import encrypt, decrypt

router = APIRouter(prefix="/api/plaid", tags=["plaid"])


async def get_plaid_provider():
    from app.services.verification.plaid_provider import PlaidProvider
    client_id = await get_secret("PLAID_CLIENT_ID")
    secret_sandbox = await get_secret("PLAID_SECRET_SANDBOX")
    if not client_id or not secret_sandbox:
        raise HTTPException(status_code=503, detail="Plaid credentials not configured")
    return PlaidProvider(client_id=client_id, secret=secret_sandbox, env="sandbox")


class ExchangeTokenRequest(BaseModel):
    public_token: str
    institution_name: Optional[str] = None
    institution_id: Optional[str] = None


class WebhookRequest(BaseModel):
    webhook_type: str
    webhook_code: str
    item_id: Optional[str] = None
    error: Optional[dict] = None


@router.get("/link-token")
async def create_link_token(current_user: dict = Depends(get_current_user)):
    provider = await get_plaid_provider()
    link_token = await provider.create_link_token(current_user["sub"])
    return {"link_token": link_token}


@router.post("/exchange-token")
async def exchange_token(
    req: ExchangeTokenRequest,
    current_user: dict = Depends(get_current_user),
):
    provider = await get_plaid_provider()
    data = await provider.exchange_public_token(req.public_token)

    item = PlaidItem(
        access_token=encrypt(data["access_token"]),
        item_id=data["item_id"],
        institution_name=req.institution_name,
        institution_id=req.institution_id,
    )
    await item.insert()
    return {"item_id": item.item_id, "institution_name": item.institution_name}


@router.get("/items")
async def list_items(current_user: dict = Depends(get_current_user)):
    items = await PlaidItem.find(PlaidItem.is_active == True).to_list()
    return {
        "items": [
            {
                "id": str(i.id),
                "item_id": i.item_id,
                "institution_name": i.institution_name,
                "is_active": i.is_active,
                "last_synced_at": i.last_synced_at.isoformat() if i.last_synced_at else None,
                "created_at": i.created_at.isoformat(),
            }
            for i in items
        ]
    }


@router.post("/items/{item_id}/sync")
async def sync_item(item_id: str, current_user: dict = Depends(get_current_user)):
    item = await PlaidItem.find_one(PlaidItem.item_id == item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Plaid item not found")

    provider = await get_plaid_provider()
    data = await provider.sync_transactions(decrypt(item.access_token), cursor=item.cursor)

    item.cursor = data["next_cursor"]
    item.last_synced_at = datetime.utcnow()
    await item.save()

    return {
        "added": len(data["added"]),
        "modified": len(data["modified"]),
        "has_more": data["has_more"],
        "cursor": data["next_cursor"],
    }


@router.delete("/items/{item_id}")
async def deactivate_item(item_id: str, current_user: dict = Depends(get_current_user)):
    item = await PlaidItem.find_one(PlaidItem.item_id == item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Plaid item not found")
    item.is_active = False
    await item.save()
    return {"detail": "Item deactivated"}


@router.post("/webhook")
async def plaid_webhook(req: WebhookRequest):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Plaid webhook: type={req.webhook_type} code={req.webhook_code} item={req.item_id}")

    if req.webhook_type == "TRANSACTIONS" and req.webhook_code == "SYNC_UPDATES_AVAILABLE":
        if req.item_id:
            item = await PlaidItem.find_one(PlaidItem.item_id == req.item_id)
            if item:
                provider = await get_plaid_provider()
                data = await provider.sync_transactions(decrypt(item.access_token), item.cursor)
                item.cursor = data["next_cursor"]
                item.last_synced_at = datetime.utcnow()
                await item.save()

    return {"received": True}

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.utils.jwt import get_current_user
from app.services.secrets_service import get_secret, set_secret, list_secrets, KNOWN_SECRETS

router = APIRouter(prefix="/api/secrets", tags=["secrets"])


class SecretSetRequest(BaseModel):
    key: str
    value: str


@router.get("/")
async def get_secrets_list(current_user: dict = Depends(get_current_user)):
    return {"secrets": await list_secrets()}


@router.post("/")
async def upsert_secret(
    req: SecretSetRequest,
    current_user: dict = Depends(get_current_user),
):
    if req.key not in KNOWN_SECRETS:
        raise HTTPException(status_code=400, detail=f"Unknown secret key: {req.key}")
    if not req.value.strip():
        raise HTTPException(status_code=400, detail="Secret value cannot be empty")
    await set_secret(req.key, req.value.strip())

    from app.models.models import AdminLog
    await AdminLog(
        username=current_user.get("username", "unknown"),
        action="secret_updated",
        detail=f"Secret '{req.key}' was updated",
    ).insert()

    return {"detail": f"Secret '{req.key}' saved successfully"}

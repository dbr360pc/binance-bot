from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.utils.jwt import get_current_user
from app.models.models import Order
from app.services.release_service import execute_release, ReleaseError

router = APIRouter(prefix="/api/release", tags=["release"])


class ReleaseRequest(BaseModel):
    order_id: str           # binance_order_id
    confirmed: bool = False  # must be True (second confirmation from UI)


@router.post("/")
async def release_order(
    req: ReleaseRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Release requires confirmed=true (second confirmation)")

    order = await Order.find_one(Order.binance_order_id == req.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found locally. Sync orders first.")

    ip = request.client.host if request.client else ""
    username = current_user.get("username", "unknown")

    try:
        data = await execute_release(order, released_by=username, ip_address=ip)
        return data
    except ReleaseError as e:
        raise HTTPException(status_code=400, detail=str(e))

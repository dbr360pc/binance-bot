import json
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from app.utils.jwt import get_current_user
from app.models.models import Order, OrderStatus, AppSettings, VerificationMode
from app.services.binance_client import get_binance_client_from_db
from app.services.release_service import execute_release, get_app_settings, ReleaseError

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _map_binance_status(binance_status: str, verification_mode: VerificationMode) -> OrderStatus:
    if binance_status in ("4", "COMPLETED"):
        return OrderStatus.RELEASED
    if verification_mode == VerificationMode.MANUAL_REVIEW:
        return OrderStatus.MANUAL_REVIEW
    return OrderStatus.CHECKING_PAYMENT


@router.get("/")
async def list_orders(
    page: int = Query(1, ge=1),
    rows: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    binance = await get_binance_client_from_db()
    if not binance:
        raise HTTPException(status_code=503, detail="Binance credentials not configured")

    app_settings = await get_app_settings()
    raw = await binance.get_open_orders(page=page, rows=rows)
    orders_data = raw.get("data", {}).get("orderList", [])

    result = []
    for o in orders_data:
        order_id = str(o.get("orderNo") or o.get("orderId"))

        db_order = await Order.find_one(Order.binance_order_id == order_id)
        if not db_order:
            db_order = Order(
                binance_order_id=order_id,
                asset=o.get("asset"),
                trade_side=o.get("tradeType"),
                amount=o.get("amount"),
                fiat_currency=o.get("fiat"),
                fiat_amount=o.get("totalPrice"),
                price=o.get("unitPrice"),
                payment_method=o.get("payType"),
                counterparty_name=o.get("buyerName") or o.get("sellerName"),
                counterparty_id=o.get("buyerUserId") or o.get("sellerUserId"),
                created_time=datetime.fromtimestamp(o["createTime"] / 1000) if o.get("createTime") else None,
                raw_data=o,
            )
            await db_order.insert()
        else:
            db_order.raw_data = o
            if db_order.order_status != OrderStatus.RELEASED:
                db_order.order_status = _map_binance_status(
                    str(o.get("orderStatus", "")), app_settings.verification_mode
                )
            db_order.updated_at = datetime.utcnow()
            await db_order.save()

        result.append({
            "id": str(db_order.id),
            "binance_order_id": db_order.binance_order_id,
            "asset": db_order.asset,
            "trade_side": db_order.trade_side,
            "amount": db_order.amount,
            "fiat_currency": db_order.fiat_currency,
            "fiat_amount": db_order.fiat_amount,
            "price": db_order.price,
            "payment_method": db_order.payment_method,
            "counterparty_name": db_order.counterparty_name,
            "created_time": db_order.created_time.isoformat() if db_order.created_time else None,
            "order_status": db_order.order_status.value,
            "released_at": db_order.released_at.isoformat() if db_order.released_at else None,
            "released_by": db_order.released_by,
        })

    return {"orders": result, "total": len(result)}


@router.get("/history")
async def order_history(
    trade_type: str = Query("BUY"),
    page: int = Query(1, ge=1),
    rows: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    binance = await get_binance_client_from_db()
    if not binance:
        raise HTTPException(status_code=503, detail="Binance credentials not configured")
    return await binance.get_order_history(trade_type=trade_type, page=page, rows=rows)


@router.get("/{order_id}")
async def order_detail(
    order_id: str,
    current_user: dict = Depends(get_current_user),
):
    binance = await get_binance_client_from_db()
    if not binance:
        raise HTTPException(status_code=503, detail="Binance credentials not configured")
    raw = await binance.get_order_detail(order_id)

    db_order = await Order.find_one(Order.binance_order_id == order_id)
    return {
        "binance_data": raw,
        "local_order": {
            "order_status": db_order.order_status.value if db_order else None,
            "released_at": db_order.released_at.isoformat() if db_order and db_order.released_at else None,
            "released_by": db_order.released_by if db_order else None,
        },
    }

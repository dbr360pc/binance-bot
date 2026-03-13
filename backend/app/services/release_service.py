"""
Central release service.
Enforces all release logic rules from the spec.
"""
from datetime import datetime
from typing import Optional

from app.models.models import (
    Order, OrderStatus, ReleaseLog, AppSettings,
    VerificationMode, ReleaseMode,
)
from app.services.binance_client import get_binance_client_from_db


class ReleaseError(Exception):
    pass


async def get_app_settings() -> AppSettings:
    settings = await AppSettings.find_one(AppSettings.singleton_key == "default")
    if settings is None:
        settings = AppSettings()
        await settings.insert()
    return settings


async def can_release(order: Order, app_settings: AppSettings) -> tuple[bool, str]:
    if app_settings.kill_switch:
        return False, "Emergency kill switch is active."

    if order.order_status == OrderStatus.RELEASED:
        return False, "Order is already released."

    vm = app_settings.verification_mode
    rm = app_settings.release_mode

    if vm == VerificationMode.MANUAL_REVIEW and rm == ReleaseMode.AUTO:
        return False, "Auto Release is not allowed without an active verification provider."

    if vm == VerificationMode.PLAID and rm == ReleaseMode.AUTO:
        if order.order_status != OrderStatus.SAFE_TO_RELEASE:
            return False, "Auto Release requires payment to be verified (Safe to Release)."

    return True, "OK"


async def execute_release(
    order: Order,
    released_by: str,
    ip_address: Optional[str] = None,
) -> dict:
    app_settings = await get_app_settings()
    can, reason = await can_release(order, app_settings)
    if not can:
        raise ReleaseError(reason)

    binance = await get_binance_client_from_db()
    if not binance:
        raise ReleaseError("Binance API credentials are not configured.")

    result = await binance.release_order(order.binance_order_id)

    success = result.get("code") == "000000" or result.get("status") == "SUCCESS"
    detail = str(result)

    if success:
        order.order_status = OrderStatus.RELEASED
        order.released_at = datetime.utcnow()
        order.released_by = released_by
        await order.save()

    log = ReleaseLog(
        order_id=str(order.id),
        binance_order_id=order.binance_order_id,
        released_by=released_by,
        verification_mode=app_settings.verification_mode.value,
        release_mode=app_settings.release_mode.value,
        success=success,
        detail=detail,
        ip_address=ip_address,
    )
    await log.insert()

    if not success:
        raise ReleaseError(f"Binance release failed: {result}")

    return {"success": True, "order_id": order.binance_order_id, "detail": result}

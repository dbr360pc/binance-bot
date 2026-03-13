from fastapi import APIRouter, Depends, Query

from app.utils.jwt import get_current_user
from app.models.models import AdminLog, ReleaseLog

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/admin")
async def admin_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    logs = await AdminLog.find().sort(-AdminLog.created_at).limit(limit).to_list()
    return {
        "logs": [
            {
                "id": str(l.id),
                "username": l.username,
                "action": l.action,
                "detail": l.detail,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]
    }


@router.get("/releases")
async def release_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    logs = await ReleaseLog.find().sort(-ReleaseLog.created_at).limit(limit).to_list()
    return {
        "logs": [
            {
                "id": str(l.id),
                "binance_order_id": l.binance_order_id,
                "released_by": l.released_by,
                "verification_mode": l.verification_mode,
                "release_mode": l.release_mode,
                "success": l.success,
                "detail": l.detail,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]
    }

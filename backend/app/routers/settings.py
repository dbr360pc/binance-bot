from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.utils.jwt import get_current_user
from app.models.models import AppSettings, AdminLog, VerificationMode, ReleaseMode
from app.services.release_service import get_app_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class UpdateSettingsRequest(BaseModel):
    verification_mode: Optional[str] = None   # "manual_review" | "plaid"
    release_mode: Optional[str] = None        # "manual" | "auto"
    ai_auto_reply: Optional[bool] = None
    kill_switch: Optional[bool] = None
    ai_system_prompt: Optional[str] = None


@router.get("/")
async def get_settings(current_user: dict = Depends(get_current_user)):
    app_settings = await get_app_settings()
    return {
        "verification_mode": app_settings.verification_mode.value,
        "release_mode": app_settings.release_mode.value,
        "ai_auto_reply": app_settings.ai_auto_reply,
        "kill_switch": app_settings.kill_switch,
        "ai_system_prompt": app_settings.ai_system_prompt,
    }


@router.patch("/")
async def update_settings(
    req: UpdateSettingsRequest,
    current_user: dict = Depends(get_current_user),
):
    app_settings = await get_app_settings()

    if req.verification_mode is not None:
        try:
            app_settings.verification_mode = VerificationMode(req.verification_mode)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid verification_mode: {req.verification_mode}")

    if req.release_mode is not None:
        try:
            new_rm = ReleaseMode(req.release_mode)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid release_mode: {req.release_mode}")

        # Enforce: Manual Review + Auto Release is NOT allowed
        vm = app_settings.verification_mode
        if vm == VerificationMode.MANUAL_REVIEW and new_rm == ReleaseMode.AUTO:
            raise HTTPException(
                status_code=400,
                detail="Auto Release is not allowed when Verification Mode is Manual Review. Enable Plaid first."
            )
        app_settings.release_mode = new_rm

    if req.ai_auto_reply is not None:
        app_settings.ai_auto_reply = req.ai_auto_reply

    if req.kill_switch is not None:
        app_settings.kill_switch = req.kill_switch

    if req.ai_system_prompt is not None:
        app_settings.ai_system_prompt = req.ai_system_prompt

    await app_settings.save()

    await AdminLog(
        username=current_user.get("username", "unknown"),
        action="settings_updated",
        detail=str(req.model_dump(exclude_none=True)),
    ).insert()

    return {"detail": "Settings updated", "settings": {
        "verification_mode": app_settings.verification_mode.value,
        "release_mode": app_settings.release_mode.value,
        "ai_auto_reply": app_settings.ai_auto_reply,
        "kill_switch": app_settings.kill_switch,
    }}

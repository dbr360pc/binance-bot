from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.utils.jwt import get_current_user
from app.models.models import ChatLog, AppSettings
from app.services.binance_client import get_binance_client_from_db
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class SendMessageRequest(BaseModel):
    order_id: str
    message: str


@router.get("/{order_id}/messages")
async def get_messages(
    order_id: str,
    current_user: dict = Depends(get_current_user),
):
    binance = await get_binance_client_from_db()
    if not binance:
        raise HTTPException(status_code=503, detail="Binance credentials not configured")
    raw = await binance.get_chat_messages(order_id)

    local_logs = await ChatLog.find(
        ChatLog.binance_order_id == order_id
    ).sort(+ChatLog.created_at).to_list()

    return {
        "binance_messages": raw,
        "local_logs": [
            {
                "id": str(l.id),
                "direction": l.direction,
                "content": l.content,
                "sender": l.sender,
                "is_ai_generated": l.is_ai_generated,
                "created_at": l.created_at.isoformat(),
            }
            for l in local_logs
        ],
    }


@router.post("/send")
async def send_message(
    req: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    binance = await get_binance_client_from_db()
    if not binance:
        raise HTTPException(status_code=503, detail="Binance credentials not configured")

    result = await binance.send_chat_message(req.order_id, req.message)

    log = ChatLog(
        binance_order_id=req.order_id,
        direction="out",
        content=req.message,
        sender=current_user.get("username"),
        is_ai_generated=False,
    )
    await log.insert()

    return {"detail": "Message sent", "binance_result": result}


@router.post("/ai-reply")
async def ai_reply(
    req: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    app_settings = await AppSettings.find_one(AppSettings.singleton_key == "default")
    if not app_settings or not app_settings.ai_auto_reply:
        raise HTTPException(status_code=400, detail="AI auto-reply is disabled")

    ai_service = await get_ai_service()
    if not ai_service:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    reply = await ai_service.generate_reply([], req.message)

    binance = await get_binance_client_from_db()
    if binance:
        await binance.send_chat_message(req.order_id, reply)

    log = ChatLog(
        binance_order_id=req.order_id,
        direction="out",
        content=reply,
        sender="ai",
        is_ai_generated=True,
    )
    await log.insert()

    return {"reply": reply}

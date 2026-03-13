from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import get_settings

settings = get_settings()

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
    return _client


async def init_db():
    """Initialize Beanie with all document models."""
    from app.models.models import (
        User, Order, VerificationResult, PlaidItem,
        ChatLog, ReleaseLog, AdminLog, EncryptedSetting, AppSettings,
    )
    client = get_client()
    await init_beanie(
        database=client[settings.MONGODB_DB],
        document_models=[
            User, Order, VerificationResult, PlaidItem,
            ChatLog, ReleaseLog, AdminLog, EncryptedSetting, AppSettings,
        ],
    )


# Dependency shim kept for router compatibility
async def get_db():
    """No-op dependency — Beanie manages its own connection."""
    yield None

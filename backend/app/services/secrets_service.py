from app.models.models import EncryptedSetting
from app.utils.crypto import encrypt, decrypt
from typing import Optional


KNOWN_SECRETS = [
    "BINANCE_API_KEY",
    "BINANCE_SECRET_KEY",
    "PLAID_CLIENT_ID",
    "PLAID_SECRET_SANDBOX",
    "PLAID_SECRET_PRODUCTION",
    "OPENAI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
]


async def get_secret(key: str) -> Optional[str]:
    setting = await EncryptedSetting.find_one(EncryptedSetting.key == key)
    if setting is None:
        return None
    return decrypt(setting.encrypted_value)


async def set_secret(key: str, value: str) -> None:
    encrypted = encrypt(value)
    setting = await EncryptedSetting.find_one(EncryptedSetting.key == key)
    if setting:
        setting.encrypted_value = encrypted
        await setting.save()
    else:
        await EncryptedSetting(key=key, encrypted_value=encrypted).insert()


async def list_secrets() -> list[dict]:
    """Return list of known secrets with masked values."""
    stored = await EncryptedSetting.find().to_list()
    stored_keys = {s.key for s in stored}

    return [
        {"key": key, "is_set": key in stored_keys, "masked": "••••••••" if key in stored_keys else ""}
        for key in KNOWN_SECRETS
    ]

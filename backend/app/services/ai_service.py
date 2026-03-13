"""
AI service for generating chat replies via OpenAI.
"""
from typing import Optional
from openai import AsyncOpenAI


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful Binance P2P merchant assistant. "
    "Respond concisely and professionally to buyer queries. "
    "Never share API keys, internal details, or sensitive information."
)


class AIService:
    def __init__(self, api_key: str, system_prompt: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    async def generate_reply(self, conversation_history: list[dict], user_message: str) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in conversation_history[-10:]:  # last 10 messages for context
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()


async def get_ai_service() -> Optional[AIService]:
    from app.services.secrets_service import get_secret
    from app.models.models import AppSettings

    api_key = await get_secret("OPENAI_API_KEY")
    if not api_key:
        return None

    app_settings = await AppSettings.find_one(AppSettings.singleton_key == "default")
    prompt = app_settings.ai_system_prompt if app_settings else None

    return AIService(api_key=api_key, system_prompt=prompt)

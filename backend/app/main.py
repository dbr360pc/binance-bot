from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.routers import auth, orders, chat, plaid, release, secrets, settings, logs

settings_config = get_settings()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Binance P2P Operations Bot",
    description="Internal dashboard for Binance P2P order management",
    version="1.0.0",
    docs_url="/docs" if settings_config.APP_ENV == "development" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
origins = [o.strip() for o in settings_config.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(chat.router)
app.include_router(plaid.router)
app.include_router(release.router)
app.include_router(secrets.router)
app.include_router(settings.router)
app.include_router(logs.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    from app.database import init_db
    await init_db()

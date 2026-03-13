from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
import bcrypt

from app.models.models import User, AdminLog
from app.utils.jwt import create_access_token, get_current_user
from app.utils.totp import generate_totp_secret, get_totp_uri, generate_qr_code_base64, verify_totp
from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


class LoginRequest(BaseModel):
    username: str
    password: str


class TOTPVerifyRequest(BaseModel):
    temp_token: str
    totp_code: str


class TOTPSetupRequest(BaseModel):
    totp_code: str


async def log_admin_action(username: str, action: str, detail: str = "", ip: str = ""):
    log = AdminLog(username=username, action=action, detail=detail, ip_address=ip)
    await log.insert()


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    user = await User.find_one(User.username == req.username)

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    ip = request.client.host if request.client else ""

    if user.totp_enabled and user.totp_secret:
        temp_token = create_access_token(
            {"sub": str(user.id), "username": user.username, "totp_pending": True},
            expires_delta=timedelta(minutes=5),
        )
        return {"totp_required": True, "temp_token": temp_token}

    access_token = create_access_token({"sub": str(user.id), "username": user.username})
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = ip
    await user.save()
    await log_admin_action(user.username, "login", "Successful login", ip)
    return {"access_token": access_token, "token_type": "bearer", "totp_required": False}


@router.post("/totp/verify")
async def verify_totp_login(req: TOTPVerifyRequest, request: Request):
    from app.utils.jwt import decode_token
    payload = decode_token(req.temp_token)
    if not payload.get("totp_pending"):
        raise HTTPException(status_code=400, detail="Invalid token type")

    user = await User.get(payload.get("sub"))
    if not user or not user.totp_secret:
        raise HTTPException(status_code=400, detail="User not found or TOTP not set")

    if not verify_totp(user.totp_secret, req.totp_code):
        raise HTTPException(status_code=401, detail="Invalid TOTP code")

    access_token = create_access_token({"sub": str(user.id), "username": user.username})
    ip = request.client.host if request.client else ""
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = ip
    await user.save()
    await log_admin_action(user.username, "login", "TOTP login successful", ip)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/totp/setup")
async def totp_setup(current_user: dict = Depends(get_current_user)):
    user = await User.get(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    secret = generate_totp_secret()
    user.totp_secret = secret
    await user.save()

    uri = get_totp_uri(secret, user.username)
    qr = generate_qr_code_base64(uri)
    return {"secret": secret, "uri": uri, "qr_code": qr}


@router.post("/totp/enable")
async def totp_enable(req: TOTPSetupRequest, current_user: dict = Depends(get_current_user)):
    user = await User.get(current_user["sub"])
    if not user or not user.totp_secret:
        raise HTTPException(status_code=400, detail="Run /totp/setup first")

    if not verify_totp(user.totp_secret, req.totp_code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    user.totp_enabled = True
    await user.save()
    await log_admin_action(user.username, "totp_enabled", "TOTP MFA enabled")
    return {"detail": "TOTP enabled successfully"}


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user.get("username"), "id": current_user.get("sub")}


class CreateUserRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(req: CreateUserRequest):
    existing = await User.find_one()
    if existing:
        raise HTTPException(status_code=403, detail="Registration is closed. Contact admin.")

    hashed = hash_password(req.password)
    user = User(username=req.username, hashed_password=hashed)
    await user.insert()
    return {"detail": "Admin user created. Please set up TOTP."}

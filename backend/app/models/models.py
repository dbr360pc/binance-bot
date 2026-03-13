import enum
from datetime import datetime
from typing import Annotated, Optional, Any
from beanie import Document, Indexed
from pydantic import Field


class VerificationMode(str, enum.Enum):
    MANUAL_REVIEW = "manual_review"
    PLAID = "plaid"


class ReleaseMode(str, enum.Enum):
    MANUAL = "manual"
    AUTO = "auto"


class OrderStatus(str, enum.Enum):
    MANUAL_REVIEW = "manual_review"
    CHECKING_PAYMENT = "checking_payment"
    PAYMENT_NOT_CONFIRMED = "payment_not_confirmed"
    SAFE_TO_RELEASE = "safe_to_release"
    RELEASED = "released"


class User(Document):
    username: Annotated[str, Indexed(unique=True)]
    hashed_password: str
    totp_secret: Optional[str] = None
    totp_enabled: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None

    class Settings:
        name = "users"


class Order(Document):
    binance_order_id: Annotated[str, Indexed(unique=True)]
    asset: Optional[str] = None
    trade_side: Optional[str] = None
    amount: Optional[float] = None
    fiat_currency: Optional[str] = None
    fiat_amount: Optional[float] = None
    price: Optional[float] = None
    payment_method: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_id: Optional[str] = None
    created_time: Optional[datetime] = None
    order_status: OrderStatus = OrderStatus.MANUAL_REVIEW
    verification_status: Optional[str] = None
    released_at: Optional[datetime] = None
    released_by: Optional[str] = None
    binance_account_id: Optional[str] = None  # multi-account ready
    raw_data: Optional[dict] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "orders"


class VerificationResult(Document):
    order_id: str  # Order document id string
    provider: str  # "plaid" | "manual"
    passed: Optional[bool] = None
    detail: Optional[str] = None
    raw: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "verification_results"


class PlaidItem(Document):
    access_token: str          # encrypted
    item_id: Annotated[str, Indexed(unique=True)]
    institution_name: Optional[str] = None
    institution_id: Optional[str] = None
    cursor: Optional[str] = None
    is_active: bool = True
    last_synced_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "plaid_items"


class ChatLog(Document):
    binance_order_id: Annotated[str, Indexed()]
    direction: str              # "in" | "out"
    content: str
    sender: Optional[str] = None
    is_ai_generated: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chat_logs"


class ReleaseLog(Document):
    order_id: str               # Order document id string
    binance_order_id: str
    released_by: str
    verification_mode: str
    release_mode: str
    success: bool
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "release_logs"


class AdminLog(Document):
    username: str
    action: str
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "admin_logs"


class EncryptedSetting(Document):
    key: Annotated[str, Indexed(unique=True)]
    encrypted_value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "encrypted_settings"


class AppSettings(Document):
    singleton_key: Annotated[str, Indexed(unique=True)] = "default"
    verification_mode: VerificationMode = VerificationMode.MANUAL_REVIEW
    release_mode: ReleaseMode = ReleaseMode.MANUAL
    ai_auto_reply: bool = False
    kill_switch: bool = False
    ai_system_prompt: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "app_settings"

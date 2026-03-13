# Binance P2P Operations Bot

Internal dashboard for Binance P2P order management with AI chat, Plaid verification, and secure release workflows.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + SQLAlchemy (async) + PostgreSQL |
| Frontend | React 18 + Vite + Tailwind CSS |
| Auth | JWT + bcrypt + TOTP (Google Authenticator) |
| Verification | Plaid (bank transactions) |
| AI Chat | OpenAI GPT-4o-mini |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis (for rate limiting)

---

### 1. Backend Setup

```bash
cd backend

# Create venv
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, and ENCRYPTION_KEY

# Generate ENCRYPTION_KEY:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Run migrations (auto-creates tables on startup)
uvicorn app.main:app --reload --port 8000
```

### 2. First Run — Create Admin User

```
POST http://localhost:8000/api/auth/register
{ "username": "admin", "password": "your-strong-password" }
```

Only works if NO users exist yet.

### 3. Enable TOTP MFA

```
GET /api/auth/totp/setup      (with Bearer token)
-> scan QR code in Google Authenticator

POST /api/auth/totp/enable
{ "totp_code": "123456" }
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## Entering Secrets

After logging in, go to **Integrations** page and enter:
- Binance API Key + Secret Key
- Plaid Client ID + Sandbox/Production secrets
- OpenAI API Key
- Telegram Bot Token + Chat ID

Secrets are **encrypted at rest** with Fernet and never shown in plain text after saving.

---

## Core Mode Rules

| Verification Mode | Release Mode | Allowed? |
|---|---|---|
| Manual Review | Manual Release | ✅ |
| Plaid | Manual Release | ✅ |
| Plaid | Auto Release | ✅ |
| Manual Review | Auto Release | ❌ BLOCKED |

---

## Order Status Flow

```
Manual Review  →  (enable Plaid)  →  Checking Payment
                                         ↓            ↓
                                  Safe to Release   Not Confirmed
                                         ↓
                                      Released
```

---

## Project Structure

```
binance-paul-app/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routers/             # API routes
│   │   │   ├── auth.py          # Login, TOTP, register
│   │   │   ├── orders.py        # Order list/detail
│   │   │   ├── chat.py          # Chat read/send/AI-reply
│   │   │   ├── plaid.py         # Plaid flow + webhooks
│   │   │   ├── release.py       # Release with confirmation
│   │   │   ├── secrets.py       # Encrypted secrets CRUD
│   │   │   ├── settings.py      # Mode controls
│   │   │   └── logs.py          # Admin + release audit logs
│   │   ├── services/
│   │   │   ├── binance_client.py  # Signed Binance requests
│   │   │   ├── binance_chat.py    # WebSocket chat handler
│   │   │   ├── ai_service.py      # OpenAI chat
│   │   │   ├── release_service.py # Central release logic
│   │   │   ├── secrets_service.py # Encrypt/decrypt secrets
│   │   │   └── verification/
│   │   │       ├── base_provider.py
│   │   │       ├── manual_provider.py
│   │   │       └── plaid_provider.py
│   │   └── utils/
│   │       ├── crypto.py        # Fernet encryption
│   │       ├── jwt.py           # JWT encode/decode
│   │       └── totp.py          # TOTP generation/verify
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/               # Login, MFA, Orders, Banks, Settings, Secrets, Logs
        ├── components/          # Layout, StatusBadge, ConfirmModal, ChatPanel
        ├── api/                 # Axios API clients
        └── context/             # AuthContext
```

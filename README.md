# Trading Journal + Analytics Platform

A production-ready full-stack web application for trading journal and analytics with MT5 integration.

## 📋 Project Overview

This is a **complete, production-ready system** for traders to:
- Track and analyze trading performance
- Connect MT5 accounts with automatic trade synchronization
- Maintain detailed trading journals with notes, tags, and screenshots
- View comprehensive analytics (win rate, profit factor, expectancy, etc.)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT TIER                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Next.js Frontend (React + TypeScript + Tailwind)  │   │
│  │  - Authentication Pages                             │   │
│  │  - Dashboard & Analytics                            │   │
│  │  - Trade Management                                 │   │
│  │  - Journal & Tagging                               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTPS/REST
┌─────────────────────────────────────────────────────────────┐
│                       APPLICATION TIER                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FastAPI Backend (Python)                          │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │ Auth Routes │  │ Trade Routes │  │ MT5 API  │ │   │
│  │  └─────────────┘  └──────────────┘  └──────────┘ │   │
│  │  ┌──────────────────────────────────────────────┐ │   │
│  │  │  Services Layer                              │ │   │
│  │  │  - AuthService (JWT + Refresh Tokens)        │ │   │
│  │  │  - MT5Service (Secure Connection & Sync)     │ │   │
│  │  │  - TradeService (CRUD + Analytics)           │ │   │
│  │  │  - JournalService (Notes + Tags)             │ │   │
│  │  └──────────────────────────────────────────────┘ │   │
│  │  ┌──────────────────────────────────────────────┐ │   │
│  │  │  Middleware                                  │ │   │
│  │  │  - JWT Verification                          │ │   │
│  │  │  - Rate Limiting                             │ │   │
│  │  │  - CORS                                      │ │   │
│  │  └──────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕ SQL
┌─────────────────────────────────────────────────────────────┐
│                         DATA TIER                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PostgreSQL Database                                │   │
│  │  - users                                            │   │
│  │  - refresh_tokens                                   │   │
│  │  - mt5_accounts (encrypted credentials)            │   │
│  │  - trades                                           │   │
│  │  - journal_entries                                  │   │
│  │  - trade_tags                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Redis (Optional)                                   │   │
│  │  - Session caching                                  │   │
│  │  - Rate limiting                                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Security Architecture

### Authentication Flow
```
1. User Registration
   → Email + password validated
   → Password hashed (bcrypt)
   → User created in DB
   
2. User Login
   → Credentials verified
   → Access token (JWT, 15min expiry) generated
   → Refresh token (JWT, 7day expiry) generated
   → Refresh token stored in DB + HttpOnly cookie
   → Access token returned to client
   
3. API Request
   → Client sends access token in Authorization header
   → Backend validates JWT signature
   → User loaded from token payload
   → Request processed
   
4. Token Refresh
   → Access token expired
   → Client sends refresh token
   → Backend validates refresh token in DB
   → New access token generated
   → Client retries original request
   
5. Logout
   → Refresh token revoked in DB
   → Cookie cleared
```

### Security Features
- ✅ Password hashing with bcrypt
- ✅ JWT access + refresh tokens
- ✅ Token rotation and revocation
- ✅ HttpOnly cookies (CSRF protection)
- ✅ Rate limiting (SlowAPI)
- ✅ CORS with whitelist
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ XSS protection (React escaping)
- ✅ Encrypted MT5 credentials (Fernet)

## 🔌 MT5 Integration Flow

```
1. Add MT5 Account
   → User provides: account number, password, broker, server
   → Password encrypted (Fernet) before storage
   → Test connection performed
   → Account metadata saved
   
2. Sync Trades
   → MT5Service connects to account
   → Password decrypted
   → MT5 login performed
   → Trade history retrieved (mt5.history_deals_get)
   → Deals processed into trades
   → New trades saved to database
   → Account sync timestamp updated
   
3. Security
   → Passwords NEVER stored in plain text
   → Encryption key stored in environment variable
   → Read-only access only
   → Connection closed after each operation
```

## 📊 Database Schema

### users
```
id (PK)              : Integer
email                : String (unique, indexed)
hashed_password      : String
is_active            : Boolean
is_verified          : Boolean
role                 : Enum (user, admin)
full_name            : String (nullable)
profile_image_url    : String (nullable)
created_at           : DateTime
updated_at           : DateTime
last_login_at        : DateTime (nullable)
```

### refresh_tokens
```
id (PK)              : Integer
token                : String (unique, indexed)
user_id (FK)         : Integer → users.id
is_revoked           : Boolean
expires_at           : DateTime
user_agent           : String (nullable)
ip_address           : String (nullable)
created_at           : DateTime
revoked_at           : DateTime (nullable)
```

### mt5_accounts
```
id (PK)              : Integer
user_id (FK)         : Integer → users.id
account_number       : String (indexed)
account_name         : String (nullable)
broker_name          : String
server_name          : String
encrypted_password   : Text
is_active            : Boolean
is_connected         : Boolean
last_sync_at         : DateTime (nullable)
last_connection_error: Text (nullable)
account_currency     : String (nullable)
account_leverage     : Integer (nullable)
account_balance      : String (nullable)
created_at           : DateTime
updated_at           : DateTime
```

### trades
```
id (PK)              : Integer
user_id (FK)         : Integer → users.id
mt5_account_id (FK)  : Integer → mt5_accounts.id (nullable)
mt5_ticket           : String (nullable, indexed)
trade_source         : Enum (mt5_auto, manual)
symbol               : String (indexed)
trade_type           : Enum (buy, sell)
volume               : Float
open_price           : Float
close_price          : Float (nullable)
stop_loss            : Float (nullable)
take_profit          : Float (nullable)
open_time            : DateTime (indexed)
close_time           : DateTime (nullable)
profit               : Float (nullable)
commission           : Float
swap                 : Float
net_profit           : Float (nullable)
is_closed            : Boolean
created_at           : DateTime
updated_at           : DateTime
```

### journal_entries
```
id (PK)              : Integer
user_id (FK)         : Integer → users.id
trade_id (FK)        : Integer → trades.id (unique)
title                : String (nullable)
notes                : Text (nullable)
pre_trade_analysis   : Text (nullable)
post_trade_analysis  : Text (nullable)
emotional_state      : String (nullable)
mistakes             : Text (nullable)
lessons_learned      : Text (nullable)
screenshot_urls      : Text (nullable, JSON array)
created_at           : DateTime
updated_at           : DateTime
```

### trade_tags
```
id (PK)              : Integer
user_id (FK)         : Integer → users.id
name                 : String (indexed)
color                : String (nullable, hex code)
category             : String (nullable)
created_at           : DateTime
```

### trade_tag_associations (junction table)
```
trade_id (PK, FK)    : Integer → trades.id
tag_id (PK, FK)      : Integer → trade_tags.id
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.109
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Authentication**: python-jose (JWT), passlib (bcrypt)
- **Encryption**: cryptography (Fernet)
- **MT5**: MetaTrader5 5.0.45
- **Rate Limiting**: SlowAPI
- **Validation**: Pydantic 2.5

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS 3.4
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Forms**: React Hook Form + Zod

## 📡 API Endpoints

### Authentication
```
POST   /api/auth/register         - Register new user
POST   /api/auth/login            - Login user
POST   /api/auth/refresh          - Refresh access token
POST   /api/auth/logout           - Logout (revoke token)
POST   /api/auth/logout-all       - Logout all devices
GET    /api/auth/me               - Get current user
```

### MT5 Accounts
```
POST   /api/mt5/accounts          - Add MT5 account
GET    /api/mt5/accounts          - Get all accounts
POST   /api/mt5/accounts/{id}/sync- Sync trades
DELETE /api/mt5/accounts/{id}     - Delete account
```

### Trades
```
POST   /api/trades                - Create manual trade
GET    /api/trades                - Get trades (with filters)
GET    /api/trades/{id}           - Get specific trade
PATCH  /api/trades/{id}           - Update trade
DELETE /api/trades/{id}           - Delete trade
GET    /api/trades/analytics/summary - Get analytics
```

### Journal
```
POST   /api/journal/entries/{trade_id}       - Create/update journal entry
GET    /api/journal/entries/{trade_id}       - Get journal entry
POST   /api/journal/tags                     - Create tag
GET    /api/journal/tags                     - Get all tags
POST   /api/journal/trades/{tid}/tags/{tagid}- Add tag to trade
DELETE /api/journal/trades/{tid}/tags/{tagid}- Remove tag from trade
```

## 🚀 Deployment

### Backend Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with production values

# Run migrations (if using Alembic)
alembic upgrade head

# Run with Gunicorn (production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Frontend Deployment

```bash
# Install dependencies
npm install

# Build
npm run build

# Run production server
npm start
```

### Environment Variables

**Backend (.env)**:
```
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=<generate with: openssl rand -hex 32>
ENCRYPTION_KEY=<generate with: openssl rand -hex 32>
REDIS_URL=redis://localhost:6379/0
ALLOWED_ORIGINS=https://yourdomain.com
```

**Frontend (.env.local)**:
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## 📈 Analytics Metrics

- **Total Trades**: Count of all closed trades
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / Gross loss
- **Expectancy**: Average profit per trade
- **Average Win/Loss**: Mean profit/loss amounts
- **Largest Win/Loss**: Peak profit/loss values
- **Equity Curve**: Cumulative P&L over time
- **Drawdown**: Peak-to-trough decline

## 🔒 Security Checklist

- [x] Passwords hashed (bcrypt)
- [x] JWT tokens with expiry
- [x] Refresh token rotation
- [x] HttpOnly cookies
- [x] CORS configured
- [x] Rate limiting
- [x] SQL injection protection (ORM)
- [x] XSS protection (React)
- [x] CSRF protection (SameSite cookies)
- [x] Encrypted sensitive data (MT5 credentials)
- [x] Environment variables for secrets
- [x] Input validation (Pydantic)
- [x] HTTPS in production (recommended)

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional)
- MT5 Terminal (for testing)

### Quick Start

```bash
# 1. Clone repository
git clone <repo-url>
cd trading-journal

# 2. Setup backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env
alembic upgrade head
uvicorn app.main:app --reload

# 3. Setup frontend
cd ../frontend
npm install
cp .env.local.example .env.local
# Edit .env.local
npm run dev
```

Visit http://localhost:3000

## 🛣️ Roadmap

### Phase 1 (MVP) ✅
- User authentication
- MT5 integration
- Trade management
- Basic analytics
- Trading journal

### Phase 2 (Future)
- [ ] Email verification
- [ ] Password reset
- [ ] Advanced charting (candlesticks)
- [ ] Trade backtesting
- [ ] Strategy templates
- [ ] Export reports (PDF)
- [ ] Mobile app (React Native)
- [ ] Multi-broker support (cTrader, etc.)
- [ ] Social trading (share strategies)
- [ ] AI-powered insights

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📧 Support

For issues or questions, please open a GitHub issue.

---

**Built with ❤️ for traders by traders**

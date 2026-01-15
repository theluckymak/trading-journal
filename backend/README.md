# Trading Journal Backend

Production-ready FastAPI backend for trading journal and analytics platform with MT5 integration.

## Features

- **Authentication**: JWT-based auth with access/refresh tokens, HttpOnly cookies
- **MT5 Integration**: Secure connection to MT5 accounts with encrypted credential storage
- **Trade Management**: Manual and automatic trade import
- **Journal System**: Detailed trade journaling with tags, notes, and screenshots
- **Analytics**: Win rate, profit factor, expectancy, equity curves

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
```

Update the following in `.env`:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `ENCRYPTION_KEY`: Generate with `openssl rand -hex 32`
- `REDIS_URL`: Redis connection string
- `ALLOWED_ORIGINS`: Frontend URLs

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb trading_journal

# Run migrations (if using Alembic)
alembic upgrade head
```

### 4. Run Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Project Structure

```
backend/
├── app/
│   ├── models/          # SQLAlchemy database models
│   ├── routes/          # API route handlers
│   ├── services/        # Business logic services
│   ├── middleware/      # Auth and other middleware
│   ├── config.py        # Configuration management
│   ├── database.py      # Database connection
│   ├── schemas.py       # Pydantic schemas
│   └── main.py          # FastAPI application
├── requirements.txt     # Python dependencies
└── .env.example        # Environment variables template
```

## Security Features

- Password hashing with bcrypt
- JWT access + refresh tokens
- Token rotation and revocation
- Encrypted MT5 credentials (Fernet)
- HttpOnly cookies
- Rate limiting
- CORS protection
- SQL injection protection (SQLAlchemy ORM)

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout (revoke token)
- `POST /api/auth/logout-all` - Logout all devices
- `GET /api/auth/me` - Get current user

### MT5 Accounts
- `POST /api/mt5/accounts` - Add MT5 account
- `GET /api/mt5/accounts` - Get all accounts
- `POST /api/mt5/accounts/{id}/sync` - Sync trades
- `DELETE /api/mt5/accounts/{id}` - Delete account

### Trades
- `POST /api/trades` - Create manual trade
- `GET /api/trades` - Get all trades (with filters)
- `GET /api/trades/{id}` - Get specific trade
- `PATCH /api/trades/{id}` - Update trade
- `DELETE /api/trades/{id}` - Delete trade
- `GET /api/trades/analytics/summary` - Get analytics

### Journal
- `POST /api/journal/entries/{trade_id}` - Create/update journal entry
- `GET /api/journal/entries/{trade_id}` - Get journal entry
- `POST /api/journal/tags` - Create tag
- `GET /api/journal/tags` - Get all tags
- `POST /api/journal/trades/{trade_id}/tags/{tag_id}` - Add tag to trade
- `DELETE /api/journal/trades/{trade_id}/tags/{tag_id}` - Remove tag

## License

MIT

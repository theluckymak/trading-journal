# MakTrades

My personal trading journal. Built this because I was tired of spreadsheets and wanted something that actually helps me track my trades properly.

Live at [maktrades.app](https://maktrades.app)

## What it does

- **Dashboard** — quick overview of performance: win rate, P&L, recent trades, calendar
- **Trade tracking** — manual entry or auto-import from MT5
- **Journal** — notes, pre/post analysis, emotional state, mistakes, lessons per trade
- **Analytics** — charts for equity curve, win rate over time, P&L by symbol/day
- **Calendar** — visual daily P&L view (like Tradezilla)
- **AI Predictions** — DRL ensemble model (PPO/A2C/SAC) with 5-day directional outlook, real-time news, and entry signals
- **Dark/Light mode** — Telegram-style theme

## Stack

**Frontend:** Next.js, TypeScript, Tailwind CSS, Recharts

**Backend:** FastAPI (Python), PostgreSQL, Redis, SQLAlchemy

**AI:** Stable-Baselines3 (PPO, A2C, SAC), HMM regime detection, yfinance for market data

**Infra:** Docker Compose, Nginx (reverse proxy + SSL), Let's Encrypt

## Running locally

You need Docker installed.

```bash
git clone https://github.com/theluckymak/trading-journal.git
cd trading-journal
cp .env.example .env
# edit .env — at minimum change SECRET_KEY and POSTGRES_PASSWORD
docker-compose up -d
```

Then open:
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

## Production deploy

Using `docker-compose.production.yml`. Basic steps:

```bash
# on your VPS
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh

git clone https://github.com/theluckymak/trading-journal.git
cd trading-journal
cp .env.example .env
nano .env  # set real values

docker compose -f docker-compose.production.yml up -d --build
```

For HTTPS, I use Let's Encrypt with certbot:
```bash
apt install certbot -y
certbot certonly --standalone -d yourdomain.com
```

The nginx config in `nginx/nginx.conf` handles SSL termination and proxying.

## Project structure

```
backend/
  app/            # FastAPI app, routes, models, services
  ai/             # DRL prediction models, training scripts
  alembic/        # DB migrations
frontend/
  src/pages/      # Next.js pages
  src/components/ # Reusable components
  src/lib/        # API client, utilities
  src/contexts/   # Auth context
nginx/            # Nginx config
models/           # Trained model files (not in git)
```

## Key env variables

| Variable | What it does |
|----------|-------------|
| `SECRET_KEY` | JWT signing key — change this |
| `DATABASE_URL` | Postgres connection string |
| `REDIS_URL` | Redis connection string |
| `CORS_ORIGINS` | Allowed frontend origins |
| `SMTP_*` | Email config for verification emails |
| `RESEND_API_KEY` | Resend.com for transactional email |

## API routes

```
POST /api/auth/register, /login, /refresh, /logout
GET  /api/auth/me

POST /api/trades
GET  /api/trades, /api/trades/{id}
PATCH/DELETE /api/trades/{id}

GET  /api/analytics

POST /api/mt5/accounts
POST /api/mt5/accounts/{id}/sync

GET  /api/ai/drl-predict/{symbol}
GET  /api/ai/news/{symbol}
GET  /api/ai/events
```


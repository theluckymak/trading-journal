# Trading Journal

A comprehensive trading journal application for tracking trades, analyzing performance, and maintaining trading discipline.

## Features

- 📊 **Dashboard** - Overview of your trading performance with key metrics
- 💼 **Trade Management** - Add, edit, and track your trades across multiple instruments (Forex, Futures, Crypto)
- 📝 **Journal Entries** - Document your trading thoughts, lessons learned, and trading psychology
- 📈 **Analytics** - Advanced analytics with interactive charts and performance metrics
- 📅 **Calendar View** - Tradezilla-style calendar showing daily P&L, trades, and R:R ratios
- 🌙 **Dark Mode** - Full dark mode support with theme persistence
- 🔐 **Authentication** - Secure JWT-based authentication with OAuth support (Google, GitHub)
- 📱 **Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices

## Tech Stack

### Backend
- **FastAPI** - Modern, fast Python web framework
- **PostgreSQL** - Robust relational database
- **Redis** - Caching and session management
- **SQLAlchemy** - SQL toolkit and ORM
- **Alembic** - Database migrations
- **JWT** - Token-based authentication

### Frontend
- **Next.js 14** - React framework with SSR
- **TypeScript** - Type-safe JavaScript
- **TailwindCSS** - Utility-first CSS framework
- **Recharts** - Charting library for React
- **Lucide Icons** - Beautiful icon set

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy and load balancing

## Quick Start (Development)

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
### Prerequisites
- Docker and Docker Compose installed
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trading-journal.git
cd trading-journal
```

2. Copy the environment file:
```bash
cp .env.example .env
```

3. Update the `.env` file with your configuration (at minimum, change SECRET_KEY and passwords)

4. Start the application:
```bash
docker-compose up -d
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

6. Create an admin user:
```bash
docker exec -it trading-journal-backend python create_admin.py
```

## Production Deployment (DigitalOcean)

### Prerequisites
- DigitalOcean Droplet (Ubuntu 22.04 LTS recommended, minimum 2GB RAM)
- Domain name (optional, for HTTPS)
- SSH access to your droplet

### Step 1: Prepare the Droplet

SSH into your droplet:
```bash
ssh root@your_droplet_ip
```

Update system packages:
```bash
apt update && apt upgrade -y
```

Install Docker:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

Install Docker Compose:
```bash
apt install docker-compose -y
```

### Step 2: Clone and Configure

Clone the repository:
```bash
cd /opt
git clone https://github.com/yourusername/trading-journal.git
cd trading-journal
```

Copy and configure environment:
```bash
cp .env.example .env
nano .env
```

**Important:** Update these values in `.env`:
- `SECRET_KEY` - Generate a strong random key
- `POSTGRES_PASSWORD` - Use a strong password
- `POSTGRES_USER` - Change from default
- `NEXT_PUBLIC_API_URL` - Set to your domain or IP (e.g., `http://your-domain.com` or `http://your_ip`)
- `CORS_ORIGINS` - Add your domain/IP

### Step 3: Deploy

Build and start containers:
```bash
docker-compose -f docker-compose.production.yml up -d --build
```

Run database migrations:
```bash
docker exec -it trading-journal-backend-prod alembic upgrade head
```

Create admin user:
```bash
docker exec -it trading-journal-backend-prod python create_admin.py
```

### Step 4: Configure Firewall

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Step 5: Setup HTTPS (Optional but Recommended)

Install Certbot:
```bash
apt install certbot python3-certbot-nginx -y
```

Obtain SSL certificate:
```bash
certbot --nginx -d your-domain.com
```

Update `nginx/nginx.conf` to uncomment the HTTPS server block and update with your domain.

Restart Nginx:
```bash
docker-compose -f docker-compose.production.yml restart nginx
```

### Step 6: Setup Automatic Backups

Create backup script:
```bash
nano /opt/backup-trading-journal.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker exec trading-journal-db-prod pg_dump -U trading_user trading_journal > $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
```

Make executable:
```bash
chmod +x /opt/backup-trading-journal.sh
```

Add to crontab (daily at 2 AM):
```bash
crontab -e
# Add this line:
0 2 * * * /opt/backup-trading-journal.sh
```

## Monitoring and Maintenance

### View logs:
```bash
docker-compose -f docker-compose.production.yml logs -f
```

### Restart services:
```bash
docker-compose -f docker-compose.production.yml restart
```

### Update application:
```bash
cd /opt/trading-journal
git pull
docker-compose -f docker-compose.production.yml up -d --build
```

### Check container status:
```bash
docker-compose -f docker-compose.production.yml ps
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | postgresql://trading_user:password@db:5432/trading_journal |
| `REDIS_URL` | Redis connection string | redis://redis:6379/0 |
| `SECRET_KEY` | JWT secret key | **Must change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token expiry | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token expiry | 30 |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost:3000 |
| `NEXT_PUBLIC_API_URL` | Frontend API URL | http://localhost:8000 |

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://your-domain/docs`
- ReDoc: `http://your-domain/redoc`

## Database Schema

The application uses the following main models:
- **Users** - User accounts with authentication
- **Trades** - Individual trade records
- **Journal Entries** - Trade journal notes
- **Chat Messages** - AI chat conversations

## Supported Trading Instruments

- **Forex**: EUR/USD, GBP/USD, USD/JPY, etc.
- **Futures**: NQ (Nasdaq), ES (S&P 500), YM (Dow), GC (Gold), CL (Crude Oil)
- **Crypto**: BTC/USD, ETH/USD, and other major pairs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation at `/docs`

## Acknowledgments

- Inspired by Tradezilla trading journal
- Built with modern web technologies
- Designed for traders, by traders
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
git clone https://github.com/theluckymak/trading-journal.git
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

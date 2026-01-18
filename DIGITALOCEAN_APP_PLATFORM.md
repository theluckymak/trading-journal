# DigitalOcean App Platform Deployment

## Prerequisites
- GitHub account with your repository
- DigitalOcean account

## Deployment Steps

### 1. Prepare Repository

Your repository already has the App Platform spec file at `.do/app.yaml`.

### 2. Create App on DigitalOcean

1. Go to https://cloud.digitalocean.com/apps
2. Click **"Create App"**
3. Select **GitHub** as the source
4. Authorize DigitalOcean to access your GitHub
5. Select repository: `theluckymak/trading-journal`
6. Select branch: `main`
7. Click **"Next"**

### 3. Configure Resources

DigitalOcean should auto-detect the `.do/app.yaml` file and configure:
- **Backend Service** (FastAPI)
- **Frontend Service** (Next.js)
- **PostgreSQL Database**

If not auto-detected, manually add:

#### Backend Service
- **Name**: backend
- **Source Directory**: `/backend`
- **Dockerfile Path**: `backend/Dockerfile`
- **HTTP Port**: 8000
- **HTTP Routes**: `/api`, `/docs`, `/redoc`, `/health`

#### Frontend Service
- **Name**: frontend
- **Source Directory**: `/frontend`
- **Dockerfile Path**: `frontend/Dockerfile`
- **HTTP Port**: 3000
- **HTTP Routes**: `/`

#### Database
- **Type**: PostgreSQL
- **Name**: db
- **Version**: 15

### 4. Configure Environment Variables

Add these environment variables to the **Backend** service:

| Key | Value | Type |
|-----|-------|------|
| `SECRET_KEY` | Generate with `openssl rand -hex 32` | Secret |
| `DATABASE_URL` | Auto-populated from database | System |
| `ALGORITHM` | HS256 | Plain Text |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Plain Text |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 30 | Plain Text |
| `CORS_ORIGINS` | ${APP_URL} | System Variable |
| `ENVIRONMENT` | production | Plain Text |

Add these to the **Frontend** service:

| Key | Value | Type |
|-----|-------|------|
| `NEXT_PUBLIC_API_URL` | ${APP_URL} | System Variable |
| `NEXT_PUBLIC_API_URL_SERVER` | http://backend:8000 | Plain Text |

### 5. Configure Info

- **App Name**: trading-journal
- **Region**: Choose closest to your users (e.g., New York, San Francisco, Amsterdam)

### 6. Review and Deploy

1. Review all settings
2. Click **"Create Resources"**
3. Wait 5-10 minutes for deployment

### 7. Post-Deployment Setup

Once deployed, you need to run database migrations and create an admin user.

#### Option A: Using App Platform Console

1. Go to your app in DigitalOcean dashboard
2. Click on **backend** service
3. Click **"Console"** tab
4. Run:
```bash
# Run migrations
alembic upgrade head

# Create admin user
python create_admin.py
```

#### Option B: Using doctl CLI

Install doctl:
```bash
# macOS
brew install doctl

# Windows
choco install doctl

# Linux
snap install doctl
```

Authenticate:
```bash
doctl auth init
```

Run commands:
```bash
# Get app ID
doctl apps list

# Get backend component ID
doctl apps spec get YOUR_APP_ID

# Run migration
doctl apps exec YOUR_APP_ID --component backend -- alembic upgrade head

# Create admin
doctl apps exec YOUR_APP_ID --component backend -- python create_admin.py
```

### 8. Access Your App

Your app will be available at:
```
https://trading-journal-xxxxx.ondigitalocean.app
```

The URL will be shown in the App Platform dashboard.

### 9. Setup Custom Domain (Optional)

1. Go to **Settings** > **Domains**
2. Click **"Add Domain"**
3. Enter your domain name
4. Add the provided DNS records to your domain registrar:
   - Type: CNAME
   - Name: @ (or subdomain)
   - Value: provided by DigitalOcean

SSL certificate will be automatically provisioned.

## Pricing

### Basic Setup (Recommended for Starting)
- **Backend**: Basic XXS ($5/month)
- **Frontend**: Basic XXS ($5/month)
- **Database**: Basic ($7/month)
- **Total**: ~$17/month

### Professional Setup
- **Backend**: Basic XS ($10/month)
- **Frontend**: Basic XS ($10/month)
- **Database**: Professional ($15/month)
- **Total**: ~$35/month

## Monitoring

### View Logs
1. Go to your app dashboard
2. Click on service (backend or frontend)
3. Click **"Runtime Logs"** tab

### View Metrics
1. Click **"Insights"** tab
2. View CPU, Memory, and Request metrics

### Alerts
1. Go to **Settings** > **Alerts**
2. Configure alerts for:
   - High error rate
   - High response time
   - Component down

## Scaling

### Horizontal Scaling
1. Go to service settings
2. Increase **Instance Count**
3. Click **"Update"**

### Vertical Scaling
1. Go to service settings
2. Change **Instance Size** (XXS → XS → S → M)
3. Click **"Update"**

## Troubleshooting

### Build Failed
- Check build logs in the dashboard
- Verify Dockerfile paths are correct
- Ensure all dependencies are in requirements.txt/package.json

### Backend Not Starting
- Check runtime logs
- Verify DATABASE_URL is set
- Verify SECRET_KEY is set
- Check that migrations ran successfully

### Frontend Not Loading
- Verify NEXT_PUBLIC_API_URL is set correctly
- Check that backend is healthy
- Check CORS_ORIGINS includes frontend URL

### Database Connection Error
- Verify DATABASE_URL is correctly set
- Check database is running (green status)
- Try restarting backend service

### 502 Bad Gateway
- Check backend health endpoint: `/health`
- Verify HTTP port is 8000 for backend, 3000 for frontend
- Check routes are configured correctly

## CI/CD

Auto-deployment is enabled when you push to the `main` branch.

To disable:
1. Go to **Settings** > **App Spec**
2. Change `deploy_on_push: true` to `false`

## Rollback

To rollback to a previous deployment:
1. Go to **Activity** tab
2. Find successful deployment
3. Click **"Rollback to this deployment"**

## Database Backups

Backups are automatic for Professional database tier.

For Basic tier, setup manual backups:
1. Use doctl or API to create snapshots
2. Schedule via cron or GitHub Actions

## Alternative: Using Droplet Instead

If you prefer more control, use a Droplet instead:
- Follow the `DEPLOY.md` guide for Droplet deployment
- More control over configuration
- Can use Docker Compose
- Slightly more setup but more flexibility

## Support

- DigitalOcean Docs: https://docs.digitalocean.com/products/app-platform/
- Community: https://www.digitalocean.com/community/
- Support Tickets: https://cloud.digitalocean.com/support

---

**Recommendation**: For production use, I recommend using a **Droplet** (see `DEPLOY.md`) as it gives you more control and allows using the full Docker Compose setup with Nginx, Redis, etc. App Platform is simpler but has limitations for complex multi-service apps.

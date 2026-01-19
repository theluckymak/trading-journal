# Railway Deployment Guide

## Why Railway?
- ✅ **$5/month free credit** with GitHub Student
- ✅ **One-click deploy** from GitHub
- ✅ **Automatic HTTPS**
- ✅ **Built-in PostgreSQL**
- ✅ **Auto-deploys on git push**

## Prerequisites
1. GitHub Student Developer Pack activated
2. GitHub account with this repository
3. Railway account (sign up with GitHub)

## Step-by-Step Deployment

### 1. Get Railway Student Credit

1. Go to https://railway.app/github-student
2. Sign up/login with your GitHub account
3. Verify your GitHub Student status
4. Get **$5/month credit** (renews monthly while you're a student)

### 2. Create New Project

1. Go to https://railway.app/new
2. Click **"Deploy from GitHub repo"**
3. Select your `trading-journal` repository
4. Railway will detect your Docker setup

### 3. Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway automatically creates and connects the database
4. Copy the `DATABASE_URL` from the database variables

### 4. Configure Backend Service

1. Click on the **backend** service
2. Go to **"Variables"** tab
3. Add these environment variables:

```env
SECRET_KEY=your_secret_key_here_use_openssl_rand_hex_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
CORS_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}
```

4. Go to **"Settings"** tab:
   - **Root Directory**: `/backend`
   - **Build Command**: (leave default - uses Dockerfile)
   - **Start Command**: (leave default - uses Dockerfile CMD)
   - **Port**: `8000`

5. Click **"Deploy"**

### 5. Configure Frontend Service

1. Click on the **frontend** service
2. Go to **"Variables"** tab
3. Add these environment variables:

```env
NEXT_PUBLIC_API_URL=https://${RAILWAY_BACKEND_DOMAIN}
```

4. Go to **"Settings"** tab:
   - **Root Directory**: `/frontend`
   - **Build Command**: (leave default - uses Dockerfile)
   - **Start Command**: (leave default - uses Dockerfile CMD)
   - **Port**: `3000`

5. Click **"Deploy"**

### 6. Generate Public URLs

1. Click on **frontend** service
2. Go to **"Settings"** → **"Networking"**
3. Click **"Generate Domain"**
4. Copy the URL (e.g., `trading-journal-production.up.railway.app`)

5. Click on **backend** service
6. Go to **"Settings"** → **"Networking"**
7. Click **"Generate Domain"**
8. Copy the URL

### 7. Update Environment Variables

1. Go back to **backend** variables
2. Update `CORS_ORIGINS` with your frontend URL:
   ```
   https://trading-journal-production.up.railway.app
   ```

3. Go to **frontend** variables
4. Update `NEXT_PUBLIC_API_URL` with your backend URL:
   ```
   https://trading-journal-backend-production.up.railway.app
   ```

### 8. Run Database Migrations

1. Click on **backend** service
2. Click **"Deployments"** tab
3. Click on the latest deployment
4. Click **"View Logs"**
5. Once backend is running, go to **"Settings"** → **"Deploy"**
6. Add a **one-time command**:
   ```bash
   alembic upgrade head
   ```

### 9. Create Admin User

After migrations, run:
```bash
python create_admin.py
```

Or connect to Railway CLI and run:
```bash
railway run python create_admin.py
```

## Alternative: Deploy with Railway Template

You can also use Railway's template feature:

1. Create a `railway.json` in your project root
2. Push to GitHub
3. Click "Deploy on Railway" button

## Railway CLI (Optional)

Install Railway CLI for easier management:

```bash
# Install
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# View logs
railway logs

# Run commands
railway run python create_admin.py
```

## Cost Breakdown

With GitHub Student credit:
- **Database**: ~$2/month
- **Backend**: ~$1.50/month
- **Frontend**: ~$1.50/month
- **Total**: ~$5/month = **FREE** with student credit ✅

## Monitoring

Railway provides:
- Real-time logs
- Metrics (CPU, Memory, Network)
- Automatic SSL certificates
- Custom domains support

## Automatic Deployments

Every time you push to GitHub:
1. Railway detects the change
2. Rebuilds containers
3. Deploys automatically
4. Zero downtime deployment

## Troubleshooting

### Issue: Frontend can't connect to Backend
**Solution**: Make sure `NEXT_PUBLIC_API_URL` points to the backend's Railway domain

### Issue: Database connection fails
**Solution**: Use `${{Postgres.DATABASE_URL}}` variable reference, not hardcoded URL

### Issue: CORS errors
**Solution**: Add frontend domain to `CORS_ORIGINS` in backend variables

### Issue: Build fails
**Solution**: Check logs, ensure Docker files are correct and all dependencies listed

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: Create an issue in your repo

## Next Steps

1. Set up custom domain (optional)
2. Configure environment-specific settings
3. Set up monitoring/alerts
4. Add CI/CD improvements

---

**Your app will be live at**: `https://your-app.up.railway.app`

Happy trading! 📈

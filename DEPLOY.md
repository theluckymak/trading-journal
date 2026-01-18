# DigitalOcean Deployment Guide

## Quick Deployment Steps

### 1. Create a Droplet

1. Log into DigitalOcean
2. Create a new Droplet:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic - $12/month (2GB RAM, 1 vCPU, 50GB SSD)
   - **Datacenter**: Choose closest to your users
   - **Authentication**: SSH key (recommended) or Password
   - **Hostname**: trading-journal

### 2. Initial Server Setup

SSH into your droplet:
```bash
ssh root@YOUR_DROPLET_IP
```

Update system:
```bash
apt update && apt upgrade -y
```

Install Docker:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh
```

Install Docker Compose:
```bash
apt install docker-compose -y
```

Create application directory:
```bash
mkdir -p /opt
cd /opt
```

### 3. Clone and Configure

Clone repository:
```bash
git clone https://github.com/theluckymak/trading-journal.git
cd trading-journal
```

Create environment file:
```bash
cp .env.example .env
nano .env
```

**Required changes in `.env`:**
```env
# Generate a strong secret (use: openssl rand -hex 32)
SECRET_KEY=your_generated_secret_key_here

# Change default passwords
POSTGRES_PASSWORD=your_strong_db_password
POSTGRES_USER=trading_admin

# Set your domain or IP
NEXT_PUBLIC_API_URL=http://YOUR_DROPLET_IP
CORS_ORIGINS=http://YOUR_DROPLET_IP

# Production environment
ENVIRONMENT=production
```

Save and exit (Ctrl+X, Y, Enter)

### 4. Deploy Application

Build and start all services:
```bash
docker-compose -f docker-compose.production.yml up -d --build
```

This will take 5-10 minutes on first build.

Wait for containers to be healthy:
```bash
watch docker-compose -f docker-compose.production.yml ps
```

Run database migrations:
```bash
docker exec -it trading-journal-backend-prod alembic upgrade head
```

Create admin user:
```bash
docker exec -it trading-journal-backend-prod python create_admin.py
```

You'll be prompted to enter:
- Email
- Password
- Full name

### 5. Configure Firewall

Enable firewall with required ports:
```bash
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS (for future)
ufw enable
```

Type `y` to confirm.

### 6. Verify Deployment

Check all containers are running:
```bash
docker-compose -f docker-compose.production.yml ps
```

All services should show "Up" status.

Test the application:
```bash
curl http://localhost/api/health
# Should return: {"status":"healthy"}
```

### 7. Access Your Application

Open your browser and navigate to:
```
http://YOUR_DROPLET_IP
```

Login with the admin credentials you created.

## Optional: Setup Domain and HTTPS

### A. Point Domain to Droplet

1. Go to your domain registrar
2. Add an A record:
   - Host: `@` (or subdomain like `trading`)
   - Value: `YOUR_DROPLET_IP`
   - TTL: 3600

Wait 5-10 minutes for DNS propagation.

### B. Install SSL Certificate

Install Certbot:
```bash
apt install certbot python3-certbot-nginx -y
```

Stop nginx container temporarily:
```bash
docker-compose -f docker-compose.production.yml stop nginx
```

Obtain certificate (replace with your domain):
```bash
certbot certonly --standalone -d yourdomain.com
```

Copy certificates to nginx directory:
```bash
mkdir -p /opt/trading-journal/nginx/ssl
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/trading-journal/nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/trading-journal/nginx/ssl/
```

Edit nginx config:
```bash
cd /opt/trading-journal
nano nginx/nginx.conf
```

Uncomment the HTTPS server block and update `your-domain.com` with your actual domain.

Update `.env` with HTTPS URLs:
```bash
nano .env
```

Change:
```env
NEXT_PUBLIC_API_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

Restart all services:
```bash
docker-compose -f docker-compose.production.yml up -d --force-recreate
```

Access your site at: `https://yourdomain.com`

## Automatic Backups

Create backup script:
```bash
nano /opt/backup-trading-journal.sh
```

Paste:
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/trading-journal"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker exec trading-journal-db-prod pg_dump -U trading_admin trading_journal > $BACKUP_DIR/db_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_$DATE.sql.gz"
```

Make executable:
```bash
chmod +x /opt/backup-trading-journal.sh
```

Test backup:
```bash
/opt/backup-trading-journal.sh
```

Schedule daily backups at 2 AM:
```bash
crontab -e
```

Add line:
```
0 2 * * * /opt/backup-trading-journal.sh >> /var/log/trading-journal-backup.log 2>&1
```

## Monitoring & Maintenance

### View Logs
```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f backend
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.production.yml restart

# Specific service
docker-compose -f docker-compose.production.yml restart backend
```

### Update Application
```bash
cd /opt/trading-journal
git pull
docker-compose -f docker-compose.production.yml up -d --build
```

### Check Resource Usage
```bash
docker stats
```

### Database Console
```bash
docker exec -it trading-journal-db-prod psql -U trading_admin -d trading_journal
```

### Restore Backup
```bash
# Stop backend
docker-compose -f docker-compose.production.yml stop backend

# Restore database
gunzip -c /opt/backups/trading-journal/db_TIMESTAMP.sql.gz | \
  docker exec -i trading-journal-db-prod psql -U trading_admin -d trading_journal

# Restart backend
docker-compose -f docker-compose.production.yml start backend
```

## Troubleshooting

### Containers won't start
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs

# Check disk space
df -h

# Clean up Docker
docker system prune -a
```

### Application not accessible
```bash
# Check firewall
ufw status

# Check nginx
docker-compose -f docker-compose.production.yml logs nginx

# Test locally
curl http://localhost/api/health
```

### Database connection errors
```bash
# Check database logs
docker-compose -f docker-compose.production.yml logs db

# Verify environment variables
docker-compose -f docker-compose.production.yml config
```

### Out of memory
```bash
# Check memory usage
free -h

# Add swap space (2GB)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

## Cost Estimation

- **Basic Droplet**: $12/month (2GB RAM)
- **Domain**: $10-15/year (optional)
- **SSL Certificate**: Free (Let's Encrypt)
- **Backups**: Included in droplet storage

**Total**: ~$12/month + $1/month (domain)

## Security Checklist

- ✅ Change all default passwords in `.env`
- ✅ Use strong SECRET_KEY
- ✅ Enable firewall (ufw)
- ✅ Setup HTTPS with SSL certificate
- ✅ Keep system updated (`apt update && apt upgrade`)
- ✅ Enable automatic backups
- ✅ Disable root SSH login (optional)
- ✅ Setup fail2ban (optional)

## Next Steps

1. Add real trading data through the UI
2. Configure OAuth providers (Google/GitHub) for easier login
3. Setup monitoring (optional): Grafana + Prometheus
4. Configure email notifications (optional)
5. Setup CDN for faster global access (optional)

## Support

If you encounter issues:
1. Check the logs
2. Review the troubleshooting section
3. Create an issue on GitHub: https://github.com/theluckymak/trading-journal/issues

Happy Trading! 📈

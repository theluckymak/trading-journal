# MT5 Sync Service for VPS

This folder contains the MT5 sync service that runs on your Windows VPS to automatically sync trades from MetaTrader 5.

## Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   User Frontend     │────▶│   Railway API    │────▶│  PostgreSQL DB      │
│   (maktrades.app)   │     │  (Backend)       │     │                     │
└─────────────────────┘     └──────────────────┘     └─────────────────────┘
                                                              ▲
                                                              │
                                    ┌─────────────────────────┘
                                    │
                            ┌───────┴───────┐
                            │  Windows VPS  │
                            │    + MT5      │
                            │    + Python   │
                            └───────────────┘
```

## How It Works

1. **User enters MT5 credentials** in Settings page on maktrades.app
2. **Credentials are encrypted** and stored in the database
3. **VPS sync service** runs continuously on your Windows 7 VPS
4. **Serial processing**: For each user with active MT5 config:
   - Login to MT5 with their credentials
   - Fetch trade history
   - Insert new trades into database
   - Logout
   - Move to next user
5. **Repeat** every minute (configurable)

## Setup Instructions

### On Your VPS

1. **Install Python 3.8+**
   - Download from https://www.python.org/downloads/
   - Make sure to check "Add to PATH" during installation

2. **Install MT5 Terminal**
   - Download MetaTrader 5 from your broker
   - Install and login at least once to set it up

3. **Run Setup Script**
   ```batch
   setup.bat
   ```

4. **Configure Environment Variables**
   Set these environment variables on your VPS:
   ```
   DATABASE_URL=postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway
   ENCRYPTION_KEY=dev-encryption-key-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```

   Or edit them directly in `mt5_sync_service.py`

5. **Run the Service**
   ```batch
   python mt5_sync_service.py
   ```

### Running as a Windows Service (Recommended)

For production, you should run this as a Windows service so it starts automatically:

1. **Download NSSM** (Non-Sucking Service Manager)
   - https://nssm.cc/download

2. **Install the service**
   ```batch
   nssm install MT5SyncService
   ```
   
3. **Configure NSSM**
   - Path: `C:\Python39\python.exe` (your Python path)
   - Startup directory: Path to this folder
   - Arguments: `mt5_sync_service.py`

4. **Start the service**
   ```batch
   nssm start MT5SyncService
   ```

## Logs

The service writes logs to `mt5_sync.log` in this folder.

## Troubleshooting

### "MT5 initialization failed"
- Make sure MT5 terminal is installed
- Try opening MT5 manually first

### "Login failed"
- Check the credentials in the database
- Make sure the server name is correct
- Try logging in manually in MT5 first

### "Connection to database failed"
- Check your DATABASE_URL
- Make sure the VPS can reach Railway's database
- Check firewall settings

## Security Notes

- Passwords are encrypted using Fernet symmetric encryption
- The encryption key MUST match between the backend and this VPS script
- Never share your ENCRYPTION_KEY
- Use environment variables for sensitive config in production

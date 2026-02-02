@echo off
REM ============================================
REM MT5 Sync Service Setup for Windows VPS
REM ============================================

echo ==================================================
echo    MT5 Trading Journal Sync Service Setup
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found. Installing required packages...
echo.

REM Install required packages
pip install MetaTrader5 pg8000 SQLAlchemy pycryptodome requests

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install packages
    echo Please make sure pip is installed and you have internet connection
    pause
    exit /b 1
)

echo.
echo ==================================================
echo    Packages installed successfully!
echo ==================================================
echo.
echo NEXT STEPS:
echo.
echo 1. Make sure MT5 terminal is installed on this VPS
echo 2. Edit mt5_sync_service.py and set your DATABASE_URL and ENCRYPTION_KEY
echo    (Or set them as environment variables)
echo.
echo 3. To run the sync service:
echo    python mt5_sync_service.py
echo.
echo 4. To run as a Windows service (recommended for production):
echo    - Use NSSM (Non-Sucking Service Manager)
echo    - Download from: https://nssm.cc/download
echo    - Run: nssm install MT5SyncService
echo    - Point to python.exe and mt5_sync_service.py
echo.
echo ==================================================
pause

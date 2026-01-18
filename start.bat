@echo off
echo Starting Trading Journal Application...
echo ======================================
echo.

echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d %~dp0backend && python.exe start.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ======================================
echo Application Starting!
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Two command windows have opened.
echo Close them to stop the servers.
echo ======================================
pause

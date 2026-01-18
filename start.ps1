# Trading Journal Startup Script
# This script starts both the backend and frontend servers

Write-Host "Starting Trading Journal Application..." -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Start Backend
Write-Host "Starting Backend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; Write-Host 'Backend Server' -ForegroundColor Yellow; python.exe start.py"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; Write-Host 'Frontend Server' -ForegroundColor Yellow; npm run dev"

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "Application Starting!" -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Two terminal windows will open." -ForegroundColor Gray
Write-Host "Close them to stop the servers." -ForegroundColor Gray
Write-Host "======================================" -ForegroundColor Green

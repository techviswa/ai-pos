# POS System Quick Start Script for Windows
# Run this script from the project root: powershell -ExecutionPolicy Bypass -File setup.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "POS System - Quick Start (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow
$dockerInstalled = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)

if ($dockerInstalled) {
    Write-Host "✓ Docker found. Starting MongoDB container..." -ForegroundColor Green
    docker-compose up -d mongodb
    Write-Host "✓ MongoDB container started" -ForegroundColor Green
    Start-Sleep -Seconds 3
} else {
    Write-Host "⚠️  Docker not found. Ensure MongoDB is running on localhost:27017" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/4] Setting up Backend..." -ForegroundColor Yellow

# Navigate to backend
Set-Location backend

# Create venv if it doesn't exist
if (!(Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Gray
    python -m venv venv
}

# Activate venv
& .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

Write-Host "✓ Backend dependencies installed" -ForegroundColor Green
Set-Location ..

Write-Host ""
Write-Host "[3/4] Setting up Frontend..." -ForegroundColor Yellow

# Navigate to frontend
Set-Location frontend

# Install dependencies
npm install

Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
Set-Location ..

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup Complete! ✓" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Start the services in separate PowerShell windows:" -ForegroundColor White
Write-Host ""
Write-Host "Window 1 - Backend:" -ForegroundColor Yellow
Write-Host "  cd backend" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  uvicorn server:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "Window 2 - Frontend:" -ForegroundColor Yellow
Write-Host "  cd frontend" -ForegroundColor Gray
Write-Host "  npm start" -ForegroundColor Gray
Write-Host ""
Write-Host "Then open: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Admin Credentials:" -ForegroundColor Yellow
Write-Host "  Email: owner@pos.com" -ForegroundColor Gray
Write-Host "  Password: admin123" -ForegroundColor Gray
Write-Host ""

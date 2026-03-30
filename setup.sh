#!/bin/bash
# POS System Quick Start Script for macOS/Linux

set -e

echo "=========================================="
echo "POS System - Quick Start"
echo "=========================================="
echo ""

# Check if Docker is running
echo "[1/4] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Installing MongoDB locally..."
    echo "Please ensure MongoDB is installed and running on localhost:27017"
else
    echo "✓ Docker found. Starting MongoDB container..."
    docker-compose up -d mongodb
    echo "✓ MongoDB container started"
fi

echo ""
echo "[2/4] Setting up Backend..."
cd backend

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "✓ Backend dependencies installed"
cd ..

echo ""
echo "[3/4] Setting up Frontend..."
cd frontend

# Install dependencies
npm install

echo "✓ Frontend dependencies installed"
cd ..

echo ""
echo "=========================================="
echo "Setup Complete! ✓"
echo "=========================================="
echo ""
echo "Start the services in separate terminals:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn server:app --reload"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend"
echo "  npm start"
echo ""
echo "Then open: http://localhost:3000"
echo ""
echo "Admin Credentials:"
echo "  Email: owner@pos.com"
echo "  Password: admin123"
echo ""

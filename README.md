# POS System - Setup & Run Instructions

A full-stack Point of Sale (POS) system with FastAPI backend and React frontend.

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **MongoDB 5.0+** (for database)

## Quick Start

### 1. Setup MongoDB

#### Option A: Using Docker (Recommended)
```bash
# Create and run MongoDB container
docker run -d --name pos-mongodb -p 27017:27017 mongo:latest
```

#### Option B: Local Installation
- Download MongoDB from [mongodb.com](https://www.mongodb.com/try/download/community)
- Install and start the MongoDB service
- Verify it's running on `localhost:27017`

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server (runs on http://localhost:8000)
uvicorn server:app --reload
```

**API Documentation:** http://localhost:8000/docs

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server (runs on http://localhost:3000)
npm start
```

## Default Admin Credentials

- **Email:** owner@pos.com
- **Password:** admin123
- **Role:** Owner

> **Note:** Update credentials in `backend/.env` for production.

## Environment Variables

### Backend (`backend/.env`)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
JWT_SECRET=your-secret-key-here
ADMIN_EMAIL=owner@pos.com
ADMIN_PASSWORD=admin123
CORS_ORIGINS=*
LOG_DIR=./memory
```

### Frontend (`frontend/.env`)
```
REACT_APP_BACKEND_URL=http://localhost:8000
WDS_SOCKET_PORT=3000
ENABLE_HEALTH_CHECK=false
```

## Project Structure

```
├── backend/
│   ├── server.py          # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env              # Environment variables
├── frontend/
│   ├── src/              # React components
│   ├── package.json      # Node dependencies
│   └── .env              # React environment variables
├── tests/                # Test files
└── design_guidelines.json # UI design specifications
```

## Common Issues & Troubleshooting

### Issue: "Cannot connect to MongoDB"
- **Solution:** Ensure MongoDB is running: `mongosh` (or `mongo` on older versions)
- If using Docker: `docker ps` to verify container is running

### Issue: "Port 8000 already in use"
- **Solution:** Change port: `uvicorn server:app --reload --port 8001`

### Issue: "Port 3000 already in use"
- **Solution:** Change port: `PORT=3001 npm start` (or set in .env)

### Issue: CORS errors
- **Solution:** Verify `REACT_APP_BACKEND_URL` in `frontend/.env` matches your backend URL

## API Endpoints

- **Auth:** `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me`, `POST /api/auth/logout`
- **Products:** `GET /api/products`, `POST /api/products`, `PUT /api/products/{id}`, `DELETE /api/products/{id}`
- **Bills:** `GET /api/bills`, `POST /api/bills`, `GET /api/bills/{id}`
- **Dashboard:** `GET /api/dashboard/stats` (Owner only)
- **Staff:** `GET /api/staff`, `POST /api/staff` (Owner only)

## Running Tests

```bash
cd backend
pytest
```

## Stopping Services

```bash
# Stop MongoDB container (if using Docker)
docker stop pos-mongodb

# Stop backend
# Press Ctrl+C in the terminal running uvicorn

# Stop frontend
# Press Ctrl+C in the terminal running npm start
```

## License

Proprietary - All rights reserved

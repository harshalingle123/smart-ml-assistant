# Quick Start Guide - Dual Query Intelligence

Get the application up and running in minutes.

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL (or configured database)

## Setup Steps

### 1. Backend Setup

```bash
# Navigate to backend directory
cd C:\Users\Harshal\Downloads\DualQueryIntelligence\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Copy .env.example to .env and configure:
# - DATABASE_URL
# - SECRET_KEY
# - CORS_ORIGINS

# Run database migrations
alembic upgrade head

# Start the backend server
python run.py
```

Backend will be running on `http://localhost:8000`

### 2. Frontend Setup

```bash
# Open a new terminal
# Navigate to frontend directory
cd C:\Users\Harshal\Downloads\DualQueryIntelligence\frontend

# Install dependencies
npm install

# (Optional) Create .env file for custom API URL
# Copy .env.example to .env if needed

# Start development server
npm run dev
```

Frontend will be running on `http://localhost:5173`

## Verify Installation

1. Open browser to `http://localhost:8000/docs` - FastAPI documentation should load
2. Open browser to `http://localhost:5173` - React app should load
3. Try creating an account and logging in

## Common Issues

### Backend won't start
- Check DATABASE_URL is correct in backend/.env
- Ensure PostgreSQL is running
- Verify all dependencies installed: `pip install -r requirements.txt`

### Frontend won't start
- Ensure backend is running first
- Check node_modules installed: `npm install`
- Verify port 5173 is available

### API calls fail
- Confirm backend is running on port 8000
- Check browser console for error details
- Verify CORS settings in backend config

## Development Workflow

1. Start backend first (required for frontend to function)
2. Start frontend in a separate terminal
3. Make changes to code
4. Frontend hot-reloads automatically
5. Backend auto-reloads with uvicorn's --reload flag

## Next Steps

- Read `frontend/README.md` for frontend details
- Read `backend/README.md` for backend details (if exists)
- Check `INTEGRATION_SUMMARY.md` for architecture overview
- Explore API docs at `http://localhost:8000/docs`

## Quick Commands Reference

### Backend
```bash
# Start server
python run.py

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Frontend
```bash
# Development
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run check
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  React Frontend (http://localhost:5173)        │
│  - TypeScript + Vite                           │
│  - TanStack Query                              │
│  - Tailwind CSS                                │
│                                                 │
└────────────────┬────────────────────────────────┘
                 │
                 │ HTTP/REST + JWT
                 │
┌────────────────▼────────────────────────────────┐
│                                                 │
│  FastAPI Backend (http://localhost:8000)       │
│  - Python 3.9+                                 │
│  - SQLAlchemy ORM                              │
│  - PostgreSQL Database                         │
│  - JWT Authentication                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Success!

You should now have both the backend and frontend running. Try:

1. Registering a new account
2. Creating a new chat
3. Uploading a dataset
4. Starting a fine-tune job

For detailed documentation, see the README files in each directory.

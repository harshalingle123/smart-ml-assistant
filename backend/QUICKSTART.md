# Quick Start Guide

## Prerequisites

1. Python 3.10 or higher
2. PostgreSQL 12 or higher
3. Git (optional)

## Setup Steps

### 1. Database Setup

Create a PostgreSQL database for the application:

```sql
CREATE DATABASE dualquery_db;
```

Or use the command line:
```bash
createdb dualquery_db
```

### 2. Environment Configuration

Copy the example environment file and configure it:

**Windows:**
```bash
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

Edit `.env` and update the following:

```env
DATABASE_URL=postgresql+asyncpg://your_user:your_password@localhost:5432/dualquery_db
SECRET_KEY=<generate-a-secure-key>
```

To generate a secure SECRET_KEY, run:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Install Dependencies

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start the Server

**Option 1: Using the run script**
```bash
python run.py
```

**Option 2: Using startup scripts**

Windows:
```bash
start.bat
```

macOS/Linux:
```bash
chmod +x start.sh
./start.sh
```

**Option 3: Using uvicorn directly**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Verify Installation

Open your browser and visit:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Testing the API

### Register a User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"testuser\",\"password\":\"testpass123\"}"
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"testuser\",\"password\":\"testpass123\"}"
```

Copy the `access_token` from the response.

### Create a Chat

```bash
curl -X POST http://localhost:8000/api/chats \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d "{\"title\":\"My First Chat\"}"
```

## Troubleshooting

### Database Connection Issues

If you get database connection errors:
1. Verify PostgreSQL is running: `pg_isready`
2. Check your DATABASE_URL in `.env`
3. Ensure the database exists
4. Test connection: `psql -h localhost -U your_user -d dualquery_db`

### Module Not Found Errors

If you get import errors:
1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.10+)

### Migration Errors

If migrations fail:
1. Drop and recreate the database
2. Run migrations again: `alembic upgrade head`
3. Check alembic.ini for correct configuration

## Next Steps

- Review the full README.md for detailed documentation
- Explore the API documentation at http://localhost:8000/docs
- Configure CORS_ORIGINS in .env to match your frontend URL
- Set up your frontend to connect to http://localhost:8000

## Production Deployment

For production deployment:

1. Set `ENVIRONMENT=production` in .env
2. Use a strong SECRET_KEY
3. Configure proper CORS_ORIGINS
4. Use a production-grade database
5. Run with multiple workers:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
6. Set up reverse proxy (nginx, traefik)
7. Enable HTTPS/SSL
8. Configure database backups
9. Set up monitoring and logging

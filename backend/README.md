# Dual Query Intelligence Backend

FastAPI backend for the dual query intelligence platform with chat, dataset management, model fine-tuning, and API key management.

## Features

- User authentication (register, login)
- Chat management (create, read, update, delete)
- Message operations (create, list by chat)
- Dataset operations (upload CSV, list, get, delete)
- Model operations (create, list, get)
- Fine-tune job management (create, track status, list)
- API key management (create, list, delete)
- JWT-based authentication
- Async PostgreSQL database operations
- CORS support for frontend integration
- Request logging middleware

## Technology Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0+** - Async ORM
- **PostgreSQL** - Database (via asyncpg driver)
- **Pydantic v2** - Data validation
- **Alembic** - Database migrations
- **JWT** - Authentication tokens
- **Bcrypt** - Password hashing

## Project Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   └── security.py        # Auth & password utilities
│   ├── models/
│   │   └── database_models.py # SQLAlchemy models
│   ├── routers/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── chats.py           # Chat endpoints
│   │   ├── messages.py        # Message endpoints
│   │   ├── datasets.py        # Dataset endpoints
│   │   ├── models.py          # Model endpoints
│   │   ├── finetune.py        # Fine-tuning endpoints
│   │   └── apikeys.py         # API key endpoints
│   ├── schemas/
│   │   ├── user_schemas.py    # User Pydantic schemas
│   │   ├── chat_schemas.py    # Chat Pydantic schemas
│   │   ├── message_schemas.py # Message Pydantic schemas
│   │   ├── model_schemas.py   # Model Pydantic schemas
│   │   ├── dataset_schemas.py # Dataset Pydantic schemas
│   │   ├── finetune_schemas.py# Fine-tune Pydantic schemas
│   │   └── apikey_schemas.py  # API key Pydantic schemas
│   ├── database.py            # Database connection
│   ├── dependencies.py        # FastAPI dependencies
│   ├── middleware.py          # Custom middleware
│   └── main.py                # FastAPI app entry point
├── alembic/
│   ├── versions/              # Migration files
│   ├── env.py                 # Alembic environment
│   └── script.py.mako         # Migration template
├── alembic.ini                # Alembic configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip or pipenv

### Installation

1. **Clone the repository** (if not already done)
   ```bash
   cd DualQueryIntelligence/backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SECRET_KEY`: A secure random string (generate with `openssl rand -hex 32`)
   - `CORS_ORIGINS`: Frontend URLs (comma-separated)

6. **Create the database**
   ```bash
   createdb your_database_name
   ```
   Or use your PostgreSQL client to create a database.

7. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

### Running the Server

**Development mode:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: `http://localhost:8000`

API documentation (Swagger UI): `http://localhost:8000/docs`
Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | 30 |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | http://localhost:5173,http://localhost:3000 |
| `ENVIRONMENT` | Environment mode | development |

## Database Migrations

**Create a new migration:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback one migration:**
```bash
alembic downgrade -1
```

**View migration history:**
```bash
alembic history
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user info

### Chats
- `POST /api/chats` - Create new chat
- `GET /api/chats` - List user's chats
- `GET /api/chats/{chat_id}` - Get chat by ID
- `PATCH /api/chats/{chat_id}` - Update chat
- `DELETE /api/chats/{chat_id}` - Delete chat

### Messages
- `POST /api/messages` - Create new message
- `GET /api/messages/chat/{chat_id}` - Get messages by chat
- `GET /api/messages/{message_id}` - Get message by ID

### Datasets
- `POST /api/datasets/upload` - Upload CSV dataset
- `GET /api/datasets` - List user's datasets
- `GET /api/datasets/{dataset_id}` - Get dataset by ID
- `DELETE /api/datasets/{dataset_id}` - Delete dataset

### Models
- `POST /api/models` - Create new model
- `GET /api/models` - List user's models
- `GET /api/models/{model_id}` - Get model by ID

### Fine-tuning
- `POST /api/finetune` - Create fine-tune job
- `GET /api/finetune` - List fine-tune jobs
- `GET /api/finetune/{job_id}` - Get fine-tune job by ID
- `PATCH /api/finetune/{job_id}/status` - Update job status

### API Keys
- `POST /api/apikeys` - Create API key
- `GET /api/apikeys` - List API keys
- `DELETE /api/apikeys/{apikey_id}` - Delete API key

## Testing

All endpoints except `/`, `/health`, `/api/auth/register`, and `/api/auth/login` require authentication via Bearer token.

**Example authentication:**
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Use token in subsequent requests
curl -X GET http://localhost:8000/api/chats \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Development

### Code Style
- Follow PEP 8 conventions
- Use type hints throughout
- Async/await patterns for all I/O operations

### Adding New Endpoints
1. Create Pydantic schemas in `app/schemas/`
2. Add database models in `app/models/database_models.py`
3. Create router in `app/routers/`
4. Register router in `app/main.py`
5. Create and run migrations

## Troubleshooting

**Database connection errors:**
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env`
- Ensure database exists

**Import errors:**
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

**Migration errors:**
- Check database connection
- Verify alembic.ini configuration
- Review migration files in `alembic/versions/`

## License

MIT License

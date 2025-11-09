# Project Structure

## Complete Backend Directory Structure

```
backend/
├── app/                                # Main application package
│   ├── __init__.py                    # Package initializer
│   ├── main.py                        # FastAPI application entry point
│   ├── database.py                    # Database connection and session management
│   ├── dependencies.py                # FastAPI dependency injection functions
│   ├── middleware.py                  # Custom middleware (logging)
│   │
│   ├── core/                          # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py                  # Application configuration and settings
│   │   └── security.py                # Authentication and password hashing
│   │
│   ├── models/                        # SQLAlchemy database models
│   │   ├── __init__.py
│   │   └── database_models.py         # All database table models
│   │
│   ├── schemas/                       # Pydantic schemas for validation
│   │   ├── __init__.py
│   │   ├── user_schemas.py            # User request/response schemas
│   │   ├── chat_schemas.py            # Chat request/response schemas
│   │   ├── message_schemas.py         # Message request/response schemas
│   │   ├── model_schemas.py           # Model request/response schemas
│   │   ├── dataset_schemas.py         # Dataset request/response schemas
│   │   ├── finetune_schemas.py        # Fine-tune job schemas
│   │   └── apikey_schemas.py          # API key schemas
│   │
│   └── routers/                       # API route handlers
│       ├── __init__.py
│       ├── auth.py                    # Authentication endpoints (register, login)
│       ├── chats.py                   # Chat CRUD endpoints
│       ├── messages.py                # Message CRUD endpoints
│       ├── datasets.py                # Dataset upload and management
│       ├── models.py                  # Model management endpoints
│       ├── finetune.py                # Fine-tuning job endpoints
│       └── apikeys.py                 # API key management
│
├── alembic/                           # Database migrations
│   ├── versions/                      # Migration version files
│   │   └── 001_initial_migration.py   # Initial database schema
│   ├── env.py                         # Alembic environment configuration
│   └── script.py.mako                 # Migration template
│
├── alembic.ini                        # Alembic configuration file
├── requirements.txt                   # Python package dependencies
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
├── run.py                             # Development server runner
├── start.bat                          # Windows startup script
├── start.sh                           # Unix/Linux startup script
├── README.md                          # Comprehensive documentation
├── QUICKSTART.md                      # Quick setup guide
└── PROJECT_STRUCTURE.md              # This file
```

## File Descriptions

### Configuration Files

- **requirements.txt**: Lists all Python dependencies (FastAPI, SQLAlchemy, etc.)
- **alembic.ini**: Alembic migration tool configuration
- **.env.example**: Template for environment variables (copy to .env)
- **.gitignore**: Files and directories to exclude from git

### Application Core

- **app/main.py**: FastAPI app initialization, middleware setup, router registration
- **app/database.py**: Async database engine and session factory
- **app/dependencies.py**: Reusable dependency functions (e.g., get_current_user)
- **app/middleware.py**: Custom middleware for request/response logging

### Configuration & Security

- **app/core/config.py**: Centralized settings using Pydantic BaseSettings
- **app/core/security.py**: JWT token creation/validation, password hashing

### Database Models (SQLAlchemy)

All models in **app/models/database_models.py**:
- **User**: User accounts with authentication and usage tracking
- **Chat**: Chat sessions with model and dataset associations
- **Message**: Individual messages within chats
- **Model**: Fine-tuned AI models
- **Dataset**: Uploaded datasets for training
- **FineTuneJob**: Training job tracking and progress
- **ApiKey**: API keys for model access

### Request/Response Schemas (Pydantic)

Located in **app/schemas/**:
- Validate incoming request data
- Serialize database models to JSON responses
- Separate Create/Update/Response schemas for each entity

### API Routers

Located in **app/routers/**:

| Router | Prefix | Purpose |
|--------|--------|---------|
| auth.py | /api/auth | User registration, login, get current user |
| chats.py | /api/chats | Chat CRUD operations |
| messages.py | /api/messages | Message creation and retrieval |
| datasets.py | /api/datasets | Dataset upload, list, delete |
| models.py | /api/models | Model creation and listing |
| finetune.py | /api/finetune | Fine-tune job management |
| apikeys.py | /api/apikeys | API key generation and management |

### Database Migrations

- **alembic/env.py**: Alembic environment setup for async SQLAlchemy
- **alembic/versions/**: Migration scripts (auto-generated or manual)
- **alembic.ini**: Alembic settings (migration location, logging)

### Utility Scripts

- **run.py**: Simple development server launcher
- **start.bat**: Automated setup and run script for Windows
- **start.sh**: Automated setup and run script for Unix/Linux

## Data Flow

### Authentication Flow
1. Client sends credentials to `/api/auth/login`
2. `auth.py` router validates credentials
3. `security.py` creates JWT token
4. Client includes token in Authorization header
5. `dependencies.py` validates token and returns user

### API Request Flow
1. Request hits FastAPI application
2. `LoggingMiddleware` logs request details
3. CORS middleware validates origin
4. Router function receives request
5. Dependencies inject database session and current user
6. Pydantic schema validates request body
7. Database operation performed via SQLAlchemy
8. Response serialized via Pydantic schema
9. JSON response returned to client

### Database Session Flow
1. Route function depends on `get_db`
2. `get_db` creates async session from pool
3. Session used for database operations
4. Session automatically closed after request
5. Transactions committed or rolled back as needed

## Development Workflow

### Adding a New Endpoint

1. **Define Database Model** (if needed)
   - Add to `app/models/database_models.py`
   - Create migration: `alembic revision --autogenerate -m "description"`
   - Apply migration: `alembic upgrade head`

2. **Create Pydantic Schemas**
   - Add to appropriate file in `app/schemas/`
   - Define Create, Update, Response schemas

3. **Implement Router**
   - Create or update router in `app/routers/`
   - Use async functions with proper dependencies
   - Add proper error handling

4. **Register Router**
   - Import in `app/main.py`
   - Add `app.include_router(router_name.router)`

5. **Test**
   - Start server: `python run.py`
   - Access docs: `http://localhost:8000/docs`
   - Test endpoints via Swagger UI or curl

## Key Design Patterns

### Async/Await
- All database operations are async
- Use `async def` for route functions
- Use `await` for database queries

### Dependency Injection
- Database sessions injected via `Depends(get_db)`
- Current user injected via `Depends(get_current_user)`
- Reusable dependencies in `app/dependencies.py`

### Repository Pattern
- Not explicitly implemented, but can be added
- Would create service layer between routes and database

### Error Handling
- HTTPException raised for client errors (404, 400, 401)
- Database constraints enforced at model level
- Validation errors caught by Pydantic automatically

## Security Considerations

1. **Password Security**: Bcrypt hashing via passlib
2. **JWT Tokens**: Signed with SECRET_KEY, include expiration
3. **Authorization**: All endpoints (except auth) require valid token
4. **CORS**: Restricted to configured origins
5. **Input Validation**: Pydantic schemas validate all inputs
6. **SQL Injection**: Prevented by SQLAlchemy ORM

## Performance Optimizations

1. **Async I/O**: Non-blocking database operations
2. **Connection Pooling**: SQLAlchemy manages connection pool
3. **Pagination**: Limit/offset parameters on list endpoints
4. **Indexes**: Database indexes on foreign keys and lookup fields
5. **Lazy Loading**: Relationships loaded on-demand

## Extensibility Points

1. **Add New Routers**: Import and register in main.py
2. **Custom Middleware**: Add to main.py middleware stack
3. **Background Tasks**: Use FastAPI BackgroundTasks
4. **WebSocket Support**: Add WebSocket routes for real-time features
5. **Caching**: Add Redis for session/response caching
6. **File Storage**: Integrate S3/Azure for dataset files
7. **AI Integration**: Add OpenAI/Anthropic API calls in services
8. **Message Queue**: Add Celery for async job processing

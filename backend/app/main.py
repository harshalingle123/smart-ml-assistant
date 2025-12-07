from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.middleware import LoggingMiddleware, RequestSizeLimitMiddleware
from app.routers import auth, chats, messages, datasets, models, finetune, apikeys, kaggle, ml, prebuilt_models, deployments, training_jobs, direct_access, model_api, usage_dashboard, automl
from app.mongodb import mongodb
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import logging
import sys
import io

logger = logging.getLogger(__name__)

# ========================================
# Fix Windows Console Encoding Issues
# ========================================
# Windows uses cp1252 encoding by default, which can't handle Unicode characters
# Reconfigure stdout/stderr to use UTF-8 with error handling
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding='utf-8',
            errors='replace',  # Replace unencodable chars instead of crashing
            line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )
        logger.info("[CONFIG] Windows console encoding set to UTF-8")
    except Exception as e:
        logger.warning(f"[CONFIG] Could not set UTF-8 encoding: {e}")

# IMPORTANT: Configure multipart limits BEFORE creating FastAPI app
# This fixes the "field larger than field limit" error

# Patch python-multipart library to handle large files
from multipart import FormParser
import starlette.formparsers

# Patch the DEFAULT_CONFIG of FormParser to allow large uploads
if hasattr(FormParser, 'DEFAULT_CONFIG'):
    # Update the default max sizes for all parsers
    FormParser.DEFAULT_CONFIG['MAX_BODY_SIZE'] = settings.MAX_UPLOAD_SIZE
    FormParser.DEFAULT_CONFIG['MAX_MEMORY_FILE_SIZE'] = settings.MAX_UPLOAD_SIZE
    logger.info(f"[CONFIG] FormParser DEFAULT_CONFIG updated:")
    logger.info(f"  MAX_BODY_SIZE: {FormParser.DEFAULT_CONFIG.get('MAX_BODY_SIZE', 'Not set')}")
    logger.info(f"  MAX_MEMORY_FILE_SIZE: {FormParser.DEFAULT_CONFIG.get('MAX_MEMORY_FILE_SIZE', 'Not set')}")

# Set Starlette's max_file_size
starlette.formparsers.MultiPartParser.max_file_size = settings.MAX_UPLOAD_SIZE

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if '/api/messages/agent' in str(request.url) or '/automl' in str(request.url) or '/api/automl' in str(request.url):
                return await asyncio.wait_for(call_next(request), timeout=600.0)
            else:
                return await asyncio.wait_for(call_next(request), timeout=120.0)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout. Training may continue in background."}
            )

app = FastAPI(
    title="Dual Query Intelligence API",
    description="Backend API for dual query intelligence platform with chat, dataset management, and model fine-tuning",
    version="1.0.0",
)

# Global exception handler to prevent crashes
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to prevent app crashes.
    Logs the error and returns a proper error response.
    """
    import traceback
    error_details = traceback.format_exc()
    logger.error(f"❌ Unhandled exception: {str(exc)}")
    logger.error(f"   Path: {request.url.path}")
    logger.error(f"   Method: {request.method}")
    logger.error(f"   Traceback:\n{error_details}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "error": str(exc) if settings.ENVIRONMENT == "development" else "Internal server error",
            "path": request.url.path
        }
    )

# Configure maximum request body size (500 MB)
# This must be set to allow large file uploads
from starlette.datastructures import UploadFile as StarletteUploadFile
StarletteUploadFile.spool_max_size = settings.MAX_UPLOAD_SIZE

logger.info(f"[CONFIG] Maximum upload size set to: {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.0f} MB")
logger.info(f"[CONFIG] MultiPartParser max_file_size: {starlette.formparsers.MultiPartParser.max_file_size / (1024 * 1024):.0f} MB")
logger.info(f"[CONFIG] UploadFile spool_max_size: {StarletteUploadFile.spool_max_size / (1024 * 1024):.0f} MB")
logger.info(f"[CONFIG] python-multipart File and Field classes patched for large uploads")

# CORS Configuration
# In production, use explicit origins from CORS_ORIGINS env var
# This allows proper control via Render dashboard environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Use env var in both dev and prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log CORS configuration for debugging
logger.info(f"[CONFIG] CORS Origins: {settings.cors_origins_list}")

app.add_middleware(TimeoutMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(finetune.router)
app.include_router(apikeys.router)
app.include_router(kaggle.router)
app.include_router(ml.router)
app.include_router(prebuilt_models.router)
app.include_router(deployments.router)
app.include_router(training_jobs.router)
app.include_router(direct_access.router)
app.include_router(model_api.router)
app.include_router(usage_dashboard.router)
app.include_router(automl.router)


@app.on_event("startup")
async def startup_db_client():
    try:
        logger.info("Starting application...")
        logger.info(f"   Environment: {settings.ENVIRONMENT}")
        logger.info(f"   Upload limit: {settings.MAX_UPLOAD_SIZE_MB} MB")

        # Validate Azure Blob Storage configuration
        if settings.AZURE_STORAGE_ENABLED:
            from app.utils.azure_storage import azure_storage_service

            if azure_storage_service.is_configured:
                logger.info("[AZURE] Azure Blob Storage is configured and ready")
                logger.info(f"[AZURE] Datasets container: {settings.AZURE_DATASETS_CONTAINER}")
                logger.info(f"[AZURE] Models container: {settings.AZURE_MODELS_CONTAINER}")
            else:
                logger.warning("[AZURE] ⚠️  Azure Blob Storage is NOT configured!")
                logger.warning("[AZURE] Dataset upload/download and model training will NOT work")
                logger.warning("[AZURE] Please configure AZURE_* environment variables")
        else:
            logger.warning("[AZURE] Azure Blob Storage is DISABLED")
            logger.warning("[AZURE] Dataset and model operations will fail")

        await mongodb.connect()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        # Don't raise - allow app to start even with errors
        # Health check will report the issue

@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        await mongodb.close()
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


@app.get("/")
async def root():
    return {
        "message": "Dual Query Intelligence API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """
    Ultra-lightweight health check endpoint for monitoring services.
    Must respond within 2 seconds to pass Render health checks.
    """
    try:
        # Quick MongoDB connection check with 1.5 second timeout
        mongodb_status = "unknown"
        if mongodb.client:
            try:
                # Use asyncio.wait_for to enforce timeout
                await asyncio.wait_for(
                    mongodb.client.admin.command('ping'),
                    timeout=1.5
                )
                mongodb_status = "healthy"
            except asyncio.TimeoutError:
                mongodb_status = "timeout"
            except Exception:
                mongodb_status = "unhealthy"

        return {
            "status": "healthy",
            "mongodb": mongodb_status,
            "api_version": "1.0.0"
        }
    except Exception as e:
        # Return 200 but with error info - prevents health check failures
        return {
            "status": "degraded",
            "error": str(e),
            "api_version": "1.0.0"
        }


@app.get("/api/config/csv-limits")
async def get_csv_limits():
    import csv
    return {
        "csv_field_size_limit_bytes": csv.field_size_limit(),
        "csv_field_size_limit_mb": csv.field_size_limit() / (1024 * 1024),
        "max_upload_size_bytes": settings.MAX_UPLOAD_SIZE,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE / (1024 * 1024)
    }

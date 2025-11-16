from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.middleware import LoggingMiddleware, RequestSizeLimitMiddleware
from app.routers import auth, chats, messages, datasets, models, finetune, apikeys, kaggle, ml, prebuilt_models, deployments, training_jobs, direct_access, model_api, usage_dashboard, automl
from app.mongodb import mongodb

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
    print(f"[CONFIG] FormParser DEFAULT_CONFIG updated:")
    print(f"  MAX_BODY_SIZE: {FormParser.DEFAULT_CONFIG.get('MAX_BODY_SIZE', 'Not set')}")
    print(f"  MAX_MEMORY_FILE_SIZE: {FormParser.DEFAULT_CONFIG.get('MAX_MEMORY_FILE_SIZE', 'Not set')}")

# Set Starlette's max_file_size
starlette.formparsers.MultiPartParser.max_file_size = settings.MAX_UPLOAD_SIZE

app = FastAPI(
    title="Dual Query Intelligence API",
    description="Backend API for dual query intelligence platform with chat, dataset management, and model fine-tuning",
    version="1.0.0",
)

# Configure maximum request body size (500 MB)
# This must be set to allow large file uploads
from starlette.datastructures import UploadFile as StarletteUploadFile
StarletteUploadFile.spool_max_size = settings.MAX_UPLOAD_SIZE

print(f"[CONFIG] Maximum upload size set to: {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.0f} MB")
print(f"[CONFIG] MultiPartParser max_file_size: {starlette.formparsers.MultiPartParser.max_file_size / (1024 * 1024):.0f} MB")
print(f"[CONFIG] UploadFile spool_max_size: {StarletteUploadFile.spool_max_size / (1024 * 1024):.0f} MB")
print(f"[CONFIG] python-multipart File and Field classes patched for large uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    await mongodb.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    await mongodb.close()


@app.get("/")
async def root():
    return {
        "message": "Dual Query Intelligence API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/config/csv-limits")
async def get_csv_limits():
    import csv
    return {
        "csv_field_size_limit_bytes": csv.field_size_limit(),
        "csv_field_size_limit_mb": csv.field_size_limit() / (1024 * 1024),
        "max_upload_size_bytes": settings.MAX_UPLOAD_SIZE,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE / (1024 * 1024)
    }

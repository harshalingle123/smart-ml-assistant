from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.middleware import LoggingMiddleware
from app.routers import auth, chats, messages, datasets, models, finetune, apikeys
from app.mongodb import mongodb

app = FastAPI(
    title="Dual Query Intelligence API",
    description="Backend API for dual query intelligence platform with chat, dataset management, and model fine-tuning",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(finetune.router)
app.include_router(apikeys.router)


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

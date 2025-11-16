from fastapi import APIRouter, Depends, HTTPException, status
from app.mongodb import mongodb
from app.models.mongodb_models import User, DirectAccessKey
from app.schemas.direct_access_schemas import (
    DirectAccessRequest,
    DirectAccessResponse,
    ModelInfo,
    ApiKeyInfo,
    ModelListItem
)
from app.dependencies import get_current_user
from bson import ObjectId
from datetime import datetime, timedelta
import secrets
from typing import List, Optional

router = APIRouter(prefix="/api/direct-access", tags=["Direct Access"])


AVAILABLE_MODELS = {
    "sentiment": {
        "vader": {
            "id": "vader",
            "name": "VADER Sentiment Analysis",
            "description": "Fast, rule-based sentiment analysis ideal for social media and reviews",
            "task": "sentiment",
            "accuracy": 0.85,
            "latency_ms": 5,
            "free_tier": 10000,
            "pricing": "$0.0001 per request after free tier",
            "languages": ["en"],
            "priority_match": {"speed": 10, "cost": 10, "accuracy": 6}
        },
        "distilbert": {
            "id": "distilbert",
            "name": "DistilBERT Sentiment",
            "description": "High-accuracy transformer model for professional sentiment analysis",
            "task": "sentiment",
            "accuracy": 0.94,
            "latency_ms": 100,
            "free_tier": 1000,
            "pricing": "$0.0006 per request after free tier",
            "languages": ["en", "multilingual"],
            "priority_match": {"speed": 7, "cost": 7, "accuracy": 10}
        },
        "roberta": {
            "id": "roberta",
            "name": "RoBERTa Sentiment",
            "description": "State-of-the-art transformer for detailed sentiment classification",
            "task": "sentiment",
            "accuracy": 0.92,
            "latency_ms": 150,
            "free_tier": 1000,
            "pricing": "$0.002 per request after free tier",
            "languages": ["en", "multilingual"],
            "priority_match": {"speed": 6, "cost": 5, "accuracy": 9}
        }
    },
    "classification": {
        "spam-detection": {
            "id": "spam-detection",
            "name": "Spam Detection",
            "description": "Identify spam messages and emails with high precision",
            "task": "classification",
            "accuracy": 0.97,
            "latency_ms": 80,
            "free_tier": 5000,
            "pricing": "$0.0001 per request after free tier",
            "languages": ["en", "multilingual"],
            "priority_match": {"speed": 8, "cost": 9, "accuracy": 10}
        },
        "language-id": {
            "id": "language-id",
            "name": "Language Detection",
            "description": "Detect language from text with 99% accuracy",
            "task": "classification",
            "accuracy": 0.99,
            "latency_ms": 20,
            "free_tier": 20000,
            "pricing": "$0.0001 per request after free tier",
            "languages": ["multilingual"],
            "priority_match": {"speed": 10, "cost": 10, "accuracy": 10}
        }
    }
}


def select_best_model(task: str, priority: str, language: str = "en") -> dict:
    if task not in AVAILABLE_MODELS:
        return None

    models = AVAILABLE_MODELS[task]
    best_model = None
    best_score = -1

    for model_id, model_data in models.items():
        if language not in model_data["languages"] and "multilingual" not in model_data["languages"]:
            continue

        score = model_data["priority_match"].get(priority, 5)

        if score > best_score:
            best_score = score
            best_model = model_data

    return best_model


def generate_api_key() -> str:
    return f"sk_live_{secrets.token_urlsafe(32)}"


@router.post("", response_model=DirectAccessResponse, status_code=status.HTTP_201_CREATED)
async def request_direct_access(
    request: DirectAccessRequest,
    current_user: User = Depends(get_current_user)
):
    model_data = select_best_model(request.task, request.priority, request.language)

    if not model_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No models available for task '{request.task}' with language '{request.language}'"
        )

    existing_key = await mongodb.database["direct_access_keys"].find_one({
        "user_id": current_user.id,
        "model_id": model_data["id"],
        "status": "active"
    })

    if existing_key:
        model_info = ModelInfo(
            id=model_data["id"],
            name=model_data["name"],
            accuracy=model_data["accuracy"],
            latency_ms=model_data["latency_ms"],
            free_tier=model_data["free_tier"]
        )

        return DirectAccessResponse(
            status="provisioned",
            endpoint=f"/v1/sentiment/{model_data['id']}",
            api_key=existing_key["api_key"],
            model=model_info,
            pricing=model_data["pricing"],
            expires_at=existing_key.get("expires_at").isoformat() if existing_key.get("expires_at") else None
        )

    api_key = generate_api_key()

    new_key = DirectAccessKey(
        user_id=current_user.id,
        api_key=api_key,
        model_id=model_data["id"],
        model_name=model_data["name"],
        task=request.task,
        subtask=request.subtask,
        usage_plan="free",
        free_tier_limit=model_data["free_tier"],
        rate_limit=10,
        priority=request.priority,
        language=request.language
    )

    await mongodb.database["direct_access_keys"].insert_one(new_key.dict(by_alias=True))

    model_info = ModelInfo(
        id=model_data["id"],
        name=model_data["name"],
        accuracy=model_data["accuracy"],
        latency_ms=model_data["latency_ms"],
        free_tier=model_data["free_tier"]
    )

    return DirectAccessResponse(
        status="provisioned",
        endpoint=f"/v1/sentiment/{model_data['id']}",
        api_key=api_key,
        model=model_info,
        pricing=model_data["pricing"],
        expires_at=None
    )


@router.get("/models", response_model=List[ModelListItem])
async def list_available_models(
    task: Optional[str] = None,
    priority: Optional[str] = None,
    language: Optional[str] = None
):
    models = []

    for task_type, task_models in AVAILABLE_MODELS.items():
        if task and task != task_type:
            continue

        for model_id, model_data in task_models.items():
            if language and language not in model_data["languages"] and "multilingual" not in model_data["languages"]:
                continue

            models.append(ModelListItem(
                id=model_data["id"],
                name=model_data["name"],
                description=model_data["description"],
                task=model_data["task"],
                accuracy=model_data["accuracy"],
                latency_ms=model_data["latency_ms"],
                free_tier=model_data["free_tier"],
                pricing=model_data["pricing"],
                languages=model_data["languages"]
            ))

    if priority:
        priority_weights = {"speed": "latency_ms", "accuracy": "accuracy", "cost": "free_tier"}
        sort_key = priority_weights.get(priority, "latency_ms")

        if sort_key == "accuracy":
            models.sort(key=lambda x: x.accuracy, reverse=True)
        elif sort_key == "latency_ms":
            models.sort(key=lambda x: x.latency_ms)
        else:
            models.sort(key=lambda x: x.free_tier, reverse=True)

    return models


@router.get("/keys", response_model=List[ApiKeyInfo])
async def list_api_keys(current_user: User = Depends(get_current_user)):
    keys = await mongodb.database["direct_access_keys"].find({
        "user_id": current_user.id
    }).to_list(None)

    result = []
    for key in keys:
        result.append(ApiKeyInfo(
            id=str(key["_id"]),
            api_key=key["api_key"],
            model_id=key["model_id"],
            model_name=key["model_name"],
            task=key["task"],
            usage_plan=key["usage_plan"],
            free_tier_limit=key["free_tier_limit"],
            requests_used=key["requests_used"],
            requests_this_month=key["requests_this_month"],
            rate_limit=key["rate_limit"],
            status=key["status"],
            created_at=key["created_at"].isoformat(),
            last_used_at=key["last_used_at"].isoformat() if key.get("last_used_at") else None
        ))

    return result


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    if not ObjectId.is_valid(key_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key ID"
        )

    key = await mongodb.database["direct_access_keys"].find_one({
        "_id": ObjectId(key_id),
        "user_id": current_user.id
    })

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    await mongodb.database["direct_access_keys"].update_one(
        {"_id": ObjectId(key_id)},
        {"$set": {"status": "revoked"}}
    )

    return None

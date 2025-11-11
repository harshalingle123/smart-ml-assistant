from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.mongodb import mongodb
from app.models.mongodb_models import User, Model
from app.schemas.model_schemas import ModelCreate, ModelResponse
from app.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    current_user: User = Depends(get_current_user),
):
    new_model = Model(
        user_id=current_user.id,
        name=model_data.name,
        base_model=model_data.base_model,
        version=model_data.version,
        accuracy=model_data.accuracy,
        f1_score=model_data.f1_score,
        loss=model_data.loss,
        status=model_data.status,
        dataset_id=model_data.dataset_id,
    )

    result = await mongodb.database["models"].insert_one(new_model.dict(by_alias=True))
    new_model.id = result.inserted_id

    return ModelResponse(**new_model.dict(by_alias=True))


@router.get("", response_model=List[ModelResponse])
async def get_models(
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    models_cursor = mongodb.database["models"].find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).skip(offset).limit(limit)
    models = await models_cursor.to_list(length=limit)
    return [ModelResponse(**model) for model in models]


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
):
    model = await mongodb.database["models"].find_one(
        {"_id": ObjectId(model_id), "user_id": current_user.id}
    )

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    return ModelResponse(**model)

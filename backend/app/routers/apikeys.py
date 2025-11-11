from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import secrets
from app.mongodb import mongodb
from app.models.mongodb_models import User, ApiKey, Model
from app.schemas.apikey_schemas import ApiKeyCreate, ApiKeyResponse
from app.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/apikeys", tags=["API Keys"])


def generate_api_key() -> str:
    return f"sk-{secrets.token_urlsafe(32)}"


@router.post("", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    apikey_data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
):
    model = await mongodb.database["models"].find_one(
        {"_id": apikey_data.model_id, "user_id": current_user.id}
    )

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    api_key_value = generate_api_key()

    new_apikey = ApiKey(
        user_id=current_user.id,
        model_id=apikey_data.model_id,
        key=api_key_value,
        name=apikey_data.name,
    )

    result = await mongodb.database["apikeys"].insert_one(new_apikey.dict(by_alias=True))
    new_apikey.id = result.inserted_id

    return ApiKeyResponse(**new_apikey.dict(by_alias=True))


@router.get("", response_model=List[ApiKeyResponse])
async def get_api_keys(
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    apikeys_cursor = mongodb.database["apikeys"].find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).skip(offset).limit(limit)
    apikeys = await apikeys_cursor.to_list(length=limit)
    return [ApiKeyResponse(**apikey) for apikey in apikeys]


@router.delete("/{apikey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    apikey_id: str,
    current_user: User = Depends(get_current_user),
):
    apikey = await mongodb.database["apikeys"].find_one(
        {"_id": ObjectId(apikey_id), "user_id": current_user.id}
    )

    if not apikey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    await mongodb.database["apikeys"].delete_one({"_id": ObjectId(apikey_id)})

    return None

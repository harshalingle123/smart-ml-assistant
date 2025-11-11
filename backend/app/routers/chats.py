from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.mongodb import mongodb
from app.models.mongodb_models import User, Chat
from app.schemas.chat_schemas import ChatCreate, ChatUpdate, ChatResponse
from app.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/chats", tags=["Chats"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
):
    new_chat = Chat(
        user_id=current_user.id,
        title=chat_data.title,
        model_id=chat_data.model_id,
        dataset_id=chat_data.dataset_id,
    )

    result = await mongodb.database["chats"].insert_one(new_chat.dict(by_alias=True))
    new_chat.id = result.inserted_id

    return ChatResponse(**new_chat.dict(by_alias=True))


@router.get("", response_model=List[ChatResponse])
async def get_chats(
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    chats_cursor = mongodb.database["chats"].find(
        {"user_id": current_user.id}
    ).sort("last_updated", -1).skip(offset).limit(limit)
    chats = await chats_cursor.to_list(length=limit)
    return [ChatResponse(**chat) for chat in chats]


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
):
    chat = await mongodb.database["chats"].find_one(
        {"_id": ObjectId(chat_id), "user_id": current_user.id}
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    return ChatResponse(**chat)


@router.patch("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: str,
    chat_data: ChatUpdate,
    current_user: User = Depends(get_current_user),
):
    update_data = chat_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    result = await mongodb.database["chats"].update_one(
        {"_id": ObjectId(chat_id), "user_id": current_user.id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or no changes made"
        )

    updated_chat = await mongodb.database["chats"].find_one({"_id": ObjectId(chat_id)})
    return ChatResponse(**updated_chat)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
):
    result = await mongodb.database["chats"].delete_one(
        {"_id": ObjectId(chat_id), "user_id": current_user.id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    return None

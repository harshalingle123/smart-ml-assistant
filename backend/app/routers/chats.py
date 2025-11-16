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
    try:
        # Validate and convert chat_id to ObjectId
        try:
            chat_oid = ObjectId(chat_id)
        except Exception as e:
            print(f"Invalid chat ID format: {chat_id}, error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chat ID format: {chat_id}"
            )

        print(f"Attempting to delete chat: {chat_id} for user: {current_user.id}")

        # Delete the chat
        result = await mongodb.database["chats"].delete_one(
            {"_id": chat_oid, "user_id": current_user.id}
        )

        print(f"Delete result: deleted_count={result.deleted_count}")

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found or you don't have permission to delete it"
            )

        # Also delete all messages in this chat
        messages_result = await mongodb.database["messages"].delete_many(
            {"chat_id": chat_oid}
        )
        print(f"Deleted {messages_result.deleted_count} messages from chat")

        print(f"Successfully deleted chat: {chat_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat: {str(e)}"
        )

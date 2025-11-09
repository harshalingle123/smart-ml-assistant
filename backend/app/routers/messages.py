from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.mongodb import mongodb
from app.models.mongodb_models import User, Message, Chat
from app.schemas.message_schemas import MessageCreate, MessageResponse
from app.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/messages", tags=["Messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
):
    chat = await mongodb.database["chats"].find_one(
        {"_id": message_data.chat_id, "user_id": current_user.id}
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    new_message = Message(
        chat_id=message_data.chat_id,
        role=message_data.role,
        content=message_data.content,
        query_type=message_data.query_type,
        charts=message_data.charts,
    )

    result = await mongodb.database["messages"].insert_one(new_message.dict(by_alias=True))
    new_message.id = result.inserted_id

    return MessageResponse(**new_message.dict(by_alias=True))


@router.get("/chat/{chat_id}", response_model=List[MessageResponse])
async def get_messages_by_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    chat = await mongodb.database["chats"].find_one(
        {"_id": ObjectId(chat_id), "user_id": current_user.id}
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    messages_cursor = mongodb.database["messages"].find(
        {"chat_id": ObjectId(chat_id)}
    ).sort("timestamp", 1).skip(offset).limit(limit)
    messages = await messages_cursor.to_list(length=limit)
    return [MessageResponse(**message) for message in messages]


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
):
    message = await mongodb.database["messages"].find_one({"_id": ObjectId(message_id)})

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    chat = await mongodb.database["chats"].find_one(
        {"_id": message["chat_id"], "user_id": current_user.id}
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    return MessageResponse(**message)

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.mongodb_models import PyObjectId


class ChatCreate(BaseModel):
    title: str
    model_id: Optional[PyObjectId] = None
    dataset_id: Optional[PyObjectId] = None


class ChatUpdate(BaseModel):
    title: Optional[str] = None
    model_id: Optional[PyObjectId] = None
    dataset_id: Optional[PyObjectId] = None


class ChatResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    title: str
    model_id: Optional[PyObjectId] = None
    dataset_id: Optional[PyObjectId] = None
    last_updated: datetime

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}

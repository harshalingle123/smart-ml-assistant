from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from app.models.mongodb_models import PyObjectId


class MessageCreate(BaseModel):
    chat_id: PyObjectId
    role: str
    content: str
    query_type: Optional[str] = None
    charts: Optional[Any] = None


class MessageResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    chat_id: PyObjectId
    role: str
    content: str
    query_type: Optional[str] = None
    charts: Optional[Any] = None
    timestamp: datetime

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}

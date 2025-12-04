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
    metadata: Optional[Any] = None  # For storing dataset search results and other metadata
    kaggle_datasets: Optional[Any] = None  # For agent dataset recommendations
    huggingface_datasets: Optional[Any] = None  # For agent HuggingFace dataset recommendations
    huggingface_models: Optional[Any] = None  # For agent HuggingFace model recommendations
    downloadable_datasets: Optional[Any] = None  # For dataset download functionality

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}
        populate_by_name = True

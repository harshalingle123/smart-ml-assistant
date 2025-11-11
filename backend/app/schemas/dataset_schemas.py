from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from app.models.mongodb_models import PyObjectId


class DatasetCreate(BaseModel):
    name: str
    file_name: str
    row_count: int
    column_count: int
    file_size: int
    status: str = "processing"
    preview_data: Optional[Any] = None


class DatasetResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    name: str
    file_name: str
    row_count: int
    column_count: int
    file_size: int
    status: str
    preview_data: Optional[Any] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}

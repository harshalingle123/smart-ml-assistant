from pydantic import BaseModel, Field
from datetime import datetime
from app.models.mongodb_models import PyObjectId


class ApiKeyCreate(BaseModel):
    model_id: PyObjectId
    name: str


class ApiKeyResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    model_id: PyObjectId
    key: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}

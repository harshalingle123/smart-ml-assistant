from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.mongodb_models import PyObjectId


class ModelCreate(BaseModel):
    name: str
    base_model: str
    version: str
    accuracy: Optional[str] = None
    f1_score: Optional[str] = None
    loss: Optional[str] = None
    status: str = "ready"
    dataset_id: Optional[PyObjectId] = None
    azure_model_url: Optional[str] = None


class ModelResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    name: str
    base_model: str
    version: str
    accuracy: Optional[str] = None
    f1_score: Optional[str] = None
    loss: Optional[str] = None
    status: str
    dataset_id: Optional[PyObjectId] = None
    created_at: datetime
    azure_model_url: Optional[str] = Field(default=None, serialization_alias="azureModelUrl")

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}
        populate_by_name = True

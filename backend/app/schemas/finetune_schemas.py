from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.mongodb_models import PyObjectId


class FineTuneJobCreate(BaseModel):
    dataset_id: PyObjectId
    base_model: str
    model_id: Optional[PyObjectId] = None
    status: str = "preparing"
    progress: int = 0
    current_step: Optional[str] = None
    logs: Optional[str] = None

    class Config:
        protected_namespaces = ()


class FineTuneJobResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    model_id: Optional[PyObjectId] = None
    dataset_id: PyObjectId
    base_model: str
    status: str
    progress: int
    current_step: Optional[str] = None
    logs: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}
        protected_namespaces = ()

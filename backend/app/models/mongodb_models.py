from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(cls.validate),
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: JsonSchemaValue) -> None:
        field_schema.update(type="string")


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr = Field(...)
    name: str = Field(...)
    password: str = Field(...)
    current_plan: str = Field(default="free")
    queries_used: int = Field(default=0)
    fine_tune_jobs: int = Field(default=0)
    datasets_count: int = Field(default=0)
    billing_cycle: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Chat(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    title: str = Field(...)
    model_id: Optional[PyObjectId] = None
    dataset_id: Optional[PyObjectId] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Message(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    chat_id: PyObjectId = Field(...)
    role: str = Field(...)
    content: str = Field(...)
    query_type: Optional[str] = None
    charts: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Model(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    name: str = Field(...)
    base_model: str = Field(...)
    version: str = Field(...)
    accuracy: Optional[str] = None
    f1_score: Optional[str] = None
    loss: Optional[str] = None
    status: str = Field(default="ready")
    dataset_id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Dataset(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    name: str = Field(...)
    file_name: str = Field(...)
    row_count: int = Field(...)
    column_count: int = Field(...)
    file_size: int = Field(...)
    status: str = Field(default="processing")
    preview_data: Optional[Any] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class FineTuneJob(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    model_id: Optional[PyObjectId] = None
    dataset_id: PyObjectId = Field(...)
    base_model: str = Field(...)
    status: str = Field(default="preparing")
    progress: int = Field(default=0)
    current_step: Optional[str] = None
    logs: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ApiKey(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    model_id: PyObjectId = Field(...)
    key: str = Field(...)
    name: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

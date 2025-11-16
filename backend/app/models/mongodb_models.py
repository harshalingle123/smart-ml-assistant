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
        populate_by_name = True
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
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()


class Message(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    chat_id: PyObjectId = Field(...)
    role: str = Field(...)
    content: str = Field(...)
    query_type: Optional[str] = None
    charts: Optional[Any] = None
    metadata: Optional[dict] = None  # For storing agent function calls, datasets, etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
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
        populate_by_name = True
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
    source: Optional[str] = None
    kaggle_ref: Optional[str] = None
    huggingface_dataset_id: Optional[str] = None
    huggingface_url: Optional[str] = None
    download_path: Optional[str] = None
    schema: Optional[List[Any]] = Field(default=None)
    sample_data: Optional[List[Any]] = Field(default=None)
    target_column: Optional[str] = Field(default=None)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()


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
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()


class ApiKey(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    model_id: PyObjectId = Field(...)
    key: str = Field(...)
    name: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()


class TrainingJob(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    dataset_id: PyObjectId = Field(...)
    model_id: str = Field(...)
    base_model: str = Field(...)
    status: str = Field(default="queued")
    progress: int = Field(default=0)
    current_step: Optional[str] = None
    estimated_cost: float = Field(default=0.0)
    estimated_duration_minutes: int = Field(default=60)
    hyperparameters: Optional[Any] = None
    metrics: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()


class PrebuiltModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    description: str = Field(...)
    task_type: str = Field(...)
    model_id: str = Field(...)
    languages: List[str] = Field(default_factory=list)
    performance_metrics: Any = Field(default_factory=dict)
    use_cases: List[str] = Field(default_factory=list)
    example_input: str = Field(...)
    example_output: str = Field(...)
    deployment_ready: bool = Field(default=True)
    cost_per_1k_requests: float = Field(default=0.0)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()


class Deployment(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    model_type: str = Field(...)
    model_id: str = Field(...)
    name: str = Field(...)
    description: Optional[str] = None
    status: str = Field(default="deploying")
    endpoint_url: str = Field(...)
    api_key: str = Field(...)
    environment: str = Field(default="production")
    auto_scale: bool = Field(default=True)
    requests_count: int = Field(default=0)
    last_request_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()


class DirectAccessKey(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    api_key: str = Field(...)
    model_id: str = Field(...)
    model_name: str = Field(...)
    task: str = Field(...)
    subtask: Optional[str] = None
    usage_plan: str = Field(default="free")
    free_tier_limit: int = Field(default=10000)
    requests_used: int = Field(default=0)
    requests_this_month: int = Field(default=0)
    rate_limit: int = Field(default=10)
    status: str = Field(default="active")
    priority: str = Field(default="speed")
    language: str = Field(default="en")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    last_reset_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()


class ModelUsage(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    api_key_id: PyObjectId = Field(...)
    user_id: PyObjectId = Field(...)
    model_id: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: int = Field(...)
    status: str = Field(...)
    cost: float = Field(default=0.0)
    request_id: str = Field(...)
    batch_size: int = Field(default=1)
    error_message: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()


class AlertConfig(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    api_key_id: PyObjectId = Field(...)
    threshold: int = Field(...)
    alert_type: str = Field(...)
    recipient: str = Field(...)
    enabled: bool = Field(default=True)
    last_triggered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

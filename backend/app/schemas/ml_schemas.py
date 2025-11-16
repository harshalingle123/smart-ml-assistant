from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.mongodb_models import PyObjectId


class ModelSearchRequest(BaseModel):
    query: Optional[str] = None
    task: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    sort: str = Field(default="downloads")


class ModelCompareRequest(BaseModel):
    model_ids: List[str] = Field(..., min_length=2, max_length=5)

    class Config:
        protected_namespaces = ()


class ModelResponse(BaseModel):
    model_id: str
    name: str
    author: str
    downloads: int
    likes: int
    tags: List[str]
    pipeline_tag: str
    library_name: str
    created_at: str
    last_modified: str

    class Config:
        protected_namespaces = ()


class ModelDetailsResponse(ModelResponse):
    languages: List[str] = []
    datasets: List[str] = []
    metrics: List[str] = []
    model_type: str = ""
    parameters: str = ""
    description: str = ""

    class Config:
        protected_namespaces = ()


class TrainingJobCreate(BaseModel):
    dataset_id: str
    model_id: str
    base_model: str
    hyperparameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

    class Config:
        protected_namespaces = ()


class TrainingJobResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    dataset_id: PyObjectId
    model_id: str
    base_model: str
    status: str
    progress: int
    current_step: Optional[str] = None
    estimated_cost: float
    estimated_duration_minutes: int
    hyperparameters: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}
        protected_namespaces = ()


class TrainingJobUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    current_step: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None


class PrebuiltModelResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    description: str
    task_type: str
    model_id: str
    languages: List[str]
    performance_metrics: Dict[str, float]
    use_cases: List[str]
    example_input: str
    example_output: str
    deployment_ready: bool
    cost_per_1k_requests: float

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}
        protected_namespaces = ()


class PrebuiltModelTestRequest(BaseModel):
    input_text: str


class PrebuiltModelTestResponse(BaseModel):
    model_id: str
    input: str
    output: Any
    processing_time_ms: float
    model_name: str

    class Config:
        protected_namespaces = ()


class DeploymentCreate(BaseModel):
    model_type: str = Field(..., description="prebuilt or trained")
    model_id: str
    name: str
    description: Optional[str] = None
    environment: str = Field(default="production")
    auto_scale: bool = Field(default=True)

    class Config:
        protected_namespaces = ()


class DeploymentResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    model_type: str
    model_id: str
    name: str
    description: Optional[str] = None
    status: str
    endpoint_url: str
    api_key: str
    environment: str
    auto_scale: bool
    requests_count: int
    last_request_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}
        protected_namespaces = ()


class DeploymentPredictRequest(BaseModel):
    input_data: Any
    parameters: Optional[Dict[str, Any]] = None


class DeploymentPredictResponse(BaseModel):
    deployment_id: str
    prediction: Any
    confidence: Optional[float] = None
    processing_time_ms: float
    timestamp: datetime


class MLRecommendationRequest(BaseModel):
    task_description: str
    dataset_id: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    budget: Optional[float] = None
    priority: str = Field(default="balanced", description="speed, cost, or accuracy")


class MLRecommendationResponse(BaseModel):
    recommended_models: List[Dict[str, Any]]
    reasoning: str
    estimated_cost: float
    estimated_accuracy: str
    training_required: bool
    prebuilt_alternative: Optional[str] = None


class MLDecisionRequest(BaseModel):
    task_description: str
    dataset_id: str
    constraints: Optional[Dict[str, Any]] = None


class MLDecisionResponse(BaseModel):
    decision: str
    selected_model: Dict[str, Any]
    reasoning: str
    confidence_score: float
    alternatives: List[Dict[str, Any]]
    next_steps: List[str]

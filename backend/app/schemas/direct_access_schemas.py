from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DirectAccessRequest(BaseModel):
    task: str = Field(..., description="Task type: sentiment, classification, object-detection, translation")
    subtask: Optional[str] = Field(None, description="Subtask: reviews, spam, general, documents")
    usage: str = Field(..., description="Usage: testing, 100/day, 1000/day, 10000/day")
    language: str = Field(default="en", description="Language: en, es, fr, multilingual")
    priority: str = Field(default="speed", description="Priority: speed, accuracy, cost")


class ModelInfo(BaseModel):
    id: str
    name: str
    accuracy: float
    latency_ms: int
    free_tier: int


class DirectAccessResponse(BaseModel):
    status: str
    endpoint: str
    api_key: str
    model: ModelInfo
    pricing: str
    expires_at: Optional[str] = None


class PredictionRequest(BaseModel):
    text: str = Field(..., description="Text to analyze")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional options")


class BatchPredictionRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to analyze")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional options")


class SentimentScore(BaseModel):
    label: str
    compound: float
    pos: float
    neu: float
    neg: float


class UsageInfo(BaseModel):
    requests_used: int
    requests_remaining: int
    reset_date: str


class PredictionResponse(BaseModel):
    text: str
    sentiment: SentimentScore
    confidence: float
    latency_ms: int
    timestamp: str
    request_id: str
    usage: UsageInfo


class BatchPredictionResponse(BaseModel):
    sentiments: List[SentimentScore]
    latency_ms: int
    timestamp: str
    request_id: str
    usage: UsageInfo


class ApiKeyInfo(BaseModel):
    id: str
    api_key: str
    model_id: str
    model_name: str
    task: str
    usage_plan: str
    free_tier_limit: int
    requests_used: int
    requests_this_month: int
    rate_limit: int
    status: str
    created_at: str
    last_used_at: Optional[str] = None


class ModelListItem(BaseModel):
    id: str
    name: str
    description: str
    task: str
    accuracy: float
    latency_ms: int
    free_tier: int
    pricing: str
    languages: List[str]


class UsageStats(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_latency_ms: float
    by_model: Dict[str, Any]
    time_series: List[Dict[str, Any]]


class CostBreakdown(BaseModel):
    current_month: Dict[str, Any]
    projected_month: Dict[str, Any]
    by_model: Dict[str, Any]


class AlertConfigRequest(BaseModel):
    api_key_id: str
    threshold: int
    alert_type: str = Field(..., description="Type: email, webhook")
    recipient: str

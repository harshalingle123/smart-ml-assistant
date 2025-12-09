from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PlanResponse(BaseModel):
    """Response model for subscription plans"""
    id: str
    plan: str
    name: str
    description: Optional[str] = None
    price_monthly: float
    currency: str
    api_hits_per_month: int
    model_generation_per_day: int
    dataset_size_mb: int
    azure_storage_gb: float  # Changed from int to float to support 0.1 GB for free plan
    training_time_minutes_per_model: int
    concurrent_trainings: int
    features: List[str]
    priority_support: bool
    razorpay_plan_id: Optional[str] = None
    is_active: bool


class SubscriptionResponse(BaseModel):
    """Response model for user subscription"""
    id: str
    user_id: str
    plan: str
    provider: str
    status: str
    period_start: datetime
    period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None
    amount: float
    currency: str
    last_payment_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    razorpay_subscription_id: Optional[str] = None


class CreateSubscriptionRequest(BaseModel):
    """Request to create a new subscription"""
    plan: str  # "pro" | "advanced"


class CreateOrderRequest(BaseModel):
    """Request to create a Razorpay order"""
    plan: str  # "pro" | "advanced"


class CreateOrderResponse(BaseModel):
    """Response with Razorpay order details"""
    order_id: str
    amount: float
    currency: str
    key_id: str
    plan: str


class VerifyPaymentRequest(BaseModel):
    """Request to verify Razorpay payment"""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription"""
    cancel_at_period_end: bool = True
    reason: Optional[str] = None


class UsageResponse(BaseModel):
    """Response with user usage statistics"""
    user_id: str
    subscription_id: str
    plan: str
    api_hits_used: int
    api_hits_limit: int
    models_trained_today: int
    models_limit_per_day: int
    azure_storage_used_mb: float
    azure_storage_limit_gb: int
    billing_cycle_start: datetime
    billing_cycle_end: datetime
    usage_percentage: dict  # {"api_hits": 45.2, "models": 20.0, "storage": 10.5}


class PaymentHistoryResponse(BaseModel):
    """Response with payment history"""
    id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    razorpay_payment_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


class SubscriptionWebhookRequest(BaseModel):
    """Razorpay webhook payload"""
    event: str
    payload: dict

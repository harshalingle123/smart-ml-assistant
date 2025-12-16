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

    # Subscription fields
    subscription_id: Optional[PyObjectId] = None  # Reference to subscriptions collection
    current_plan: str = Field(default="free")  # Cached for quick access: "free" | "pro" | "advanced"
    queries_used: int = Field(default=0)  # DEPRECATED: Use UsageRecord instead
    fine_tune_jobs: int = Field(default=0)  # DEPRECATED: Use UsageRecord instead
    datasets_count: int = Field(default=0)  # DEPRECATED: Use UsageRecord instead
    billing_cycle: Optional[str] = None  # DEPRECATED: Use Subscription.period_start/end

    # Admin & Roles
    is_admin: bool = Field(default=False)  # Admin access for managing plans, promo codes, etc.

    # Authentication & Verification Fields
    email_verified: bool = Field(default=False)
    auth_provider: str = Field(default="email")  # "email", "google", "github", etc.
    oauth_id: Optional[str] = None  # Google ID, GitHub ID, etc.
    account_status: str = Field(default="pending")  # "pending", "active", "suspended", "locked"
    failed_login_attempts: int = Field(default=0)
    last_login_attempt: Optional[datetime] = None
    account_locked_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None

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
    version: str = Field(default="v1")
    azure_blob_path: Optional[str] = None  # Azure blob path (e.g., user_id/model_id/model-v1.zip)
    azure_model_url: Optional[str] = None  # DEPRECATED: Legacy field for backward compatibility
    task_type: Optional[str] = None  # "classification" or "regression"
    accuracy: Optional[str] = None
    f1_score: Optional[str] = None
    loss: Optional[str] = None
    status: str = Field(default="ready")
    dataset_id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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
    azure_blob_path: Optional[str] = None  # Azure blob path (e.g., user_id/dataset_id/file.csv)
    azure_dataset_url: Optional[str] = None  # DEPRECATED: Legacy field for backward compatibility
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = None  # "upload", "kaggle", "huggingface"
    kaggle_ref: Optional[str] = None
    huggingface_dataset_id: Optional[str] = None
    huggingface_url: Optional[str] = None
    target_column: Optional[str] = Field(default=None)  # Metadata only

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


class Subscription(BaseModel):
    """User subscription details"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    plan: str = Field(...)  # "free" | "pro" | "advanced"
    provider: str = Field(default="razorpay")  # "razorpay" | "stripe" | "manual"
    status: str = Field(default="active")  # "active" | "canceled" | "past_due" | "expired"

    # Razorpay specific fields
    razorpay_subscription_id: Optional[str] = None
    razorpay_customer_id: Optional[str] = None
    razorpay_plan_id: Optional[str] = None

    # Billing cycle
    period_start: datetime = Field(default_factory=datetime.utcnow)
    period_end: datetime = Field(...)
    cancel_at_period_end: bool = Field(default=False)
    canceled_at: Optional[datetime] = None

    # Payment tracking
    amount: float = Field(default=0.0)  # Amount in INR
    currency: str = Field(default="INR")
    last_payment_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Plan(BaseModel):
    """Subscription plan details - supports standard, custom, and enterprise plans"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    plan: str = Field(...)  # "free" | "pro" | "advanced" | "custom_plan_slug"
    name: str = Field(...)
    description: Optional[str] = None

    # Pricing
    price_monthly: float = Field(default=0.0)  # Price in INR
    currency: str = Field(default="INR")

    # Limits
    api_hits_per_month: int = Field(...)
    model_generation_per_day: int = Field(...)
    dataset_size_mb: int = Field(...)
    azure_storage_gb: int = Field(...)
    training_time_minutes_per_model: int = Field(...)
    concurrent_trainings: int = Field(default=1)

    # Labeling Limits
    labeling_files_per_month: int = Field(default=50)  # Max files to label per month
    labeling_file_size_mb: int = Field(default=10)  # Max file size for labeling

    # Features
    features: List[str] = Field(default_factory=list)
    priority_support: bool = Field(default=False)

    # Razorpay plan ID
    razorpay_plan_id: Optional[str] = None

    # Custom Plan Fields (Admin-created plans)
    is_custom: bool = Field(default=False)  # True if admin-created custom plan
    created_by_admin_id: Optional[PyObjectId] = None  # Admin who created this plan
    plan_type: str = Field(default="standard")  # "standard" | "custom" | "enterprise"

    # Enterprise Custom Plans (Private plans)
    is_private: bool = Field(default=False)  # True if visible only to specific users
    allowed_user_ids: List[PyObjectId] = Field(default_factory=list)  # Users who can see this plan
    contract_details: Optional[str] = None  # Custom contract terms for enterprise
    billing_contact_email: Optional[str] = None  # Enterprise billing contact

    # Display & Organization
    display_order: int = Field(default=0)  # For sorting plans in UI (lower = higher priority)
    is_archived: bool = Field(default=False)  # Soft delete for old plans
    valid_from: Optional[datetime] = None  # When plan becomes available
    valid_until: Optional[datetime] = None  # When plan expires (for limited-time offers)

    # Metadata
    tags: List[str] = Field(default_factory=list)  # ["enterprise", "startup", "student"]
    internal_notes: Optional[str] = None  # Admin notes not visible to users

    # Status
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UsageRecord(BaseModel):
    """Track user usage for billing and limits"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    subscription_id: Optional[PyObjectId] = None  # None for free plan users

    # Usage counters (monthly reset)
    api_hits_used: int = Field(default=0)
    models_trained_today: int = Field(default=0)
    azure_storage_used_mb: float = Field(default=0.0)
    labeling_files_used: int = Field(default=0)  # Files labeled this month

    # Composite Limits (Base plan + Add-ons) - Cached for performance
    composite_limits: Optional[dict] = None  # Calculated limits including add-ons
    # Example: {
    #   "api_hits_per_month": 15000,  # base 10000 + addon 5000
    #   "azure_storage_gb": 15,        # base 10 + addon 5
    #   "model_generation_per_day": 30 # base 25 + addon 5
    # }
    last_limits_recalculation: datetime = Field(default_factory=datetime.utcnow)  # TTL: 1 hour

    # Tracking
    billing_cycle_start: datetime = Field(default_factory=datetime.utcnow)
    billing_cycle_end: datetime = Field(...)
    last_reset_at: datetime = Field(default_factory=datetime.utcnow)
    last_daily_reset_at: datetime = Field(default_factory=datetime.utcnow)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Payment(BaseModel):
    """Payment transaction record - supports subscriptions, add-ons, and promo codes"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    subscription_id: Optional[PyObjectId] = None

    # Payment details
    amount: float = Field(...)  # Final amount paid (after discount)
    currency: str = Field(default="INR")
    status: str = Field(...)  # "pending" | "success" | "failed" | "refunded"
    payment_method: str = Field(...)  # "upi" | "card" | "netbanking" | "wallet"

    # Razorpay details
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_signature: Optional[str] = None

    # Promo Code Tracking
    promo_code_id: Optional[PyObjectId] = None  # Reference to promo_codes collection
    promo_code: Optional[str] = None  # Denormalized code for easy display
    discount_applied: float = Field(default=0.0)  # Discount amount
    original_amount: Optional[float] = None  # Amount before discount

    # Add-on Tracking
    addon_id: Optional[PyObjectId] = None  # If payment is for an add-on
    payment_type: str = Field(default="subscription")  # "subscription" | "addon" | "renewal"

    # Additional info
    description: Optional[str] = None
    failure_reason: Optional[str] = None
    refund_amount: Optional[float] = None
    refunded_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Addon(BaseModel):
    """Purchasable add-ons for subscription plans (e.g., extra storage, API boosts)"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # Basic Info
    addon_slug: str = Field(...)  # "extra_storage_5gb", "api_boost_10k", "priority_support"
    name: str = Field(...)  # "Extra 5GB Storage"
    description: str = Field(...)  # Detailed description of what this add-on provides
    category: str = Field(...)  # "storage" | "api_hits" | "training" | "support"

    # Pricing
    price_monthly: float = Field(...)
    price_annual: Optional[float] = None  # Discounted annual price (if applicable)
    currency: str = Field(default="INR")

    # What it provides
    quota_type: str = Field(...)  # "azure_storage_gb" | "api_hits_per_month" | "model_generation_per_day"
    quota_amount: float = Field(...)  # How much it adds (e.g., 5 for 5GB)

    # Availability
    compatible_plans: List[str] = Field(default_factory=list)  # ["pro", "advanced"] or [] for all plans
    max_quantity: int = Field(default=10)  # Max user can purchase (e.g., 10x storage addon)
    is_active: bool = Field(default=True)

    # Display
    icon: Optional[str] = None  # Icon name for UI (e.g., "HardDrive", "Zap")
    badge_text: Optional[str] = None  # "Most Popular", "Best Value", etc.
    display_order: int = Field(default=0)  # For sorting in UI

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserAddon(BaseModel):
    """User's active add-on subscriptions"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # References
    user_id: PyObjectId = Field(...)
    subscription_id: PyObjectId = Field(...)  # Main subscription this is attached to
    addon_id: PyObjectId = Field(...)

    # Purchase Details
    quantity: int = Field(default=1)  # How many of this addon they bought
    amount_paid: float = Field(...)  # Amount paid for this add-on
    currency: str = Field(default="INR")

    # Razorpay
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None

    # Status
    status: str = Field(default="active")  # "active" | "canceled" | "expired"
    period_start: datetime = Field(default_factory=datetime.utcnow)
    period_end: datetime = Field(...)  # Typically 30 days from start
    auto_renew: bool = Field(default=True)  # Auto-renew at period end
    canceled_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class PromoCode(BaseModel):
    """Promotional discount codes for subscriptions and add-ons"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # Code Details
    code: str = Field(...)  # "STUDENT50", "BLACKFRIDAY2025", etc. (stored uppercase)
    description: str = Field(...)  # "50% off for students"

    # Discount
    discount_type: str = Field(...)  # "percentage" | "fixed_amount"
    discount_value: float = Field(...)  # 50 for 50% or 100 for ₹100 off
    max_discount_amount: Optional[float] = None  # Cap for percentage discounts (e.g., max ₹500 off)

    # Applicability
    applicable_plans: List[str] = Field(default_factory=list)  # [] = all plans, ["pro", "advanced"] = specific
    applicable_addons: List[str] = Field(default_factory=list)  # [] = all addons, ["addon_slug"] = specific
    first_payment_only: bool = Field(default=False)  # True = only applies to first payment

    # Usage Limits
    usage_limit: Optional[int] = None  # Total times code can be used (None = unlimited)
    usage_count: int = Field(default=0)  # Times used so far
    per_user_limit: int = Field(default=1)  # Times each user can use (typically 1)

    # Validity
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None  # None = no expiry
    is_active: bool = Field(default=True)

    # Metadata
    created_by_admin_id: Optional[PyObjectId] = None  # Admin who created this code
    campaign_name: Optional[str] = None  # "Black Friday 2025", "Student Discount"
    internal_notes: Optional[str] = None  # Admin notes

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class PromoCodeUsage(BaseModel):
    """Track promo code usage by users for analytics and enforcement"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    promo_code_id: PyObjectId = Field(...)
    code: str = Field(...)  # Denormalized for easy lookup
    user_id: PyObjectId = Field(...)
    subscription_id: Optional[PyObjectId] = None
    payment_id: Optional[PyObjectId] = None

    # Discount Applied
    discount_amount: float = Field(...)  # Actual discount amount given
    original_amount: float = Field(...)  # Original price before discount
    final_amount: float = Field(...)  # Price after discount

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class WebhookEvent(BaseModel):
    """
    Webhook event logging for Razorpay webhooks
    Enables idempotent processing, retry logic, and audit trail
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # Event Identification (for idempotency)
    event_id: str = Field(...)  # Razorpay event ID (e.g., "event_xxxx")
    event_type: str = Field(...)  # "payment.captured", "payment.failed", "subscription.charged", etc.

    # Payload
    payload: dict = Field(...)  # Full webhook payload from Razorpay

    # Processing Status
    status: str = Field(default="pending")  # "pending" | "processing" | "processed" | "failed"
    processing_attempts: int = Field(default=0)  # Number of times we tried to process this
    max_retry_attempts: int = Field(default=3)  # Maximum retry attempts before giving up

    # Timestamps
    processed_at: Optional[datetime] = None  # When successfully processed
    next_retry_at: Optional[datetime] = None  # When to retry if failed

    # Error Tracking
    error_message: Optional[str] = None  # Last error message if processing failed
    error_stack: Optional[str] = None  # Full stack trace for debugging

    # Metadata
    source_ip: Optional[str] = None  # IP address of webhook sender (for security)
    signature_valid: bool = Field(default=True)  # Was signature verification successful

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DunningAttempt(BaseModel):
    """
    Track payment retry attempts (dunning) for failed payments
    Helps recover revenue from failed subscriptions
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # References
    subscription_id: PyObjectId = Field(...)
    user_id: PyObjectId = Field(...)
    payment_id: Optional[str] = None  # Failed Razorpay payment ID

    # Dunning Details
    attempt_number: int = Field(default=1)  # 1st, 2nd, 3rd retry
    status: str = Field(default="pending")  # "pending" | "attempted" | "success" | "failed" | "skipped"

    # Scheduling
    scheduled_at: datetime = Field(...)  # When this retry should happen
    attempted_at: Optional[datetime] = None  # When we actually tried

    # Result
    result_status: Optional[str] = None  # "success" | "failed" | "card_declined" | "insufficient_funds"
    error_message: Optional[str] = None
    razorpay_payment_id: Optional[str] = None  # New payment ID if retry succeeded

    # Communication
    email_sent: bool = Field(default=False)  # Did we send reminder email
    email_sent_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class LabelData(BaseModel):
    """Structured labeling result from Gemini"""
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    objects: Optional[List[dict]] = None  # {label, confidence, box_2d, location}
    topics: Optional[List[str]] = None
    events: Optional[List[dict]] = None  # {timestamp, description}
    entities: Optional[List[dict]] = None  # {name, type}
    safety_flags: Optional[List[str]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class LabelingFile(BaseModel):
    """Individual file within a labeling dataset"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    dataset_id: PyObjectId = Field(...)
    user_id: PyObjectId = Field(...)

    # File metadata
    filename: str = Field(...)
    original_name: str = Field(...)
    media_type: str = Field(...)  # "image" | "video" | "audio" | "text" | "pdf" | "unknown"
    file_size: int = Field(...)  # bytes
    azure_blob_path: str = Field(...)  # Azure storage path
    preview_url: Optional[str] = None  # For images/videos

    # Processing
    status: str = Field(default="pending")  # "pending" | "processing" | "completed" | "failed"
    result: Optional[LabelData] = None
    error_message: Optional[str] = None

    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class LabelingDataset(BaseModel):
    """Collection of files for labeling"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)

    # Dataset info
    name: str = Field(...)
    task: str = Field(...)  # "general_analysis" | "object_detection" | "sentiment_analysis" | etc.
    target_labels: Optional[List[str]] = None  # Constrained label vocabulary

    # Statistics
    total_files: int = Field(default=0)
    completed_files: int = Field(default=0)
    failed_files: int = Field(default=0)

    # Status
    status: str = Field(default="active")  # "active" | "completed" | "archived"

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

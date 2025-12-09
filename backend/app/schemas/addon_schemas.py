"""
Add-on Pydantic Schemas for Request/Response Models
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AddonResponse(BaseModel):
    """Response model for add-on product"""
    id: str
    addon_slug: str
    name: str
    description: str
    category: str
    price_monthly: float
    price_annual: Optional[float]
    currency: str
    quota_type: str
    quota_amount: float
    compatible_plans: List[str]
    max_quantity: int
    is_active: bool
    icon: Optional[str]
    badge_text: Optional[str]
    display_order: int


class UserAddonResponse(BaseModel):
    """Response model for user's active add-on"""
    id: str
    addon_id: str
    addon_name: str
    addon_description: str
    quantity: int
    amount_paid: float
    currency: str
    status: str
    period_start: datetime
    period_end: datetime
    auto_renew: bool
    quota_type: str
    quota_amount: float
    total_quota: float  # quantity * quota_amount


class PurchaseAddonRequest(BaseModel):
    """Request to purchase an add-on"""
    addon_slug: str
    quantity: int = 1


class CreateAddonOrderResponse(BaseModel):
    """Response with Razorpay order details for add-on"""
    order_id: str
    amount: float
    currency: str
    key_id: str
    addon_slug: str
    addon_name: str
    quantity: int
    total_price: float


class VerifyAddonPaymentRequest(BaseModel):
    """Request to verify add-on payment"""
    addon_slug: str
    quantity: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class CancelAddonRequest(BaseModel):
    """Request to cancel add-on"""
    user_addon_id: str
    immediate: bool = False  # False = cancel at period end, True = cancel immediately


class CombinedLimitsResponse(BaseModel):
    """User's total limits (base plan + all add-ons)"""
    user_id: str
    plan: str

    # Base plan limits
    base_limits: Dict[str, Any]

    # Add-on contributions
    addon_contributions: Dict[str, float]  # e.g., {"azure_storage_gb": 15, "api_hits_per_month": 10000}

    # Total combined limits
    total_limits: Dict[str, Any]

    # Active add-ons breakdown
    active_addons: List[UserAddonResponse]

    # Summary
    addon_count: int
    total_addon_cost: float


class AddonPaymentHistoryResponse(BaseModel):
    """Add-on payment record"""
    id: str
    addon_name: str
    quantity: int
    amount: float
    currency: str
    status: str
    razorpay_payment_id: Optional[str]
    created_at: datetime

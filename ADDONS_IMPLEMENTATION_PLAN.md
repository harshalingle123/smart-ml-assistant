# Add-ons System Implementation Plan

## Overview

This document provides a complete implementation plan for the subscription add-ons feature, allowing users to enhance their subscription plans with additional capabilities like extra storage, API boosts, and premium features.

---

## Table of Contents

1. [System Design](#system-design)
2. [Database Schema](#database-schema)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [Testing Plan](#testing-plan)
6. [Deployment Checklist](#deployment-checklist)

---

## System Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Action                          │
│           "Purchase Extra Storage (10 GB)"                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Billing Page)                    │
│  - Add-ons catalog with pricing                            │
│  - Purchase flow (Razorpay checkout)                       │
│  - Active add-ons management                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (/api/addons)                      │
│  - Create add-on order                                      │
│  - Verify payment                                           │
│  - Activate add-on                                          │
│  - Calculate combined limits (base + add-ons)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  MongoDB Collections                         │
│  - addon_products: Available add-ons catalog               │
│  - user_addons: Active user add-ons                        │
│  - addon_payments: Add-on payment records                  │
└─────────────────────────────────────────────────────────────┘
```

### Add-on Types

1. **Storage Add-ons**
   - Increment: `azure_storage_gb`
   - Stackable: Yes (can buy multiple)
   - Examples: +5GB, +10GB, +50GB

2. **API Boost Add-ons**
   - Increment: `api_hits_per_month`
   - Stackable: Yes
   - Examples: +5,000, +10,000, +50,000 calls

3. **Model Training Add-ons**
   - Increment: `model_generation_per_day`
   - Stackable: Yes
   - Examples: +10, +20, +50 models/day

4. **Feature Add-ons**
   - Increment: Enable specific features
   - Stackable: No (binary: on/off)
   - Examples: Priority Queue, Custom Domain, White Label

### Pricing Strategy

**Formula**: Add-on price should be 40-60% of next tier upgrade cost

Example:
- Pro: 5 GB storage, ₹499/month
- Advanced: 20 GB storage, ₹1,999/month
- Difference: 15 GB for ₹1,500
- Per GB: ₹100/GB
- Add-on (+10 GB): ₹199/month (50% cheaper than upgrading)

**Benefits**:
- Users get flexibility without full upgrade
- Company captures revenue from users who won't upgrade fully
- Creates upgrade path (buying multiple add-ons → suggests upgrade)

---

## Database Schema

### Collection: addon_products

```javascript
{
  _id: ObjectId("..."),
  addon_id: "extra_storage_10gb",         // Unique identifier
  name: "Extra Storage (10 GB)",          // Display name
  description: "Add 10 GB of Azure Blob Storage to your plan",
  type: "storage",                        // storage | api | models | feature
  category: "capacity",                   // capacity | performance | features
  price_monthly: 199.0,
  currency: "INR",

  // What this add-on provides
  increment: {
    azure_storage_gb: 10                  // Add 10 GB
  },

  // Eligibility
  available_for_plans: ["free", "pro"],   // Cannot buy on Advanced (already has 20GB)
  max_quantity: 10,                       // Max purchasable per user
  is_stackable: true,                     // Can buy multiple?

  // Metadata
  icon: "hard-drive",                     // Icon name (lucide-react)
  badge: "POPULAR",                       // Optional badge
  sort_order: 1,                          // Display order
  is_active: true,
  created_at: ISODate("2024-01-01T00:00:00Z"),
  updated_at: ISODate("2024-01-01T00:00:00Z")
}
```

### Collection: user_addons

```javascript
{
  _id: ObjectId("..."),
  user_id: ObjectId("..."),
  subscription_id: ObjectId("..."),       // Parent subscription
  addon_id: "extra_storage_10gb",         // Reference to addon_products

  // Subscription details
  status: "active",                       // active | canceled | expired
  quantity: 2,                            // If stackable, how many purchased

  // Billing
  amount_per_month: 199.0,
  total_amount: 398.0,                    // quantity × amount_per_month
  currency: "INR",

  // Period
  started_at: ISODate("2024-01-15T10:30:00Z"),
  current_period_start: ISODate("2024-01-15T00:00:00Z"),
  current_period_end: ISODate("2024-02-15T00:00:00Z"),

  // Cancellation
  cancel_at_period_end: false,
  canceled_at: null,

  // Razorpay
  razorpay_subscription_id: "sub_xxx",    // If recurring
  razorpay_plan_id: "plan_xxx",           // Add-on plan in Razorpay
  last_payment_at: ISODate("2024-01-15T10:30:00Z"),
  next_billing_date: ISODate("2024-02-15T00:00:00Z"),

  // Metadata
  created_at: ISODate("2024-01-15T10:30:00Z"),
  updated_at: ISODate("2024-01-15T10:30:00Z")
}
```

### Collection: addon_payments

```javascript
{
  _id: ObjectId("..."),
  user_id: ObjectId("..."),
  user_addon_id: ObjectId("..."),         // Reference to user_addons
  addon_id: "extra_storage_10gb",

  // Payment details
  amount: 398.0,                          // Total amount (quantity × price)
  currency: "INR",
  status: "success",                      // success | failed | pending
  payment_method: "upi",

  // Razorpay
  razorpay_payment_id: "pay_xxx",
  razorpay_order_id: "order_xxx",
  razorpay_signature: "...",

  // Metadata
  description: "Add-on: Extra Storage (10 GB) × 2",
  invoice_id: "INV-2024-001",             // Optional
  created_at: ISODate("2024-01-15T10:30:00Z")
}
```

### Database Indexes

```python
# addon_products
await db.addon_products.create_index("addon_id", unique=True)
await db.addon_products.create_index([("type", 1), ("is_active", 1)])
await db.addon_products.create_index("sort_order")

# user_addons
await db.user_addons.create_index("user_id")
await db.user_addons.create_index([("user_id", 1), ("status", 1)])
await db.user_addons.create_index("subscription_id")
await db.user_addons.create_index("addon_id")
await db.user_addons.create_index("razorpay_subscription_id")

# addon_payments
await db.addon_payments.create_index("user_id")
await db.addon_payments.create_index("user_addon_id")
await db.addon_payments.create_index("razorpay_payment_id")
await db.addon_payments.create_index([("created_at", -1)])  # For history
```

---

## Backend Implementation

### Step 1: Data Models

**File**: `backend/app/models/mongodb_models.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

class AddonProduct(BaseModel):
    """Add-on product definition"""
    addon_id: str
    name: str
    description: str
    type: str  # storage, api, models, feature
    category: str  # capacity, performance, features
    price_monthly: float
    currency: str = "INR"
    increment: Dict[str, Any]
    available_for_plans: List[str]
    max_quantity: int = 1
    is_stackable: bool = False
    icon: Optional[str] = None
    badge: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class UserAddon(BaseModel):
    """User's active add-on subscription"""
    user_id: ObjectId
    subscription_id: Optional[ObjectId] = None
    addon_id: str
    status: str = "active"
    quantity: int = 1
    amount_per_month: float
    total_amount: float
    currency: str = "INR"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    current_period_start: datetime = Field(default_factory=datetime.utcnow)
    current_period_end: datetime
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    razorpay_subscription_id: Optional[str] = None
    razorpay_plan_id: Optional[str] = None
    last_payment_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class AddonPayment(BaseModel):
    """Add-on payment record"""
    user_id: ObjectId
    user_addon_id: ObjectId
    addon_id: str
    amount: float
    currency: str = "INR"
    status: str = "success"
    payment_method: str
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    description: Optional[str] = None
    invoice_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
```

### Step 2: Pydantic Schemas

**File**: `backend/app/schemas/addon_schemas.py`

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AddonProductResponse(BaseModel):
    """Response for add-on product"""
    id: str
    addon_id: str
    name: str
    description: str
    type: str
    category: str
    price_monthly: float
    currency: str
    increment: Dict[str, Any]
    available_for_plans: List[str]
    max_quantity: int
    is_stackable: bool
    icon: Optional[str]
    badge: Optional[str]
    is_active: bool


class PurchaseAddonRequest(BaseModel):
    """Request to purchase add-on"""
    addon_id: str
    quantity: int = 1


class CreateAddonOrderResponse(BaseModel):
    """Response with Razorpay order details for add-on"""
    order_id: str
    amount: float
    currency: str
    key_id: str
    addon_id: str
    addon_name: str
    quantity: int


class VerifyAddonPaymentRequest(BaseModel):
    """Request to verify add-on payment"""
    addon_id: str
    quantity: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class UserAddonResponse(BaseModel):
    """Response for user's active add-on"""
    id: str
    addon_id: str
    addon_name: str
    status: str
    quantity: int
    amount_per_month: float
    total_amount: float
    currency: str
    started_at: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    next_billing_date: Optional[datetime]


class CancelAddonRequest(BaseModel):
    """Request to cancel add-on"""
    user_addon_id: str
    cancel_at_period_end: bool = True


class CombinedLimitsResponse(BaseModel):
    """User's total limits (base plan + add-ons)"""
    plan: str
    base_limits: Dict[str, Any]
    addon_limits: Dict[str, Any]
    total_limits: Dict[str, Any]
    active_addons: List[UserAddonResponse]
```

### Step 3: Add-on Service

**File**: `backend/app/services/addon_service.py`

```python
"""
Add-on Management Service
Handles add-on catalog, purchases, and combined limit calculations
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from bson import ObjectId
from app.mongodb import mongodb
from app.models.mongodb_models import AddonProduct, UserAddon
import logging

logger = logging.getLogger(__name__)


class AddonService:
    """Manage subscription add-ons"""

    async def get_all_addons(
        self,
        user_plan: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all available add-ons, optionally filtered by user's plan

        Args:
            user_plan: Filter add-ons available for this plan

        Returns:
            List of add-on products
        """
        query = {"is_active": True}

        if user_plan:
            query["available_for_plans"] = user_plan

        addons = await mongodb.database["addon_products"].find(query).sort("sort_order", 1).to_list(None)
        return addons

    async def get_addon_by_id(self, addon_id: str) -> Optional[Dict[str, Any]]:
        """Get add-on product by ID"""
        return await mongodb.database["addon_products"].find_one({"addon_id": addon_id})

    async def get_user_addons(
        self,
        user_id: ObjectId,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """
        Get user's active add-ons

        Args:
            user_id: User ID
            status: Filter by status (active, canceled, expired)

        Returns:
            List of user's add-ons with details
        """
        user_addons = await mongodb.database["user_addons"].find({
            "user_id": user_id,
            "status": status
        }).to_list(None)

        # Enrich with add-on product details
        enriched = []
        for ua in user_addons:
            addon_product = await self.get_addon_by_id(ua["addon_id"])
            if addon_product:
                enriched.append({
                    **ua,
                    "addon_name": addon_product["name"],
                    "addon_description": addon_product["description"],
                    "addon_type": addon_product["type"]
                })

        return enriched

    async def calculate_combined_limits(
        self,
        user_id: ObjectId
    ) -> Dict[str, Any]:
        """
        Calculate total limits = base plan + all active add-ons

        Args:
            user_id: User ID

        Returns:
            Dict with base_limits, addon_limits, and total_limits
        """
        from app.services.subscription_service import subscription_service

        # Get base plan limits
        subscription = await subscription_service.get_user_subscription(user_id)
        base_limits = subscription["limits"]

        # Get all active add-ons
        active_addons = await self.get_user_addons(user_id, status="active")

        # Calculate addon contributions
        addon_limits = {
            "api_hits_per_month": 0,
            "model_generation_per_day": 0,
            "dataset_size_mb": 0,
            "azure_storage_gb": 0,
            "training_time_minutes_per_model": 0,
            "concurrent_trainings": 0
        }

        for ua in active_addons:
            addon_product = await self.get_addon_by_id(ua["addon_id"])
            if addon_product and addon_product["increment"]:
                quantity = ua.get("quantity", 1)
                for key, value in addon_product["increment"].items():
                    if key in addon_limits:
                        addon_limits[key] += value * quantity

        # Calculate total limits
        total_limits = {}
        for key in base_limits:
            total_limits[key] = base_limits[key] + addon_limits.get(key, 0)

        return {
            "plan": subscription["plan"],
            "base_limits": base_limits,
            "addon_limits": addon_limits,
            "total_limits": total_limits,
            "active_addons": active_addons
        }

    async def can_purchase_addon(
        self,
        user_id: ObjectId,
        addon_id: str,
        quantity: int = 1
    ) -> tuple[bool, str]:
        """
        Check if user can purchase this add-on

        Returns:
            (can_purchase, reason_if_not)
        """
        # Get addon product
        addon_product = await self.get_addon_by_id(addon_id)
        if not addon_product:
            return False, "Add-on not found"

        if not addon_product["is_active"]:
            return False, "Add-on is not available"

        # Check user's plan eligibility
        from app.services.subscription_service import subscription_service
        subscription = await subscription_service.get_user_subscription(user_id)
        user_plan = subscription["plan"]

        if user_plan not in addon_product["available_for_plans"]:
            return False, f"Add-on not available for {user_plan} plan"

        # Check if user already has this add-on
        existing_addons = await mongodb.database["user_addons"].find({
            "user_id": user_id,
            "addon_id": addon_id,
            "status": "active"
        }).to_list(None)

        current_quantity = sum(ua.get("quantity", 1) for ua in existing_addons)

        # Check max quantity
        if not addon_product["is_stackable"] and current_quantity > 0:
            return False, "This add-on cannot be purchased multiple times"

        if current_quantity + quantity > addon_product["max_quantity"]:
            return False, f"Maximum quantity is {addon_product['max_quantity']}"

        return True, ""


# Global add-on service instance
addon_service = AddonService()
```

### Step 4: Add-on Router

**File**: `backend/app/routers/addons.py`

```python
"""
Add-on Management Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.mongodb import mongodb
from app.models.mongodb_models import User
from app.dependencies import get_current_user
from app.services.addon_service import addon_service
from app.services.payment_service import payment_service
from app.schemas.addon_schemas import (
    AddonProductResponse,
    PurchaseAddonRequest,
    CreateAddonOrderResponse,
    VerifyAddonPaymentRequest,
    UserAddonResponse,
    CancelAddonRequest,
    CombinedLimitsResponse
)
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/addons", tags=["Add-ons"])


@router.get("/", response_model=List[AddonProductResponse])
async def get_addons(current_user: User = Depends(get_current_user)):
    """Get all available add-ons for user's plan"""
    addons = await addon_service.get_all_addons(user_plan=current_user.current_plan)

    return [
        AddonProductResponse(
            id=str(addon["_id"]),
            addon_id=addon["addon_id"],
            name=addon["name"],
            description=addon["description"],
            type=addon["type"],
            category=addon["category"],
            price_monthly=addon["price_monthly"],
            currency=addon["currency"],
            increment=addon["increment"],
            available_for_plans=addon["available_for_plans"],
            max_quantity=addon["max_quantity"],
            is_stackable=addon["is_stackable"],
            icon=addon.get("icon"),
            badge=addon.get("badge"),
            is_active=addon["is_active"]
        )
        for addon in addons
    ]


@router.get("/my-addons", response_model=List[UserAddonResponse])
async def get_my_addons(current_user: User = Depends(get_current_user)):
    """Get user's active add-ons"""
    addons = await addon_service.get_user_addons(current_user.id, status="active")

    return [
        UserAddonResponse(
            id=str(addon["_id"]),
            addon_id=addon["addon_id"],
            addon_name=addon["addon_name"],
            status=addon["status"],
            quantity=addon["quantity"],
            amount_per_month=addon["amount_per_month"],
            total_amount=addon["total_amount"],
            currency=addon["currency"],
            started_at=addon["started_at"],
            current_period_end=addon["current_period_end"],
            cancel_at_period_end=addon["cancel_at_period_end"],
            next_billing_date=addon.get("next_billing_date")
        )
        for addon in addons
    ]


@router.get("/combined-limits", response_model=CombinedLimitsResponse)
async def get_combined_limits(current_user: User = Depends(get_current_user)):
    """Get user's total limits (base plan + add-ons)"""
    limits = await addon_service.calculate_combined_limits(current_user.id)

    return CombinedLimitsResponse(
        plan=limits["plan"],
        base_limits=limits["base_limits"],
        addon_limits=limits["addon_limits"],
        total_limits=limits["total_limits"],
        active_addons=[
            UserAddonResponse(
                id=str(addon["_id"]),
                addon_id=addon["addon_id"],
                addon_name=addon["addon_name"],
                status=addon["status"],
                quantity=addon["quantity"],
                amount_per_month=addon["amount_per_month"],
                total_amount=addon["total_amount"],
                currency=addon["currency"],
                started_at=addon["started_at"],
                current_period_end=addon["current_period_end"],
                cancel_at_period_end=addon["cancel_at_period_end"],
                next_billing_date=addon.get("next_billing_date")
            )
            for addon in limits["active_addons"]
        ]
    )


@router.post("/purchase", response_model=CreateAddonOrderResponse)
async def purchase_addon(
    request: PurchaseAddonRequest,
    current_user: User = Depends(get_current_user)
):
    """Create Razorpay order for add-on purchase"""
    # Check if user can purchase
    can_purchase, reason = await addon_service.can_purchase_addon(
        current_user.id,
        request.addon_id,
        request.quantity
    )

    if not can_purchase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason
        )

    # Get addon details
    addon = await addon_service.get_addon_by_id(request.addon_id)
    if not addon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Add-on not found"
        )

    # Create order (using payment_service)
    # TODO: Extend payment_service to handle add-ons

    # For now, return mock response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Add-on purchase will be implemented in Phase 2"
    )


@router.post("/verify-payment")
async def verify_addon_payment(
    request: VerifyAddonPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify add-on payment and activate"""
    # TODO: Implement payment verification and add-on activation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Add-on payment verification will be implemented in Phase 2"
    )


@router.post("/cancel")
async def cancel_addon(
    request: CancelAddonRequest,
    current_user: User = Depends(get_current_user)
):
    """Cancel user's add-on"""
    # TODO: Implement add-on cancellation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Add-on cancellation will be implemented in Phase 2"
    )
```

### Step 5: Update Main App

**File**: `backend/app/main.py`

```python
# Add to imports
from app.routers import ..., addons

# Add to routers
app.include_router(addons.router)
```

### Step 6: Initialize Add-on Products

**File**: `backend/app/scripts/init_addon_products.py`

```python
"""
Initialize Add-on Products in MongoDB
Run once to populate the addon_products collection
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings


async def init_addons():
    """Initialize add-on products"""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client.get_database()

    addons = [
        # Storage Add-ons
        {
            "addon_id": "extra_storage_5gb",
            "name": "Extra Storage (+5 GB)",
            "description": "Add 5 GB of Azure Blob Storage",
            "type": "storage",
            "category": "capacity",
            "price_monthly": 99.0,
            "currency": "INR",
            "increment": {"azure_storage_gb": 5},
            "available_for_plans": ["free", "pro"],
            "max_quantity": 10,
            "is_stackable": True,
            "icon": "hard-drive",
            "badge": None,
            "sort_order": 1,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_id": "extra_storage_10gb",
            "name": "Extra Storage (+10 GB)",
            "description": "Add 10 GB of Azure Blob Storage",
            "type": "storage",
            "category": "capacity",
            "price_monthly": 179.0,
            "currency": "INR",
            "increment": {"azure_storage_gb": 10},
            "available_for_plans": ["free", "pro"],
            "max_quantity": 10,
            "is_stackable": True,
            "icon": "hard-drive",
            "badge": "POPULAR",
            "sort_order": 2,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },

        # API Boost Add-ons
        {
            "addon_id": "api_boost_5000",
            "name": "API Boost (+5,000 calls)",
            "description": "Add 5,000 API calls per month",
            "type": "api",
            "category": "capacity",
            "price_monthly": 149.0,
            "currency": "INR",
            "increment": {"api_hits_per_month": 5000},
            "available_for_plans": ["free", "pro"],
            "max_quantity": 10,
            "is_stackable": True,
            "icon": "zap",
            "badge": None,
            "sort_order": 3,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_id": "api_boost_10000",
            "name": "API Boost (+10,000 calls)",
            "description": "Add 10,000 API calls per month",
            "type": "api",
            "category": "capacity",
            "price_monthly": 279.0,
            "currency": "INR",
            "increment": {"api_hits_per_month": 10000},
            "available_for_plans": ["free", "pro"],
            "max_quantity": 10,
            "is_stackable": True,
            "icon": "zap",
            "badge": "BEST VALUE",
            "sort_order": 4,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },

        # Model Training Add-ons
        {
            "addon_id": "model_boost_10",
            "name": "Model Boost (+10 models/day)",
            "description": "Train 10 additional models per day",
            "type": "models",
            "category": "capacity",
            "price_monthly": 199.0,
            "currency": "INR",
            "increment": {"model_generation_per_day": 10},
            "available_for_plans": ["free", "pro"],
            "max_quantity": 5,
            "is_stackable": True,
            "icon": "activity",
            "badge": None,
            "sort_order": 5,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_id": "model_boost_20",
            "name": "Model Boost (+20 models/day)",
            "description": "Train 20 additional models per day",
            "type": "models",
            "category": "capacity",
            "price_monthly": 379.0,
            "currency": "INR",
            "increment": {"model_generation_per_day": 20},
            "available_for_plans": ["free", "pro"],
            "max_quantity": 5,
            "is_stackable": True,
            "icon": "activity",
            "badge": None,
            "sort_order": 6,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },

        # Feature Add-ons
        {
            "addon_id": "priority_queue",
            "name": "Priority Queue",
            "description": "Jump to the front of model training queue",
            "type": "feature",
            "category": "performance",
            "price_monthly": 499.0,
            "currency": "INR",
            "increment": {"has_priority_queue": True},
            "available_for_plans": ["pro"],
            "max_quantity": 1,
            "is_stackable": False,
            "icon": "trending-up",
            "badge": "PREMIUM",
            "sort_order": 7,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_id": "custom_domain",
            "name": "Custom Domain",
            "description": "Deploy your models on a custom domain",
            "type": "feature",
            "category": "features",
            "price_monthly": 599.0,
            "currency": "INR",
            "increment": {"has_custom_domain": True},
            "available_for_plans": ["pro", "advanced"],
            "max_quantity": 1,
            "is_stackable": False,
            "icon": "globe",
            "badge": None,
            "sort_order": 8,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_id": "white_label",
            "name": "White Label",
            "description": "Remove Smart ML branding from your deployments",
            "type": "feature",
            "category": "features",
            "price_monthly": 999.0,
            "currency": "INR",
            "increment": {"has_white_label": True},
            "available_for_plans": ["advanced"],
            "max_quantity": 1,
            "is_stackable": False,
            "icon": "eye-off",
            "badge": "ENTERPRISE",
            "sort_order": 9,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    # Insert or update add-ons
    for addon in addons:
        existing = await db.addon_products.find_one({"addon_id": addon["addon_id"]})

        if existing:
            await db.addon_products.update_one(
                {"addon_id": addon["addon_id"]},
                {"$set": addon}
            )
            print(f"Updated: {addon['name']}")
        else:
            await db.addon_products.insert_one(addon)
            print(f"Created: {addon['name']}")

    print(f"\n{len(addons)} add-on products initialized!")

    # Create indexes
    print("\nCreating indexes...")
    await db.addon_products.create_index("addon_id", unique=True)
    await db.addon_products.create_index([("type", 1), ("is_active", 1)])
    await db.addon_products.create_index("sort_order")
    print("Indexes created!")

    client.close()


if __name__ == "__main__":
    print("Initializing add-on products...\n")
    asyncio.run(init_addons())
```

---

## Frontend Implementation

### Step 1: Add-ons Component

**File**: `frontend/client/src/components/AddonsGrid.tsx`

```tsx
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { HardDrive, Zap, Activity, TrendingUp, Globe, EyeOff, Plus } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import axios from 'axios';

interface Addon {
  id: string;
  addon_id: string;
  name: string;
  description: string;
  type: string;
  category: string;
  price_monthly: number;
  currency: string;
  increment: Record<string, any>;
  max_quantity: number;
  is_stackable: boolean;
  icon?: string;
  badge?: string;
  is_active: boolean;
}

interface ActiveAddon {
  id: string;
  addon_id: string;
  addon_name: string;
  quantity: number;
  total_amount: number;
}

const AddonsGrid: React.FC = () => {
  const [addons, setAddons] = useState<Addon[]>([]);
  const [myAddons, setMyAddons] = useState<ActiveAddon[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchAddons();
    fetchMyAddons();
  }, []);

  const fetchAddons = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/addons/', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setAddons(response.data);
    } catch (error) {
      console.error('Failed to fetch add-ons:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMyAddons = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/addons/my-addons', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setMyAddons(response.data);
    } catch (error) {
      console.error('Failed to fetch my add-ons:', error);
    }
  };

  const getIcon = (iconName?: string) => {
    const icons: Record<string, JSX.Element> = {
      'hard-drive': <HardDrive className="h-5 w-5" />,
      'zap': <Zap className="h-5 w-5" />,
      'activity': <Activity className="h-5 w-5" />,
      'trending-up': <TrendingUp className="h-5 w-5" />,
      'globe': <Globe className="h-5 w-5" />,
      'eye-off': <EyeOff className="h-5 w-5" />
    };
    return icons[iconName || 'hard-drive'] || <HardDrive className="h-5 w-5" />;
  };

  const handlePurchase = async (addonId: string, quantity: number = 1) => {
    try {
      const response = await axios.post(
        'http://localhost:8000/api/addons/purchase',
        { addon_id: addonId, quantity },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );

      // TODO: Handle Razorpay checkout flow
      toast({
        title: 'Coming Soon',
        description: 'Add-on purchase will be available in the next update!',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to purchase add-on',
        variant: 'destructive'
      });
    }
  };

  const getActiveQuantity = (addonId: string): number => {
    const active = myAddons.find(a => a.addon_id === addonId);
    return active?.quantity || 0;
  };

  if (loading) {
    return <div className="text-center py-8">Loading add-ons...</div>;
  }

  return (
    <div className="space-y-8">
      {/* Active Add-ons Section */}
      {myAddons.length > 0 && (
        <div>
          <h3 className="text-xl font-bold mb-4">Your Active Add-ons</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {myAddons.map((addon) => (
              <Card key={addon.id} className="border-green-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">{addon.addon_name}</CardTitle>
                  <Badge variant="secondary" className="w-fit">Active</Badge>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">Quantity: {addon.quantity}</p>
                  <p className="text-lg font-semibold mt-2">₹{addon.total_amount}/month</p>
                </CardContent>
                <CardFooter>
                  <Button variant="outline" size="sm" className="w-full">
                    Manage
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Available Add-ons Section */}
      <div>
        <h3 className="text-xl font-bold mb-4">Available Add-ons</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {addons.map((addon) => {
            const activeQuantity = getActiveQuantity(addon.addon_id);
            const canPurchaseMore = activeQuantity < addon.max_quantity;

            return (
              <Card key={addon.id} className="hover:shadow-lg transition-shadow">
                {addon.badge && (
                  <div className="absolute top-0 right-0 bg-blue-600 text-white px-3 py-1 text-xs font-semibold rounded-bl-lg">
                    {addon.badge}
                  </div>
                )}

                <CardHeader>
                  <div className="flex items-center gap-2 text-blue-600">
                    {getIcon(addon.icon)}
                    <CardTitle className="text-lg">{addon.name}</CardTitle>
                  </div>
                  <CardDescription>{addon.description}</CardDescription>
                </CardHeader>

                <CardContent className="space-y-3">
                  <div className="text-3xl font-bold">
                    ₹{addon.price_monthly}
                    <span className="text-sm text-gray-500 font-normal">/month</span>
                  </div>

                  {activeQuantity > 0 && (
                    <Badge variant="secondary">
                      Active: {activeQuantity} × ₹{addon.price_monthly}
                    </Badge>
                  )}

                  <div className="text-sm text-gray-600">
                    {addon.is_stackable && `Max: ${addon.max_quantity}`}
                  </div>
                </CardContent>

                <CardFooter>
                  <Button
                    onClick={() => handlePurchase(addon.addon_id)}
                    disabled={!canPurchaseMore}
                    className="w-full"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    {activeQuantity > 0 ? 'Add More' : 'Purchase'}
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AddonsGrid;
```

### Step 2: Update Billing Page

**File**: `frontend/client/src/pages/Billing.tsx`

Update the "Add-ons" tab content:

```tsx
<TabsContent value="addons" className="space-y-6">
  <AddonsGrid />
</TabsContent>
```

---

## Testing Plan

### Unit Tests

1. **AddonService Tests**
   - `test_get_all_addons()`
   - `test_calculate_combined_limits()`
   - `test_can_purchase_addon()`

2. **AddonRouter Tests**
   - `test_get_addons_endpoint()`
   - `test_purchase_addon_validation()`
   - `test_combined_limits_calculation()`

### Integration Tests

1. **Purchase Flow**
   - Create order
   - Verify payment
   - Activate add-on
   - Update limits

2. **Limit Enforcement**
   - Base plan limits
   - With 1 add-on
   - With multiple stackable add-ons

3. **Cancellation Flow**
   - Cancel immediately
   - Cancel at period end
   - Verify limits revert

### E2E Tests

1. View add-ons catalog
2. Purchase storage add-on
3. Verify increased storage limit
4. Purchase API boost add-on
5. Verify combined limits
6. Cancel add-on
7. Verify limits decrease

---

## Deployment Checklist

- [ ] Run `init_addon_products.py` in production
- [ ] Verify all add-ons created in MongoDB
- [ ] Test add-on catalog API
- [ ] Test combined limits calculation
- [ ] Deploy frontend with add-ons UI
- [ ] Test purchase flow end-to-end
- [ ] Configure Razorpay for add-on payments
- [ ] Set up monitoring for add-on metrics
- [ ] Update documentation
- [ ] Announce feature to users

---

## Future Enhancements

1. **Dynamic Pricing**
   - Based on demand
   - Seasonal discounts
   - Bundle offers

2. **Trial Periods**
   - 7-day free trial for add-ons
   - Auto-cancel if not upgraded

3. **Usage-Based Add-ons**
   - Pay-per-GB storage
   - Pay-per-1000 API calls

4. **Add-on Bundles**
   - "Power User Pack" (storage + API + models)
   - "Enterprise Pack" (all features)

---

**Status**: Ready for implementation (Week 4)
**Estimated Effort**: 3-4 days
**Priority**: High (Revenue driver)

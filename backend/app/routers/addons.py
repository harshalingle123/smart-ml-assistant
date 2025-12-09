"""
Add-on Management Endpoints
Handles add-on catalog, purchases, and management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.mongodb import mongodb
from app.models.mongodb_models import User
from app.dependencies import get_current_user
from app.services.addon_service import addon_service
from app.services.payment_service import payment_service
from app.schemas.addon_schemas import (
    AddonResponse,
    UserAddonResponse,
    PurchaseAddonRequest,
    CreateAddonOrderResponse,
    VerifyAddonPaymentRequest,
    CancelAddonRequest,
    CombinedLimitsResponse,
    AddonPaymentHistoryResponse
)
from bson import ObjectId
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/addons", tags=["Add-ons"])


@router.get("/", response_model=List[AddonResponse])
async def get_addons(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get all available add-ons

    Optional query params:
    - category: Filter by category (storage, api_hits, training, support)
    """
    addons = await addon_service.get_all_addons(
        user_plan=current_user.current_plan,
        category=category
    )

    return [
        AddonResponse(
            id=str(addon["_id"]),
            addon_slug=addon["addon_slug"],
            name=addon["name"],
            description=addon["description"],
            category=addon["category"],
            price_monthly=addon["price_monthly"],
            price_annual=addon.get("price_annual"),
            currency=addon["currency"],
            quota_type=addon["quota_type"],
            quota_amount=addon["quota_amount"],
            compatible_plans=addon.get("compatible_plans", []),
            max_quantity=addon.get("max_quantity", 10),
            is_active=addon["is_active"],
            icon=addon.get("icon"),
            badge_text=addon.get("badge_text"),
            display_order=addon.get("display_order", 0)
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
            addon_id=str(addon["addon_id"]),
            addon_name=addon["addon_name"],
            addon_description=addon["addon_description"],
            quantity=addon["quantity"],
            amount_paid=addon["amount_paid"],
            currency=addon["currency"],
            status=addon["status"],
            period_start=addon["period_start"],
            period_end=addon["period_end"],
            auto_renew=addon["auto_renew"],
            quota_type=addon["quota_type"],
            quota_amount=addon["quota_amount"],
            total_quota=addon["total_quota"]
        )
        for addon in addons
    ]


@router.get("/combined-limits", response_model=CombinedLimitsResponse)
async def get_combined_limits(current_user: User = Depends(get_current_user)):
    """
    Get user's total limits (base plan + add-ons)

    Returns combined limits showing how add-ons boost the base plan
    """
    limits = await addon_service.calculate_combined_limits(current_user.id)

    return CombinedLimitsResponse(
        user_id=limits["user_id"],
        plan=limits["plan"],
        base_limits=limits["base_limits"],
        addon_contributions=limits["addon_contributions"],
        total_limits=limits["total_limits"],
        active_addons=[
            UserAddonResponse(
                id=str(addon["_id"]),
                addon_id=str(addon["addon_id"]),
                addon_name=addon["addon_name"],
                addon_description=addon["addon_description"],
                quantity=addon["quantity"],
                amount_paid=addon["amount_paid"],
                currency=addon["currency"],
                status=addon["status"],
                period_start=addon["period_start"],
                period_end=addon["period_end"],
                auto_renew=addon["auto_renew"],
                quota_type=addon["quota_type"],
                quota_amount=addon["quota_amount"],
                total_quota=addon["total_quota"]
            )
            for addon in limits["active_addons"]
        ],
        addon_count=limits["addon_count"],
        total_addon_cost=limits["total_addon_cost"]
    )


@router.post("/create-order", response_model=CreateAddonOrderResponse)
async def create_addon_order(
    request: PurchaseAddonRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create Razorpay order for add-on purchase

    Step 1 of payment flow:
    1. Frontend calls this endpoint
    2. Backend creates Razorpay order
    3. Frontend opens Razorpay checkout
    4. User completes payment
    5. Frontend calls verify-payment endpoint
    """
    # Check if user can purchase
    can_purchase, reason = await addon_service.can_purchase_addon(
        current_user.id,
        request.addon_slug,
        request.quantity
    )

    if not can_purchase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason
        )

    # Get addon details
    addon = await addon_service.get_addon_by_slug(request.addon_slug)
    if not addon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Add-on not found"
        )

    # Calculate total price
    total_price = addon["price_monthly"] * request.quantity

    # Create Razorpay order
    if not payment_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service not configured"
        )

    try:
        from app.core.config import settings
        from datetime import datetime

        amount_paise = int(total_price * 100)  # Convert to paise
        # Receipt must be <= 40 chars. Use last 12 chars of user_id + timestamp
        timestamp = int(datetime.utcnow().timestamp())
        receipt = f"adn_{str(current_user.id)[-12:]}_{timestamp}"
        order_data = {
            "amount": amount_paise,
            "currency": addon["currency"],
            "receipt": receipt,
            "notes": {
                "user_id": str(current_user.id),
                "addon_slug": request.addon_slug,
                "quantity": str(request.quantity),
                "type": "addon_purchase"
            }
        }

        razorpay_order = payment_service.client.order.create(data=order_data)
        logger.info(f"Razorpay order created for add-on: {razorpay_order['id']}")

        return CreateAddonOrderResponse(
            order_id=razorpay_order["id"],
            amount=total_price,
            currency=addon["currency"],
            key_id=settings.RAZORPAY_KEY_ID,
            addon_slug=request.addon_slug,
            addon_name=addon["name"],
            quantity=request.quantity,
            total_price=total_price
        )

    except Exception as e:
        logger.error(f"Failed to create addon order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order creation failed: {str(e)}"
        )


@router.post("/verify-payment")
async def verify_addon_payment(
    request: VerifyAddonPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Verify add-on payment and activate

    Step 2 of payment flow (called after successful Razorpay payment)
    """
    # Verify signature
    if not payment_service.verify_payment_signature(
        request.razorpay_order_id,
        request.razorpay_payment_id,
        request.razorpay_signature
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )

    # Fetch payment details from Razorpay
    try:
        payment_details = payment_service.client.payment.fetch(request.razorpay_payment_id)
        logger.info(f"Add-on payment verified: {request.razorpay_payment_id}")
    except Exception as e:
        logger.error(f"Failed to fetch payment details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed"
        )

    # Get addon details
    addon = await addon_service.get_addon_by_slug(request.addon_slug)
    if not addon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Add-on not found"
        )

    # Calculate amount paid
    total_price = addon["price_monthly"] * request.quantity

    # Activate add-on
    try:
        result = await addon_service.activate_addon(
            user_id=current_user.id,
            addon_slug=request.addon_slug,
            quantity=request.quantity,
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_order_id=request.razorpay_order_id,
            amount_paid=total_price
        )

        # Record payment transaction in payments collection
        from app.models.mongodb_models import Payment
        from datetime import datetime

        payment_record = Payment(
            user_id=current_user.id,
            subscription_id=None,  # Add-ons don't have subscription_id
            amount=total_price,
            currency=addon["currency"],
            status="success",
            payment_method=payment_details.get("method", "unknown"),
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_order_id=request.razorpay_order_id,
            razorpay_signature=request.razorpay_signature,
            description=f"Add-on: {addon['name']} (Qty: {request.quantity})"
        )
        await mongodb.database["payments"].insert_one(
            payment_record.dict(by_alias=True)
        )
        logger.info(f"Payment record created for add-on purchase: {request.razorpay_payment_id}")

        return {
            "success": True,
            "message": result["message"],
            "user_addon_id": result["user_addon_id"],
            "addon_name": addon["name"],
            "quantity": request.quantity,
            "period_start": result["period_start"],
            "period_end": result["period_end"]
        }

    except Exception as e:
        logger.error(f"Failed to activate add-on: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Add-on activation failed: {str(e)}"
        )


@router.post("/cancel")
async def cancel_addon(
    request: CancelAddonRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel user's add-on

    - immediate=False: Cancel at period end (user keeps access until then)
    - immediate=True: Cancel now (access removed immediately, no refund)
    """
    try:
        result = await addon_service.cancel_addon(
            user_id=current_user.id,
            user_addon_id=request.user_addon_id,
            immediate=request.immediate
        )

        return result

    except Exception as e:
        logger.error(f"Add-on cancellation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/payment-history", response_model=List[AddonPaymentHistoryResponse])
async def get_addon_payment_history(current_user: User = Depends(get_current_user)):
    """Get user's add-on payment history"""
    user_addons = await mongodb.database["user_addons"].find({
        "user_id": current_user.id
    }).sort("created_at", -1).limit(50).to_list(50)

    history = []
    for ua in user_addons:
        # Get addon details
        addon = await addon_service.get_addon_by_id(ua["addon_id"])
        if addon:
            history.append(
                AddonPaymentHistoryResponse(
                    id=str(ua["_id"]),
                    addon_name=addon["name"],
                    quantity=ua["quantity"],
                    amount=ua["amount_paid"],
                    currency=ua["currency"],
                    status=ua["status"],
                    razorpay_payment_id=ua.get("razorpay_payment_id"),
                    created_at=ua["created_at"]
                )
            )

    return history

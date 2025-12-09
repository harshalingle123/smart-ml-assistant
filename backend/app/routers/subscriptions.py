"""
Subscription Management Endpoints
Handles subscription lifecycle, payments, and usage tracking
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from app.mongodb import mongodb
from app.models.mongodb_models import User
from app.dependencies import get_current_user
from app.services.payment_service import payment_service
from app.services.subscription_service import subscription_service
from app.schemas.subscription_schemas import (
    PlanResponse,
    SubscriptionResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    VerifyPaymentRequest,
    CancelSubscriptionRequest,
    UsageResponse,
    PaymentHistoryResponse,
    SubscriptionWebhookRequest
)
from bson import ObjectId
from typing import List
from datetime import datetime
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans():
    """Get all available subscription plans"""
    plans = await subscription_service.get_all_plans()

    return [
        PlanResponse(
            id=str(plan["_id"]),
            plan=plan["plan"],
            name=plan["name"],
            description=plan.get("description"),
            price_monthly=plan["price_monthly"],
            currency=plan["currency"],
            api_hits_per_month=plan["api_hits_per_month"],
            model_generation_per_day=plan["model_generation_per_day"],
            dataset_size_mb=plan["dataset_size_mb"],
            azure_storage_gb=plan["azure_storage_gb"],
            training_time_minutes_per_model=plan["training_time_minutes_per_model"],
            concurrent_trainings=plan["concurrent_trainings"],
            features=plan.get("features", []),
            priority_support=plan.get("priority_support", False),
            razorpay_plan_id=plan.get("razorpay_plan_id"),
            is_active=plan["is_active"]
        )
        for plan in plans
    ]


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(current_user: User = Depends(get_current_user)):
    """Get user's current subscription details"""
    subscription = await subscription_service.get_user_subscription(current_user.id)

    if not subscription or subscription.get("plan") == "free":
        # Return free plan as default
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active paid subscription found. User is on free plan."
        )

    return SubscriptionResponse(
        id=str(subscription["_id"]),
        user_id=str(subscription["user_id"]),
        plan=subscription["plan"],
        provider=subscription["provider"],
        status=subscription["status"],
        period_start=subscription["period_start"],
        period_end=subscription["period_end"],
        cancel_at_period_end=subscription["cancel_at_period_end"],
        canceled_at=subscription.get("canceled_at"),
        amount=subscription["amount"],
        currency=subscription["currency"],
        last_payment_at=subscription.get("last_payment_at"),
        next_billing_date=subscription.get("next_billing_date"),
        razorpay_subscription_id=subscription.get("razorpay_subscription_id")
    )


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    order_request: CreateOrderRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a Razorpay order for subscription payment
    Supports UPI, Cards, NetBanking, Wallets
    """
    logger.info(f"[CREATE ORDER] Request from user {current_user.id} for plan: {order_request.plan}")

    if order_request.plan not in ["pro", "advanced"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan. Choose 'pro' or 'advanced'."
        )

    try:
        logger.info(f"[CREATE ORDER] Calling payment_service.create_order...")
        order_details = await payment_service.create_order(
            user_id=current_user.id,
            plan_name=order_request.plan
        )
        logger.info(f"[CREATE ORDER] Success! Order ID: {order_details['order_id']}")

        return CreateOrderResponse(**order_details)

    except Exception as e:
        import traceback
        logger.error(f"[CREATE ORDER] Failed to create order for user {current_user.id}")
        logger.error(f"[CREATE ORDER] Error: {str(e)}")
        logger.error(f"[CREATE ORDER] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/verify-payment")
async def verify_payment(
    payment_request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Verify Razorpay payment and activate subscription
    Called after successful payment from frontend
    """
    try:
        result = await payment_service.process_payment(
            user_id=current_user.id,
            plan_name=payment_request.plan,
            razorpay_order_id=payment_request.razorpay_order_id,
            razorpay_payment_id=payment_request.razorpay_payment_id,
            razorpay_signature=payment_request.razorpay_signature
        )

        return result

    except Exception as e:
        logger.error(f"Payment verification failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/cancel")
async def cancel_subscription(
    cancel_request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel user subscription
    If cancel_at_period_end=True, subscription remains active until period ends
    """
    try:
        result = await payment_service.cancel_subscription(
            user_id=current_user.id,
            cancel_at_period_end=cancel_request.cancel_at_period_end
        )

        return result

    except Exception as e:
        logger.error(f"Subscription cancellation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(current_user: User = Depends(get_current_user)):
    """Get user's current usage statistics and limits"""
    try:
        usage_stats = await subscription_service.get_usage_stats(current_user.id)
        return UsageResponse(**usage_stats)

    except Exception as e:
        logger.error(f"Failed to get usage for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.get("/payment-history", response_model=List[PaymentHistoryResponse])
async def get_payment_history(current_user: User = Depends(get_current_user)):
    """Get user's payment history"""
    payments = await mongodb.database["payments"].find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).limit(50).to_list(50)

    return [
        PaymentHistoryResponse(
            id=str(payment["_id"]),
            amount=payment["amount"],
            currency=payment["currency"],
            status=payment["status"],
            payment_method=payment["payment_method"],
            razorpay_payment_id=payment.get("razorpay_payment_id"),
            description=payment.get("description"),
            created_at=payment["created_at"]
        )
        for payment in payments
    ]


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None)
):
    """
    Handle Razorpay webhook events
    Verifies webhook signature and processes events with full logging
    """
    from app.core.config import settings

    # Get raw body for signature verification
    body = await request.body()
    body_str = body.decode("utf-8")

    # Get client IP for security logging
    source_ip = request.client.host if request.client else None

    # Verify webhook signature
    signature_valid = True
    if settings.RAZORPAY_WEBHOOK_SECRET and x_razorpay_signature:
        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            body_str.encode(),
            hashlib.sha256
        ).hexdigest()

        signature_valid = hmac.compare_digest(expected_signature, x_razorpay_signature)

        if not signature_valid:
            logger.warning(f"Invalid webhook signature from IP: {source_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )

    # Parse webhook payload
    try:
        import json
        payload = json.loads(body_str)
        event = payload.get("event")
        event_id = payload.get("id")  # Razorpay event ID

        logger.info(f"Webhook received: {event} (ID: {event_id}) from IP: {source_ip}")

        # Process webhook with full context
        result = await payment_service.handle_webhook(
            event=event,
            payload=payload,
            event_id=event_id,
            source_ip=source_ip
        )

        return result

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

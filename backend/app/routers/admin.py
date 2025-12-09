"""
Admin Endpoints
Manage webhooks, refunds, analytics, and system operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.mongodb import mongodb
from app.models.mongodb_models import User
from app.dependencies import get_current_user
from app.services.payment_service import payment_service
from app.services.dunning_service import dunning_service
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin access"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ===== WEBHOOK MANAGEMENT =====

@router.get("/webhooks/events")
async def list_webhook_events(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, processing, processed, failed"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    admin_user: User = Depends(require_admin)
):
    """
    List all webhook events with filtering and pagination
    """
    query = {}
    if status_filter:
        query["status"] = status_filter
    if event_type:
        query["event_type"] = event_type

    # Get total count
    total = await mongodb.database["webhook_events"].count_documents(query)

    # Get paginated results
    events = await mongodb.database["webhook_events"].find(query).sort(
        "created_at", -1
    ).skip(offset).limit(limit).to_list(limit)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "events": [
            {
                "id": str(event["_id"]),
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "status": event["status"],
                "processing_attempts": event.get("processing_attempts", 0),
                "error_message": event.get("error_message"),
                "source_ip": event.get("source_ip"),
                "created_at": event["created_at"],
                "processed_at": event.get("processed_at"),
                "updated_at": event["updated_at"]
            }
            for event in events
        ]
    }


@router.get("/webhooks/events/{event_id}")
async def get_webhook_event(
    event_id: str,
    admin_user: User = Depends(require_admin)
):
    """
    Get detailed webhook event information including full payload
    """
    try:
        event_object_id = ObjectId(event_id)
        event = await mongodb.database["webhook_events"].find_one({"_id": event_object_id})

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook event not found"
            )

        return {
            "id": str(event["_id"]),
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "status": event["status"],
            "processing_attempts": event.get("processing_attempts", 0),
            "max_retry_attempts": event.get("max_retry_attempts", 3),
            "payload": event["payload"],
            "error_message": event.get("error_message"),
            "error_stack": event.get("error_stack"),
            "source_ip": event.get("source_ip"),
            "signature_valid": event.get("signature_valid", True),
            "created_at": event["created_at"],
            "processed_at": event.get("processed_at"),
            "next_retry_at": event.get("next_retry_at"),
            "updated_at": event["updated_at"]
        }

    except Exception as e:
        logger.error(f"Failed to get webhook event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/webhooks/events/{event_id}/retry")
async def retry_webhook_event(
    event_id: str,
    admin_user: User = Depends(require_admin)
):
    """
    Manually retry a failed webhook event
    Useful for recovering from temporary failures
    """
    try:
        event_object_id = ObjectId(event_id)
        event = await mongodb.database["webhook_events"].find_one({"_id": event_object_id})

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook event not found"
            )

        if event["status"] == "processed":
            return {
                "success": False,
                "message": "Event already processed successfully"
            }

        # Check if max retries exceeded
        if event.get("processing_attempts", 0) >= event.get("max_retry_attempts", 3):
            return {
                "success": False,
                "message": "Maximum retry attempts exceeded"
            }

        # Reset status and retry
        await mongodb.database["webhook_events"].update_one(
            {"_id": event_object_id},
            {
                "$set": {
                    "status": "pending",
                    "error_message": None,
                    "error_stack": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Process the webhook again
        result = await payment_service.handle_webhook(
            event=event["event_type"],
            payload=event["payload"],
            event_id=event["event_id"],
            source_ip=event.get("source_ip")
        )

        return {
            "success": True,
            "message": "Webhook event retried",
            "result": result
        }

    except Exception as e:
        logger.error(f"Failed to retry webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/webhooks/stats")
async def get_webhook_stats(
    days: int = Query(7, le=90, description="Number of days to analyze"),
    admin_user: User = Depends(require_admin)
):
    """
    Get webhook processing statistics
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get all events in timeframe
        events = await mongodb.database["webhook_events"].find({
            "created_at": {"$gte": start_date}
        }).to_list(None)

        stats = {
            "total_events": len(events),
            "by_status": {
                "pending": sum(1 for e in events if e["status"] == "pending"),
                "processing": sum(1 for e in events if e["status"] == "processing"),
                "processed": sum(1 for e in events if e["status"] == "processed"),
                "failed": sum(1 for e in events if e["status"] == "failed")
            },
            "by_event_type": {},
            "success_rate": 0.0,
            "average_processing_attempts": 0.0,
            "timeframe_days": days
        }

        # Count by event type
        for event in events:
            event_type = event["event_type"]
            if event_type not in stats["by_event_type"]:
                stats["by_event_type"][event_type] = 0
            stats["by_event_type"][event_type] += 1

        # Calculate success rate
        completed = stats["by_status"]["processed"] + stats["by_status"]["failed"]
        if completed > 0:
            stats["success_rate"] = round(
                (stats["by_status"]["processed"] / completed) * 100, 2
            )

        # Calculate average attempts
        if events:
            total_attempts = sum(e.get("processing_attempts", 0) for e in events)
            stats["average_processing_attempts"] = round(total_attempts / len(events), 2)

        return stats

    except Exception as e:
        logger.error(f"Failed to get webhook stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== DUNNING MANAGEMENT =====

@router.get("/dunning/attempts")
async def list_dunning_attempts(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None),
    admin_user: User = Depends(require_admin)
):
    """
    List all dunning attempts
    """
    query = {}
    if status_filter:
        query["status"] = status_filter

    total = await mongodb.database["dunning_attempts"].count_documents(query)

    attempts = await mongodb.database["dunning_attempts"].find(query).sort(
        "created_at", -1
    ).skip(offset).limit(limit).to_list(limit)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "attempts": [
            {
                "id": str(attempt["_id"]),
                "subscription_id": str(attempt["subscription_id"]),
                "user_id": str(attempt["user_id"]),
                "attempt_number": attempt["attempt_number"],
                "status": attempt["status"],
                "scheduled_at": attempt["scheduled_at"],
                "attempted_at": attempt.get("attempted_at"),
                "result_status": attempt.get("result_status"),
                "error_message": attempt.get("error_message"),
                "email_sent": attempt.get("email_sent", False),
                "created_at": attempt["created_at"]
            }
            for attempt in attempts
        ]
    }


@router.get("/dunning/stats")
async def get_dunning_stats(
    days: int = Query(30, le=365),
    admin_user: User = Depends(require_admin)
):
    """
    Get dunning process statistics and recovery rate
    """
    try:
        stats = await dunning_service.get_dunning_stats()

        # Get recent dunning attempts
        start_date = datetime.utcnow() - timedelta(days=days)
        recent_attempts = await mongodb.database["dunning_attempts"].find({
            "created_at": {"$gte": start_date}
        }).to_list(None)

        stats["recent_attempts"] = len(recent_attempts)
        stats["timeframe_days"] = days

        return stats

    except Exception as e:
        logger.error(f"Failed to get dunning stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/dunning/process-pending")
async def process_pending_dunning(
    admin_user: User = Depends(require_admin)
):
    """
    Manually trigger processing of pending dunning attempts
    Normally runs via cron job, but can be triggered manually
    """
    try:
        result = await dunning_service.process_pending_retries()
        return {
            "success": True,
            "message": "Pending dunning attempts processed",
            "result": result
        }

    except Exception as e:
        logger.error(f"Failed to process dunning: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== SUBSCRIPTION MANAGEMENT =====

@router.get("/subscriptions")
async def list_all_subscriptions(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None),
    plan_filter: Optional[str] = Query(None),
    admin_user: User = Depends(require_admin)
):
    """
    List all subscriptions (admin view)
    """
    query = {}
    if status_filter:
        query["status"] = status_filter
    if plan_filter:
        query["plan"] = plan_filter

    total = await mongodb.database["subscriptions"].count_documents(query)

    subscriptions = await mongodb.database["subscriptions"].find(query).sort(
        "created_at", -1
    ).skip(offset).limit(limit).to_list(limit)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "subscriptions": [
            {
                "id": str(sub["_id"]),
                "user_id": str(sub["user_id"]),
                "plan": sub["plan"],
                "status": sub["status"],
                "provider": sub["provider"],
                "amount": sub["amount"],
                "currency": sub["currency"],
                "period_start": sub["period_start"],
                "period_end": sub["period_end"],
                "cancel_at_period_end": sub.get("cancel_at_period_end", False),
                "canceled_at": sub.get("canceled_at"),
                "last_payment_at": sub.get("last_payment_at"),
                "created_at": sub["created_at"]
            }
            for sub in subscriptions
        ]
    }


@router.get("/subscriptions/stats")
async def get_subscription_stats(
    admin_user: User = Depends(require_admin)
):
    """
    Get subscription statistics for business insights
    """
    try:
        # Get all subscriptions
        all_subs = await mongodb.database["subscriptions"].find({}).to_list(None)

        stats = {
            "total_subscriptions": len(all_subs),
            "by_status": {
                "active": sum(1 for s in all_subs if s["status"] == "active"),
                "canceled": sum(1 for s in all_subs if s["status"] == "canceled"),
                "past_due": sum(1 for s in all_subs if s["status"] == "past_due"),
                "expired": sum(1 for s in all_subs if s["status"] == "expired")
            },
            "by_plan": {},
            "mrr": 0.0,  # Monthly Recurring Revenue
            "arr": 0.0   # Annual Recurring Revenue
        }

        # Count by plan
        for sub in all_subs:
            plan = sub["plan"]
            if plan not in stats["by_plan"]:
                stats["by_plan"][plan] = 0
            stats["by_plan"][plan] += 1

            # Calculate MRR (only active subscriptions)
            if sub["status"] == "active":
                stats["mrr"] += sub.get("amount", 0)

        # Calculate ARR
        stats["arr"] = stats["mrr"] * 12

        return stats

    except Exception as e:
        logger.error(f"Failed to get subscription stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

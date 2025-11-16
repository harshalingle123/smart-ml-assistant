from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.mongodb import mongodb
from app.models.mongodb_models import User, AlertConfig
from app.schemas.direct_access_schemas import (
    UsageStats,
    CostBreakdown,
    AlertConfigRequest
)
from app.dependencies import get_current_user
from app.services.usage_tracker import usage_tracker
from bson import ObjectId
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/dashboard", tags=["Usage Dashboard"])


@router.get("/usage", response_model=UsageStats)
async def get_usage_statistics(
    timeframe: str = Query(default="30d", regex="^(1h|24h|7d|30d)$"),
    current_user: User = Depends(get_current_user)
):
    stats = await usage_tracker.get_usage_stats(current_user.id, timeframe)

    by_model = await usage_tracker.get_usage_by_model(current_user.id, timeframe)

    time_series = await usage_tracker.get_time_series(current_user.id, timeframe)

    return UsageStats(
        total_requests=stats["total_requests"],
        successful_requests=stats["successful_requests"],
        failed_requests=stats["failed_requests"],
        average_latency_ms=stats["average_latency_ms"],
        by_model=by_model,
        time_series=time_series
    )


@router.get("/costs", response_model=CostBreakdown)
async def get_cost_breakdown(
    current_user: User = Depends(get_current_user)
):
    by_model = await usage_tracker.get_usage_by_model(current_user.id, "30d")

    total_cost = 0.0
    free_tier_used = 0
    paid_requests = 0

    for model_id, model_stats in by_model.items():
        total_cost += model_stats["cost"]
        free_tier_used += model_stats["free_tier_used"]
        if model_stats["cost"] > 0:
            paid_requests += model_stats["requests"]

    stats = await usage_tracker.get_usage_stats(current_user.id, "7d")
    weekly_requests = stats["total_requests"]
    daily_average = weekly_requests / 7 if weekly_requests > 0 else 0
    projected_monthly_requests = int(daily_average * 30)

    projected_cost = 0.0
    for model_id, model_stats in by_model.items():
        model_requests = model_stats["requests"]
        if weekly_requests > 0:
            model_ratio = model_requests / weekly_requests
            projected_model_requests = int(projected_monthly_requests * model_ratio)

            api_key = await mongodb.database["direct_access_keys"].find_one({
                "user_id": current_user.id,
                "model_id": model_id
            })

            if api_key:
                free_tier_limit = api_key["free_tier_limit"]
                projected_cost += usage_tracker.calculate_cost(
                    model_id,
                    projected_model_requests,
                    free_tier_limit
                )

    return CostBreakdown(
        current_month={
            "total_cost": round(total_cost, 4),
            "free_tier_used": free_tier_used,
            "paid_requests": paid_requests
        },
        projected_month={
            "estimated_cost": round(projected_cost, 2),
            "based_on_current_rate": True,
            "projected_requests": projected_monthly_requests
        },
        by_model=by_model
    )


@router.post("/alerts", status_code=status.HTTP_201_CREATED)
async def configure_alert(
    alert_request: AlertConfigRequest,
    current_user: User = Depends(get_current_user)
):
    if not ObjectId.is_valid(alert_request.api_key_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key ID"
        )

    api_key = await mongodb.database["direct_access_keys"].find_one({
        "_id": ObjectId(alert_request.api_key_id),
        "user_id": current_user.id
    })

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    existing_alert = await mongodb.database["alert_configs"].find_one({
        "user_id": current_user.id,
        "api_key_id": ObjectId(alert_request.api_key_id)
    })

    if existing_alert:
        await mongodb.database["alert_configs"].update_one(
            {"_id": existing_alert["_id"]},
            {
                "$set": {
                    "threshold": alert_request.threshold,
                    "alert_type": alert_request.alert_type,
                    "recipient": alert_request.recipient
                }
            }
        )
        return {"message": "Alert configuration updated", "alert_id": str(existing_alert["_id"])}

    new_alert = AlertConfig(
        user_id=current_user.id,
        api_key_id=ObjectId(alert_request.api_key_id),
        threshold=alert_request.threshold,
        alert_type=alert_request.alert_type,
        recipient=alert_request.recipient
    )

    result = await mongodb.database["alert_configs"].insert_one(new_alert.dict(by_alias=True))

    return {"message": "Alert configured successfully", "alert_id": str(result.inserted_id)}


@router.get("/alerts")
async def list_alerts(
    current_user: User = Depends(get_current_user)
):
    alerts = await mongodb.database["alert_configs"].find({
        "user_id": current_user.id,
        "enabled": True
    }).to_list(None)

    result = []
    for alert in alerts:
        api_key = await mongodb.database["direct_access_keys"].find_one({
            "_id": alert["api_key_id"]
        })

        result.append({
            "id": str(alert["_id"]),
            "api_key_id": str(alert["api_key_id"]),
            "model_name": api_key["model_name"] if api_key else "Unknown",
            "threshold": alert["threshold"],
            "alert_type": alert["alert_type"],
            "recipient": alert["recipient"],
            "enabled": alert["enabled"],
            "last_triggered_at": alert.get("last_triggered_at").isoformat() if alert.get("last_triggered_at") else None,
            "created_at": alert["created_at"].isoformat()
        })

    return result


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    if not ObjectId.is_valid(alert_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID"
        )

    alert = await mongodb.database["alert_configs"].find_one({
        "_id": ObjectId(alert_id),
        "user_id": current_user.id
    })

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert configuration not found"
        )

    await mongodb.database["alert_configs"].delete_one({"_id": ObjectId(alert_id)})

    return None


@router.get("/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user)
):
    api_keys = await mongodb.database["direct_access_keys"].find({
        "user_id": current_user.id,
        "status": "active"
    }).to_list(None)

    stats_30d = await usage_tracker.get_usage_stats(current_user.id, "30d")
    stats_24h = await usage_tracker.get_usage_stats(current_user.id, "24h")

    total_free_tier = sum(key["free_tier_limit"] for key in api_keys)
    total_used = sum(key["requests_this_month"] for key in api_keys)
    total_remaining = total_free_tier - total_used

    return {
        "active_api_keys": len(api_keys),
        "total_requests_30d": stats_30d["total_requests"],
        "total_requests_24h": stats_24h["total_requests"],
        "average_latency_ms": stats_30d["average_latency_ms"],
        "success_rate": round(
            (stats_30d["successful_requests"] / stats_30d["total_requests"] * 100)
            if stats_30d["total_requests"] > 0 else 0,
            2
        ),
        "free_tier_usage": {
            "total_limit": total_free_tier,
            "total_used": total_used,
            "total_remaining": max(0, total_remaining),
            "usage_percentage": round((total_used / total_free_tier * 100) if total_free_tier > 0 else 0, 2)
        }
    }

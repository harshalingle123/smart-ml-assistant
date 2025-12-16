"""
Subscription Management Service
Handles subscription lifecycle, usage tracking, and limits enforcement
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from bson import ObjectId
from app.mongodb import mongodb
from app.models.mongodb_models import Subscription, Plan, UsageRecord
import logging

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Manage subscriptions and enforce usage limits"""

    async def get_user_subscription(self, user_id: ObjectId) -> Optional[Dict[str, Any]]:
        """Get user's current subscription with plan details"""
        subscription = await mongodb.database["subscriptions"].find_one(
            {"user_id": user_id, "status": {"$in": ["active", "past_due"]}}
        )

        if not subscription:
            # Return free plan defaults
            return {
                "plan": "free",
                "status": "active",
                "period_start": None,
                "period_end": None,
                "limits": await self.get_plan_limits("free")
            }

        # Get plan limits
        limits = await self.get_plan_limits(subscription["plan"])

        return {
            **subscription,
            "limits": limits
        }

    async def get_plan_limits(self, plan_name: str) -> Dict[str, Any]:
        """Get limits for a specific plan"""
        plan = await mongodb.database["plans"].find_one({"plan": plan_name})

        if not plan:
            # Return default free plan limits
            return {
                "api_hits_per_month": 500,
                "model_generation_per_day": 3,
                "dataset_size_mb": 50,
                "azure_storage_gb": 0.1,
                "training_time_minutes_per_model": 5,
                "concurrent_trainings": 1
            }

        return {
            "api_hits_per_month": plan["api_hits_per_month"],
            "model_generation_per_day": plan["model_generation_per_day"],
            "dataset_size_mb": plan["dataset_size_mb"],
            "azure_storage_gb": plan["azure_storage_gb"],
            "training_time_minutes_per_model": plan["training_time_minutes_per_model"],
            "concurrent_trainings": plan["concurrent_trainings"]
        }

    async def get_usage_stats(self, user_id: ObjectId) -> Dict[str, Any]:
        """Get user's current usage statistics"""
        # Get subscription
        subscription = await self.get_user_subscription(user_id)

        # Get usage record
        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id}
        )

        if not usage_record:
            # Create default usage record
            usage_record = {
                "api_hits_used": 0,
                "models_trained_today": 0,
                "azure_storage_used_mb": 0.0
            }

        limits = subscription["limits"]

        # Calculate usage percentages
        usage_percentage = {
            "api_hits": round((usage_record["api_hits_used"] / limits["api_hits_per_month"]) * 100, 2),
            "models": round((usage_record["models_trained_today"] / limits["model_generation_per_day"]) * 100, 2),
            "storage": round((usage_record["azure_storage_used_mb"] / (limits["azure_storage_gb"] * 1024)) * 100, 2)
        }

        return {
            "user_id": str(user_id),
            "subscription_id": str(subscription.get("_id", "")),
            "plan": subscription["plan"],
            "api_hits_used": usage_record["api_hits_used"],
            "api_hits_limit": limits["api_hits_per_month"],
            "models_trained_today": usage_record["models_trained_today"],
            "models_limit_per_day": limits["model_generation_per_day"],
            "azure_storage_used_mb": usage_record["azure_storage_used_mb"],
            "azure_storage_limit_gb": limits["azure_storage_gb"],
            "billing_cycle_start": usage_record.get("billing_cycle_start"),
            "billing_cycle_end": usage_record.get("billing_cycle_end"),
            "usage_percentage": usage_percentage
        }

    async def check_api_limit(self, user_id: ObjectId) -> bool:
        """Check if user has remaining API hits (including add-ons)"""
        from app.services.addon_service import addon_service

        # Get combined limits (base plan + add-ons)
        combined_limits = await addon_service.calculate_combined_limits(user_id)

        logger.info(f"[SERVICE] Checking API limit for user: {user_id}, total limit: {combined_limits['total_limits']['api_hits_per_month']}")

        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id}
        )

        if not usage_record:
            logger.info(f"[SERVICE] No usage record found for user: {user_id}, allowing request")
            return True  # First request

        api_hits_used = usage_record.get("api_hits_used", 0)
        limit = combined_limits["total_limits"]["api_hits_per_month"]

        logger.info(f"[SERVICE] User {user_id}: {api_hits_used}/{limit} API hits used")

        return api_hits_used < limit

    async def check_model_training_limit(self, user_id: ObjectId) -> bool:
        """Check if user can train more models today (including add-ons)"""
        from app.services.addon_service import addon_service

        # Get combined limits (base plan + add-ons)
        combined_limits = await addon_service.calculate_combined_limits(user_id)

        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id}
        )

        if not usage_record:
            return True  # First training

        # Check if we need to reset daily counter
        last_reset = usage_record.get("last_daily_reset_at", datetime.utcnow())
        if datetime.utcnow().date() > last_reset.date():
            # Reset daily counter
            await mongodb.database["usage_records"].update_one(
                {"_id": usage_record["_id"]},
                {
                    "$set": {
                        "models_trained_today": 0,
                        "last_daily_reset_at": datetime.utcnow()
                    }
                }
            )
            return True

        models_trained = usage_record.get("models_trained_today", 0)
        limit = combined_limits["total_limits"]["model_generation_per_day"]

        return models_trained < limit

    async def check_dataset_size_limit(self, user_id: ObjectId, file_size_mb: float) -> bool:
        """Check if dataset size is within plan limits (including add-ons)"""
        from app.services.addon_service import addon_service

        # Get combined limits (base plan + add-ons)
        combined_limits = await addon_service.calculate_combined_limits(user_id)
        limit_mb = combined_limits["total_limits"]["dataset_size_mb"]

        return file_size_mb <= limit_mb

    async def check_storage_limit(self, user_id: ObjectId, additional_mb: float) -> bool:
        """Check if user has enough storage space (including add-ons)"""
        from app.services.addon_service import addon_service

        # Get combined limits (base plan + add-ons)
        combined_limits = await addon_service.calculate_combined_limits(user_id)

        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id}
        )

        current_usage = usage_record.get("azure_storage_used_mb", 0.0) if usage_record else 0.0
        limit_mb = combined_limits["total_limits"]["azure_storage_gb"] * 1024

        return (current_usage + additional_mb) <= limit_mb

    async def increment_api_usage(self, user_id: ObjectId) -> None:
        """Increment API hit counter"""
        logger.info(f"[API USAGE] Incrementing API usage for user: {user_id}")

        # Get or create usage record
        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id}
        )

        if not usage_record:
            logger.info(f"[API USAGE] Creating new usage record for user: {user_id}")
            # Create usage record
            subscription = await self.get_user_subscription(user_id)
            period_start = datetime.utcnow()
            period_end = period_start + timedelta(days=30)

            new_usage = UsageRecord(
                user_id=user_id,
                subscription_id=subscription.get("_id"),
                api_hits_used=1,
                models_trained_today=0,
                azure_storage_used_mb=0.0,
                billing_cycle_start=period_start,
                billing_cycle_end=period_end
            )
            result = await mongodb.database["usage_records"].insert_one(
                new_usage.model_dump(by_alias=True, mode='json')
            )
            logger.info(f"[API USAGE] Created usage record: {result.inserted_id}, initial count: 1")
        else:
            logger.info(f"[API USAGE] Updating existing usage record for user: {user_id}, current count: {usage_record.get('api_hits_used', 0)}")
            result = await mongodb.database["usage_records"].update_one(
                {"_id": usage_record["_id"]},
                {
                    "$inc": {"api_hits_used": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            logger.info(f"[API USAGE] Updated {result.modified_count} records, new count: {usage_record.get('api_hits_used', 0) + 1}")

    async def increment_model_training(self, user_id: ObjectId) -> None:
        """Increment model training counter"""
        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id}
        )

        if usage_record:
            # Check if we need to reset daily counter
            last_reset = usage_record.get("last_daily_reset_at", datetime.utcnow())
            if datetime.utcnow().date() > last_reset.date():
                # Reset daily counter
                await mongodb.database["usage_records"].update_one(
                    {"_id": usage_record["_id"]},
                    {
                        "$set": {
                            "models_trained_today": 1,
                            "last_daily_reset_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            else:
                await mongodb.database["usage_records"].update_one(
                    {"_id": usage_record["_id"]},
                    {
                        "$inc": {"models_trained_today": 1},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )

    async def update_storage_usage(self, user_id: ObjectId, size_mb: float) -> None:
        """Update Azure storage usage"""
        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id}
        )

        if usage_record:
            await mongodb.database["usage_records"].update_one(
                {"_id": usage_record["_id"]},
                {
                    "$inc": {"azure_storage_used_mb": size_mb},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

    async def get_all_plans(self) -> List[Dict[str, Any]]:
        """Get all available subscription plans"""
        plans = await mongodb.database["plans"].find({"is_active": True}).to_list(None)
        return plans

    async def reset_monthly_usage(self) -> None:
        """Reset monthly usage counters (run via cron job)"""
        # Find all subscriptions with expired billing cycles
        now = datetime.utcnow()
        expired_records = await mongodb.database["usage_records"].find(
            {"billing_cycle_end": {"$lte": now}}
        ).to_list(None)

        for record in expired_records:
            # Calculate new billing cycle
            new_start = now
            new_end = new_start + timedelta(days=30)

            await mongodb.database["usage_records"].update_one(
                {"_id": record["_id"]},
                {
                    "$set": {
                        "api_hits_used": 0,
                        "models_trained_today": 0,
                        "billing_cycle_start": new_start,
                        "billing_cycle_end": new_end,
                        "last_reset_at": now,
                        "updated_at": now
                    }
                }
            )

        logger.info(f"Reset monthly usage for {len(expired_records)} users")

    async def check_expired_subscriptions(self) -> None:
        """Check and update expired subscriptions (run via cron job)"""
        now = datetime.utcnow()

        # Find subscriptions that have expired
        expired_subs = await mongodb.database["subscriptions"].find(
            {
                "status": "active",
                "period_end": {"$lte": now},
                "cancel_at_period_end": False
            }
        ).to_list(None)

        for sub in expired_subs:
            # Mark as expired
            await mongodb.database["subscriptions"].update_one(
                {"_id": sub["_id"]},
                {
                    "$set": {
                        "status": "expired",
                        "updated_at": now
                    }
                }
            )

            # Downgrade user to free plan
            await mongodb.database["users"].update_one(
                {"_id": sub["user_id"]},
                {
                    "$set": {
                        "current_plan": "free",
                        "updated_at": now
                    }
                }
            )

        logger.info(f"Marked {len(expired_subs)} subscriptions as expired")

        # Handle subscriptions that should be canceled at period end
        cancel_at_end = await mongodb.database["subscriptions"].find(
            {
                "status": "active",
                "period_end": {"$lte": now},
                "cancel_at_period_end": True
            }
        ).to_list(None)

        for sub in cancel_at_end:
            await mongodb.database["subscriptions"].update_one(
                {"_id": sub["_id"]},
                {
                    "$set": {
                        "status": "canceled",
                        "updated_at": now
                    }
                }
            )

            # Downgrade to free
            await mongodb.database["users"].update_one(
                {"_id": sub["user_id"]},
                {
                    "$set": {
                        "current_plan": "free",
                        "updated_at": now
                    }
                }
            )

        logger.info(f"Canceled {len(cancel_at_end)} subscriptions at period end")

    async def check_labeling_limit(self, user_id: ObjectId, num_files: int) -> bool:
        """Check if user can label more files this month"""
        from app.services.addon_service import addon_service

        # Get combined limits (base plan + add-ons)
        combined_limits = await addon_service.calculate_combined_limits(user_id)

        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id}
        )

        if not usage_record:
            return True  # First labeling

        files_labeled = usage_record.get("labeling_files_used", 0)
        limit = combined_limits["total_limits"].get("labeling_files_per_month", 50)

        if files_labeled + num_files > limit:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Labeling limit exceeded. You have used {files_labeled}/{limit} files this month. Upgrade your plan to label more files."
            )

        return True

    async def check_labeling_file_size(self, user_id: ObjectId, file_size_bytes: int) -> bool:
        """Check if file size is within labeling limits"""
        from app.services.addon_service import addon_service

        # Get combined limits (base plan + add-ons)
        combined_limits = await addon_service.calculate_combined_limits(user_id)
        limit_mb = combined_limits["total_limits"].get("labeling_file_size_mb", 10)
        file_size_mb = file_size_bytes / (1024 * 1024)

        if file_size_mb > limit_mb:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size_mb:.2f} MB) exceeds limit of {limit_mb} MB. Upgrade your plan for larger files."
            )

        return True

    async def increment_labeling_usage(self, user_id: ObjectId) -> None:
        """Increment labeling file counter"""
        logger.info(f"[LABELING USAGE] Incrementing labeling usage for user: {user_id}")

        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id}
        )

        if not usage_record:
            logger.info(f"[LABELING USAGE] Creating new usage record for user: {user_id}")
            subscription = await self.get_user_subscription(user_id)
            period_start = datetime.utcnow()
            period_end = period_start + timedelta(days=30)

            new_usage = UsageRecord(
                user_id=user_id,
                subscription_id=subscription.get("_id"),
                api_hits_used=0,
                models_trained_today=0,
                azure_storage_used_mb=0.0,
                labeling_files_used=1,
                billing_cycle_start=period_start,
                billing_cycle_end=period_end
            )
            await mongodb.database["usage_records"].insert_one(
                new_usage.model_dump(by_alias=True, mode='json')
            )
            logger.info(f"[LABELING USAGE] Created usage record with 1 labeled file")
        else:
            logger.info(f"[LABELING USAGE] Updating existing usage record for user: {user_id}")
            await mongodb.database["usage_records"].update_one(
                {"_id": usage_record["_id"]},
                {
                    "$inc": {"labeling_files_used": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            logger.info(f"[LABELING USAGE] Incremented labeling files used")


# Global subscription service instance
subscription_service = SubscriptionService()

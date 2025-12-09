"""
Subscription Middleware
Enforces usage limits based on user's subscription plan
"""
from fastapi import HTTPException, status
from app.services.subscription_service import subscription_service
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class SubscriptionLimits:
    """Enforce subscription-based usage limits"""

    @staticmethod
    async def check_api_limit(user_id: ObjectId):
        """Check if user has remaining API hits"""
        logger.info(f"[MIDDLEWARE] Checking API limit for user: {user_id}")
        has_limit = await subscription_service.check_api_limit(user_id)

        if not has_limit:
            logger.warning(f"[MIDDLEWARE] API limit exceeded for user: {user_id}")
            subscription = await subscription_service.get_user_subscription(user_id)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "API limit exceeded",
                    "message": f"You have reached your monthly limit of {subscription['limits']['api_hits_per_month']} API hits.",
                    "current_plan": subscription["plan"],
                    "upgrade_required": True
                }
            )

        # Increment usage
        logger.info(f"[MIDDLEWARE] API limit OK, incrementing usage for user: {user_id}")
        await subscription_service.increment_api_usage(user_id)
        logger.info(f"[MIDDLEWARE] API usage incremented successfully for user: {user_id}")

    @staticmethod
    async def check_model_training_limit(user_id: ObjectId):
        """Check if user can train more models today"""
        has_limit = await subscription_service.check_model_training_limit(user_id)

        if not has_limit:
            subscription = await subscription_service.get_user_subscription(user_id)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Model training limit exceeded",
                    "message": f"You have reached your daily limit of {subscription['limits']['model_generation_per_day']} model trainings.",
                    "current_plan": subscription["plan"],
                    "upgrade_required": True,
                    "reset_time": "Limit resets at midnight UTC"
                }
            )

        # Increment usage
        await subscription_service.increment_model_training(user_id)

    @staticmethod
    async def check_dataset_size_limit(user_id: ObjectId, file_size_mb: float):
        """Check if dataset size is within plan limits"""
        has_limit = await subscription_service.check_dataset_size_limit(user_id, file_size_mb)

        if not has_limit:
            subscription = await subscription_service.get_user_subscription(user_id)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "Dataset size limit exceeded",
                    "message": f"Dataset size ({file_size_mb:.2f} MB) exceeds your plan limit of {subscription['limits']['dataset_size_mb']} MB.",
                    "current_plan": subscription["plan"],
                    "upgrade_required": True
                }
            )

    @staticmethod
    async def check_storage_limit(user_id: ObjectId, additional_mb: float):
        """Check if user has enough storage space"""
        has_limit = await subscription_service.check_storage_limit(user_id, additional_mb)

        if not has_limit:
            subscription = await subscription_service.get_user_subscription(user_id)
            usage = await subscription_service.get_usage_stats(user_id)
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail={
                    "error": "Storage limit exceeded",
                    "message": f"Adding {additional_mb:.2f} MB would exceed your storage limit of {subscription['limits']['azure_storage_gb']} GB.",
                    "current_usage_mb": usage["azure_storage_used_mb"],
                    "current_plan": subscription["plan"],
                    "upgrade_required": True
                }
            )

        # Update storage usage
        await subscription_service.update_storage_usage(user_id, additional_mb)

    @staticmethod
    async def get_plan_feature(user_id: ObjectId, feature: str) -> any:
        """Get specific plan feature value"""
        subscription = await subscription_service.get_user_subscription(user_id)
        return subscription["limits"].get(feature)


subscription_limits = SubscriptionLimits()

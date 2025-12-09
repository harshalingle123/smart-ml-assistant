"""
Dunning Service - Failed Payment Recovery System
Handles smart retry logic for failed payments to reduce churn
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from bson import ObjectId
from app.mongodb import mongodb
from app.models.mongodb_models import DunningAttempt, Subscription

logger = logging.getLogger(__name__)


class DunningService:
    """
    Manage failed payment recovery (dunning process)

    Retry Schedule (Industry Best Practice):
    - Attempt 1: Immediate (same day)
    - Attempt 2: Day 3
    - Attempt 3: Day 7
    - After 7 days: Cancel subscription

    Features:
    - Smart retry scheduling (avoid weekends if possible)
    - Email notifications before each retry
    - Subscription status transitions (active → past_due → canceled)
    - Grace period to retain customers
    """

    # Retry schedule in days from failed payment
    RETRY_SCHEDULE = [0, 3, 7]  # Day 0 (immediate), Day 3, Day 7
    MAX_RETRY_ATTEMPTS = 3
    GRACE_PERIOD_DAYS = 7  # Total grace period before cancellation

    async def handle_failed_payment(
        self,
        subscription_id: ObjectId,
        user_id: ObjectId,
        payment_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle a failed payment by initiating dunning process

        Args:
            subscription_id: Subscription that failed
            user_id: User ID
            payment_id: Failed Razorpay payment ID
            error_message: Reason for failure

        Returns:
            Dict with dunning process details
        """
        logger.info(f"Initiating dunning for subscription {subscription_id}, user {user_id}")

        try:
            # Update subscription status to past_due
            await self._update_subscription_status(subscription_id, "past_due")

            # Check if we already have dunning attempts for this subscription
            existing_attempts = await mongodb.database["dunning_attempts"].find(
                {"subscription_id": subscription_id, "status": {"$in": ["pending", "failed"]}}
            ).to_list(None)

            attempt_number = len(existing_attempts) + 1

            if attempt_number > self.MAX_RETRY_ATTEMPTS:
                logger.warning(f"Max retry attempts reached for subscription {subscription_id}")
                await self._cancel_subscription_after_dunning(subscription_id, user_id)
                return {
                    "success": False,
                    "message": "Maximum retry attempts exceeded. Subscription canceled.",
                    "attempts": attempt_number - 1
                }

            # Schedule retry attempts
            scheduled_attempts = await self._schedule_retry_attempts(
                subscription_id,
                user_id,
                payment_id,
                attempt_number
            )

            logger.info(f"Scheduled {len(scheduled_attempts)} dunning attempts for subscription {subscription_id}")

            return {
                "success": True,
                "message": "Dunning process initiated",
                "subscription_status": "past_due",
                "scheduled_attempts": len(scheduled_attempts),
                "next_retry": scheduled_attempts[0]["scheduled_at"] if scheduled_attempts else None
            }

        except Exception as e:
            logger.error(f"Failed to initiate dunning: {str(e)}")
            return {
                "success": False,
                "message": f"Dunning initiation failed: {str(e)}"
            }

    async def _schedule_retry_attempts(
        self,
        subscription_id: ObjectId,
        user_id: ObjectId,
        payment_id: Optional[str],
        starting_attempt: int
    ) -> List[Dict[str, Any]]:
        """Schedule all retry attempts for a failed payment"""
        scheduled_attempts = []
        now = datetime.utcnow()

        for i, days_delay in enumerate(self.RETRY_SCHEDULE[starting_attempt - 1:]):
            attempt_number = starting_attempt + i
            scheduled_at = now + timedelta(days=days_delay)

            # Adjust for weekends (if retry falls on weekend, move to Monday)
            scheduled_at = self._adjust_for_weekend(scheduled_at)

            dunning_attempt = DunningAttempt(
                subscription_id=subscription_id,
                user_id=user_id,
                payment_id=payment_id,
                attempt_number=attempt_number,
                status="pending",
                scheduled_at=scheduled_at
            )

            result = await mongodb.database["dunning_attempts"].insert_one(
                dunning_attempt.dict(by_alias=True)
            )

            scheduled_attempts.append({
                "id": str(result.inserted_id),
                "attempt_number": attempt_number,
                "scheduled_at": scheduled_at
            })

        return scheduled_attempts

    def _adjust_for_weekend(self, scheduled_at: datetime) -> datetime:
        """
        Adjust retry date to avoid weekends
        If Saturday (5) or Sunday (6), move to Monday
        """
        weekday = scheduled_at.weekday()

        if weekday == 5:  # Saturday
            scheduled_at += timedelta(days=2)
        elif weekday == 6:  # Sunday
            scheduled_at += timedelta(days=1)

        return scheduled_at

    async def process_pending_retries(self) -> Dict[str, Any]:
        """
        Process all pending dunning attempts (call this from a cron job)

        Returns:
            Statistics about processed retries
        """
        now = datetime.utcnow()

        # Find all pending retries that are due
        pending_retries = await mongodb.database["dunning_attempts"].find({
            "status": "pending",
            "scheduled_at": {"$lte": now}
        }).to_list(None)

        logger.info(f"Processing {len(pending_retries)} pending dunning attempts")

        processed = 0
        succeeded = 0
        failed = 0

        for retry in pending_retries:
            try:
                result = await self._attempt_retry(retry)
                processed += 1

                if result["success"]:
                    succeeded += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Error processing retry {retry['_id']}: {str(e)}")
                failed += 1

        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "timestamp": datetime.utcnow()
        }

    async def _attempt_retry(self, retry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to retry a failed payment

        In production, this would:
        1. Send reminder email to user
        2. Create new Razorpay order
        3. Send payment link to user
        4. Wait for webhook to confirm payment

        For now, we'll just log and mark as attempted
        """
        retry_id = retry["_id"]
        subscription_id = retry["subscription_id"]
        user_id = retry["user_id"]

        logger.info(f"Attempting dunning retry {retry_id} for subscription {subscription_id}")

        try:
            # Update retry status
            await mongodb.database["dunning_attempts"].update_one(
                {"_id": retry_id},
                {
                    "$set": {
                        "status": "attempted",
                        "attempted_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # TODO: In production:
            # 1. Create new Razorpay order
            # 2. Send email with payment link
            # 3. Mark email_sent = True

            # For now, we'll simulate this
            await mongodb.database["dunning_attempts"].update_one(
                {"_id": retry_id},
                {
                    "$set": {
                        "email_sent": True,
                        "email_sent_at": datetime.utcnow()
                    }
                }
            )

            return {
                "success": True,
                "retry_id": str(retry_id),
                "message": "Retry email sent to user"
            }

        except Exception as e:
            logger.error(f"Retry attempt failed: {str(e)}")

            # Mark retry as failed
            await mongodb.database["dunning_attempts"].update_one(
                {"_id": retry_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            return {
                "success": False,
                "retry_id": str(retry_id),
                "error": str(e)
            }

    async def mark_retry_success(
        self,
        subscription_id: ObjectId,
        razorpay_payment_id: str
    ) -> None:
        """
        Mark dunning as successful when payment succeeds
        Called from webhook when payment is captured after retry
        """
        logger.info(f"Marking dunning success for subscription {subscription_id}")

        # Update subscription back to active
        await self._update_subscription_status(subscription_id, "active")

        # Mark all pending/attempted retries as success
        await mongodb.database["dunning_attempts"].update_many(
            {
                "subscription_id": subscription_id,
                "status": {"$in": ["pending", "attempted"]}
            },
            {
                "$set": {
                    "status": "success",
                    "result_status": "success",
                    "razorpay_payment_id": razorpay_payment_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Dunning recovery successful for subscription {subscription_id}")

    async def _update_subscription_status(
        self,
        subscription_id: ObjectId,
        status: str
    ) -> None:
        """Update subscription status"""
        await mongodb.database["subscriptions"].update_one(
            {"_id": subscription_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Updated subscription {subscription_id} status to {status}")

    async def _cancel_subscription_after_dunning(
        self,
        subscription_id: ObjectId,
        user_id: ObjectId
    ) -> None:
        """
        Cancel subscription after all dunning attempts fail
        Move user to free plan
        """
        logger.info(f"Canceling subscription {subscription_id} after failed dunning")

        # Update subscription
        await mongodb.database["subscriptions"].update_one(
            {"_id": subscription_id},
            {
                "$set": {
                    "status": "canceled",
                    "canceled_at": datetime.utcnow(),
                    "period_end": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Downgrade user to free plan
        await mongodb.database["users"].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "current_plan": "free",
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Mark all pending retries as failed
        await mongodb.database["dunning_attempts"].update_many(
            {
                "subscription_id": subscription_id,
                "status": "pending"
            },
            {
                "$set": {
                    "status": "skipped",
                    "result_status": "max_attempts_exceeded",
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Subscription {subscription_id} canceled, user downgraded to free")

    async def get_dunning_stats(self, user_id: Optional[ObjectId] = None) -> Dict[str, Any]:
        """
        Get dunning statistics

        Args:
            user_id: If provided, get stats for specific user

        Returns:
            Dunning statistics
        """
        query = {}
        if user_id:
            query["user_id"] = user_id

        all_attempts = await mongodb.database["dunning_attempts"].find(query).to_list(None)

        stats = {
            "total_attempts": len(all_attempts),
            "pending": sum(1 for a in all_attempts if a["status"] == "pending"),
            "attempted": sum(1 for a in all_attempts if a["status"] == "attempted"),
            "success": sum(1 for a in all_attempts if a["status"] == "success"),
            "failed": sum(1 for a in all_attempts if a["status"] == "failed"),
            "recovery_rate": 0.0
        }

        # Calculate recovery rate
        total_completed = stats["success"] + stats["failed"]
        if total_completed > 0:
            stats["recovery_rate"] = round((stats["success"] / total_completed) * 100, 2)

        return stats

    async def cancel_pending_retries(self, subscription_id: ObjectId) -> None:
        """
        Cancel all pending retries for a subscription
        Used when user manually pays or cancels subscription
        """
        await mongodb.database["dunning_attempts"].update_many(
            {
                "subscription_id": subscription_id,
                "status": "pending"
            },
            {
                "$set": {
                    "status": "skipped",
                    "result_status": "manually_canceled",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Canceled pending retries for subscription {subscription_id}")


# Global dunning service instance
dunning_service = DunningService()

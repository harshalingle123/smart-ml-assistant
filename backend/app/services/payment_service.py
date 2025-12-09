"""
Razorpay Payment Gateway Service
Handles payment processing, order creation, and subscription management
"""
import razorpay
import hmac
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings
from bson import ObjectId
from app.mongodb import mongodb
from app.models.mongodb_models import Payment, Subscription, Plan, UsageRecord
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """Handle Razorpay payment operations"""

    def __init__(self):
        self.client = None
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            self.client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            logger.info("Razorpay client initialized")
        else:
            logger.warning("Razorpay credentials not configured")

    def is_configured(self) -> bool:
        """Check if Razorpay is properly configured"""
        return self.client is not None

    async def get_plan_details(self, plan_name: str) -> Optional[Plan]:
        """Get plan details from database"""
        plan_doc = await mongodb.database["plans"].find_one({"plan": plan_name})
        if plan_doc:
            return Plan(**plan_doc)
        return None

    async def create_order(
        self,
        user_id: ObjectId,
        plan_name: str
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order for one-time payment
        Returns order details for frontend integration
        """
        if not self.is_configured():
            raise Exception("Razorpay not configured")

        # Get plan details
        plan = await self.get_plan_details(plan_name)
        if not plan:
            raise Exception(f"Plan '{plan_name}' not found")

        if plan.price_monthly <= 0:
            raise Exception("Cannot create order for free plan")

        # Create Razorpay order
        amount_paise = int(plan.price_monthly * 100)  # Convert to paise
        # Receipt must be <= 40 chars. Use last 12 chars of user_id + timestamp
        timestamp = int(datetime.utcnow().timestamp())
        receipt = f"ord_{str(user_id)[-12:]}_{timestamp}"
        order_data = {
            "amount": amount_paise,
            "currency": plan.currency,
            "receipt": receipt,
            "notes": {
                "user_id": str(user_id),
                "plan": plan_name,
                "description": f"Subscription: {plan.name}"
            }
        }

        try:
            razorpay_order = self.client.order.create(data=order_data)
            logger.info(f"Razorpay order created: {razorpay_order['id']} for user {user_id}")

            return {
                "order_id": razorpay_order["id"],
                "amount": plan.price_monthly,
                "currency": plan.currency,
                "key_id": settings.RAZORPAY_KEY_ID,
                "plan": plan_name,
                "plan_name": plan.name
            }
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {str(e)}")
            raise Exception(f"Payment order creation failed: {str(e)}")

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature
        Returns True if signature is valid
        """
        if not self.is_configured():
            return False

        try:
            # Generate expected signature
            message = f"{order_id}|{payment_id}"
            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False

    async def process_payment(
        self,
        user_id: ObjectId,
        plan_name: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> Dict[str, Any]:
        """
        Process and verify payment, create/update subscription
        """
        # Verify signature
        if not self.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        ):
            raise Exception("Invalid payment signature")

        # Fetch payment details from Razorpay
        try:
            payment_details = self.client.payment.fetch(razorpay_payment_id)
            logger.info(f"Payment verified: {razorpay_payment_id}")
        except Exception as e:
            logger.error(f"Failed to fetch payment details: {str(e)}")
            raise Exception("Payment verification failed")

        # Get plan details
        plan = await self.get_plan_details(plan_name)
        if not plan:
            raise Exception(f"Plan '{plan_name}' not found")

        # Calculate billing period (monthly)
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)

        # Check if user already has a subscription
        existing_sub = await mongodb.database["subscriptions"].find_one(
            {"user_id": user_id, "status": {"$in": ["active", "past_due"]}}
        )

        if existing_sub:
            # Update existing subscription
            subscription_id = existing_sub["_id"]
            await mongodb.database["subscriptions"].update_one(
                {"_id": subscription_id},
                {
                    "$set": {
                        "plan": plan_name,
                        "status": "active",
                        "period_start": period_start,
                        "period_end": period_end,
                        "amount": plan.price_monthly,
                        "last_payment_at": datetime.utcnow(),
                        "next_billing_date": period_end,
                        "razorpay_plan_id": plan.razorpay_plan_id,
                        "cancel_at_period_end": False,
                        "canceled_at": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Updated subscription {subscription_id} for user {user_id}")
        else:
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                plan=plan_name,
                provider="razorpay",
                status="active",
                period_start=period_start,
                period_end=period_end,
                amount=plan.price_monthly,
                currency=plan.currency,
                last_payment_at=datetime.utcnow(),
                next_billing_date=period_end,
                razorpay_plan_id=plan.razorpay_plan_id
            )
            result = await mongodb.database["subscriptions"].insert_one(
                subscription.dict(by_alias=True)
            )
            subscription_id = result.inserted_id
            logger.info(f"Created subscription {subscription_id} for user {user_id}")

        # Update user's current_plan and subscription_id
        await mongodb.database["users"].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "current_plan": plan_name,
                    "subscription_id": subscription_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Create or update usage record
        usage_record = await mongodb.database["usage_records"].find_one(
            {"user_id": user_id, "subscription_id": subscription_id}
        )

        if not usage_record:
            new_usage = UsageRecord(
                user_id=user_id,
                subscription_id=subscription_id,
                api_hits_used=0,
                models_trained_today=0,
                azure_storage_used_mb=0.0,
                billing_cycle_start=period_start,
                billing_cycle_end=period_end
            )
            await mongodb.database["usage_records"].insert_one(
                new_usage.dict(by_alias=True)
            )
            logger.info(f"Created usage record for user {user_id}")
        else:
            # Reset usage for new billing cycle
            await mongodb.database["usage_records"].update_one(
                {"_id": usage_record["_id"]},
                {
                    "$set": {
                        "api_hits_used": 0,
                        "models_trained_today": 0,
                        "billing_cycle_start": period_start,
                        "billing_cycle_end": period_end,
                        "last_reset_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

        # Record payment transaction
        payment_record = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=plan.price_monthly,
            currency=plan.currency,
            status="success",
            payment_method=payment_details.get("method", "unknown"),
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            razorpay_signature=razorpay_signature,
            description=f"Subscription: {plan.name}"
        )
        await mongodb.database["payments"].insert_one(
            payment_record.dict(by_alias=True)
        )

        return {
            "success": True,
            "subscription_id": str(subscription_id),
            "plan": plan_name,
            "message": "Subscription activated successfully"
        }

    async def cancel_subscription(
        self,
        user_id: ObjectId,
        cancel_at_period_end: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel user subscription
        If cancel_at_period_end=True, subscription remains active until period ends
        """
        subscription = await mongodb.database["subscriptions"].find_one(
            {"user_id": user_id, "status": "active"}
        )

        if not subscription:
            raise Exception("No active subscription found")

        update_data = {
            "cancel_at_period_end": cancel_at_period_end,
            "canceled_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        if not cancel_at_period_end:
            # Cancel immediately
            update_data["status"] = "canceled"
            update_data["period_end"] = datetime.utcnow()

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

        await mongodb.database["subscriptions"].update_one(
            {"_id": subscription["_id"]},
            {"$set": update_data}
        )

        logger.info(f"Subscription canceled for user {user_id} (at_period_end={cancel_at_period_end})")

        return {
            "success": True,
            "message": "Subscription canceled" if not cancel_at_period_end else "Subscription will be canceled at period end",
            "cancel_at_period_end": cancel_at_period_end,
            "period_end": subscription["period_end"]
        }

    async def handle_webhook(
        self,
        event: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        source_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle Razorpay webhook events with full processing and error handling

        Events supported:
        - payment.captured: Payment successful, activate subscription
        - payment.failed: Payment failed, trigger dunning
        - subscription.charged: Auto-renewal successful
        - subscription.cancelled: Subscription canceled via Razorpay
        - subscription.paused: Subscription paused
        - subscription.resumed: Subscription resumed

        Features:
        - Idempotent processing (won't process same event twice)
        - Database logging for audit trail
        - Error handling with retry support
        - Dunning integration for failed payments
        """
        from app.models.mongodb_models import WebhookEvent
        from app.services.dunning_service import dunning_service

        logger.info(f"Processing webhook: {event}")

        # Extract event_id from payload if not provided
        if not event_id:
            event_id = payload.get("event", {}).get("id") or payload.get("id") or f"event_{datetime.utcnow().timestamp()}"

        try:
            # Step 1: Check if event already processed (idempotency)
            existing_event = await mongodb.database["webhook_events"].find_one(
                {"event_id": event_id}
            )

            if existing_event and existing_event["status"] == "processed":
                logger.info(f"Event {event_id} already processed, skipping")
                return {
                    "success": True,
                    "message": "Event already processed",
                    "idempotent": True
                }

            # Step 2: Log webhook event to database
            webhook_event_id = None
            if not existing_event:
                webhook_event = WebhookEvent(
                    event_id=event_id,
                    event_type=event,
                    payload=payload,
                    status="processing",
                    source_ip=source_ip
                )
                result = await mongodb.database["webhook_events"].insert_one(
                    webhook_event.dict(by_alias=True)
                )
                webhook_event_id = result.inserted_id
            else:
                webhook_event_id = existing_event["_id"]
                # Update to processing
                await mongodb.database["webhook_events"].update_one(
                    {"_id": webhook_event_id},
                    {
                        "$set": {
                            "status": "processing",
                            "processing_attempts": existing_event.get("processing_attempts", 0) + 1,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

            # Step 3: Process event based on type
            result = await self._process_webhook_event(event, payload)

            # Step 4: Mark event as processed
            await mongodb.database["webhook_events"].update_one(
                {"_id": webhook_event_id},
                {
                    "$set": {
                        "status": "processed",
                        "processed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            logger.info(f"Webhook {event_id} processed successfully")
            return {
                "success": True,
                "event_id": event_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")

            # Mark event as failed
            if webhook_event_id:
                import traceback
                await mongodb.database["webhook_events"].update_one(
                    {"_id": webhook_event_id},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": str(e),
                            "error_stack": traceback.format_exc(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

            return {
                "success": False,
                "error": str(e),
                "event_id": event_id
            }

    async def _process_webhook_event(self, event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process different webhook event types

        Returns:
            Processing result for each event type
        """
        from app.services.dunning_service import dunning_service

        if event == "payment.captured":
            return await self._handle_payment_captured(payload)

        elif event == "payment.failed":
            return await self._handle_payment_failed(payload)

        elif event == "subscription.charged":
            return await self._handle_subscription_charged(payload)

        elif event == "subscription.cancelled":
            return await self._handle_subscription_cancelled(payload)

        elif event == "subscription.paused":
            return await self._handle_subscription_paused(payload)

        elif event == "subscription.resumed":
            return await self._handle_subscription_resumed(payload)

        else:
            logger.warning(f"Unhandled webhook event type: {event}")
            return {"message": f"Event type '{event}' not handled"}

    async def _handle_payment_captured(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful payment
        This might be auto-renewal or retry after dunning
        """
        payment_entity = payload.get("payment", {}).get("entity", {})
        payment_id = payment_entity.get("id")
        order_id = payment_entity.get("order_id")
        amount = payment_entity.get("amount", 0) / 100  # Convert paise to rupees

        logger.info(f"Payment captured: {payment_id}, Amount: ₹{amount}")

        # Find associated subscription by order_id or payment_id
        # This could be from initial payment or dunning retry
        payment_record = await mongodb.database["payments"].find_one(
            {"razorpay_payment_id": payment_id}
        )

        if payment_record:
            subscription_id = payment_record.get("subscription_id")

            if subscription_id:
                # Check if this was a dunning retry that succeeded
                dunning_attempt = await mongodb.database["dunning_attempts"].find_one({
                    "subscription_id": subscription_id,
                    "status": {"$in": ["pending", "attempted"]}
                })

                if dunning_attempt:
                    # Dunning recovery successful!
                    await dunning_service.mark_retry_success(subscription_id, payment_id)
                    logger.info(f"Dunning recovery successful for subscription {subscription_id}")

                # Update subscription status to active if it was past_due
                await mongodb.database["subscriptions"].update_one(
                    {"_id": subscription_id},
                    {"$set": {"status": "active", "last_payment_at": datetime.utcnow()}}
                )

        return {
            "message": "Payment captured successfully",
            "payment_id": payment_id,
            "amount": amount
        }

    async def _handle_payment_failed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle failed payment
        Trigger dunning process for recovery
        """
        from app.services.dunning_service import dunning_service

        payment_entity = payload.get("payment", {}).get("entity", {})
        payment_id = payment_entity.get("id")
        error_code = payment_entity.get("error_code")
        error_description = payment_entity.get("error_description")

        logger.warning(f"Payment failed: {payment_id}, Error: {error_code} - {error_description}")

        # Find subscription associated with this payment
        # Look in order notes or payment metadata
        order_id = payment_entity.get("order_id")

        # Try to find subscription from order
        payment_record = await mongodb.database["payments"].find_one(
            {"razorpay_order_id": order_id}
        )

        if payment_record:
            subscription_id = payment_record.get("subscription_id")
            user_id = payment_record.get("user_id")

            if subscription_id and user_id:
                # Initiate dunning process
                dunning_result = await dunning_service.handle_failed_payment(
                    subscription_id=subscription_id,
                    user_id=user_id,
                    payment_id=payment_id,
                    error_message=f"{error_code}: {error_description}"
                )

                return {
                    "message": "Payment failed, dunning initiated",
                    "payment_id": payment_id,
                    "error": error_description,
                    "dunning": dunning_result
                }

        return {
            "message": "Payment failed, no subscription found",
            "payment_id": payment_id,
            "error": error_description
        }

    async def _handle_subscription_charged(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful auto-renewal
        Extend subscription period
        """
        subscription_entity = payload.get("subscription", {}).get("entity", {})
        razorpay_subscription_id = subscription_entity.get("id")
        amount = subscription_entity.get("charge_at", 0) / 100

        logger.info(f"Subscription charged: {razorpay_subscription_id}, Amount: ₹{amount}")

        # Find subscription in our database
        subscription = await mongodb.database["subscriptions"].find_one(
            {"razorpay_subscription_id": razorpay_subscription_id}
        )

        if subscription:
            # Extend subscription period by 30 days
            new_period_end = subscription["period_end"] + timedelta(days=30)

            await mongodb.database["subscriptions"].update_one(
                {"_id": subscription["_id"]},
                {
                    "$set": {
                        "period_end": new_period_end,
                        "next_billing_date": new_period_end,
                        "last_payment_at": datetime.utcnow(),
                        "status": "active",
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            logger.info(f"Subscription {subscription['_id']} renewed until {new_period_end}")

            return {
                "message": "Subscription auto-renewed",
                "subscription_id": str(subscription["_id"]),
                "new_period_end": new_period_end
            }

        return {"message": "Subscription not found in database"}

    async def _handle_subscription_cancelled(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subscription cancellation from Razorpay dashboard
        """
        subscription_entity = payload.get("subscription", {}).get("entity", {})
        razorpay_subscription_id = subscription_entity.get("id")

        logger.info(f"Subscription cancelled: {razorpay_subscription_id}")

        subscription = await mongodb.database["subscriptions"].find_one(
            {"razorpay_subscription_id": razorpay_subscription_id}
        )

        if subscription:
            # Mark as canceled
            await mongodb.database["subscriptions"].update_one(
                {"_id": subscription["_id"]},
                {
                    "$set": {
                        "status": "canceled",
                        "canceled_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Downgrade user to free
            await mongodb.database["users"].update_one(
                {"_id": subscription["user_id"]},
                {"$set": {"current_plan": "free"}}
            )

            return {
                "message": "Subscription canceled",
                "subscription_id": str(subscription["_id"])
            }

        return {"message": "Subscription not found"}

    async def _handle_subscription_paused(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription pause"""
        subscription_entity = payload.get("subscription", {}).get("entity", {})
        razorpay_subscription_id = subscription_entity.get("id")

        logger.info(f"Subscription paused: {razorpay_subscription_id}")

        subscription = await mongodb.database["subscriptions"].find_one(
            {"razorpay_subscription_id": razorpay_subscription_id}
        )

        if subscription:
            await mongodb.database["subscriptions"].update_one(
                {"_id": subscription["_id"]},
                {"$set": {"status": "paused", "updated_at": datetime.utcnow()}}
            )

        return {"message": "Subscription paused"}

    async def _handle_subscription_resumed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription resume"""
        subscription_entity = payload.get("subscription", {}).get("entity", {})
        razorpay_subscription_id = subscription_entity.get("id")

        logger.info(f"Subscription resumed: {razorpay_subscription_id}")

        subscription = await mongodb.database["subscriptions"].find_one(
            {"razorpay_subscription_id": razorpay_subscription_id}
        )

        if subscription:
            await mongodb.database["subscriptions"].update_one(
                {"_id": subscription["_id"]},
                {"$set": {"status": "active", "updated_at": datetime.utcnow()}}
            )

        return {"message": "Subscription resumed"}


# Global payment service instance
payment_service = PaymentService()

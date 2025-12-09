"""
Add-on Management Service
Handles add-on catalog, purchases, limit calculations, and lifecycle
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from bson import ObjectId
from app.mongodb import mongodb
from app.models.mongodb_models import Addon, UserAddon
import logging

logger = logging.getLogger(__name__)


class AddonService:
    """Manage subscription add-ons"""

    async def get_all_addons(
        self,
        user_plan: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all available add-ons, optionally filtered

        Args:
            user_plan: Filter add-ons compatible with this plan
            category: Filter by category (storage, api_hits, training, support)

        Returns:
            List of add-on products sorted by display_order
        """
        query = {"is_active": True}

        # Filter by plan compatibility
        if user_plan:
            query["$or"] = [
                {"compatible_plans": []},  # Empty list means available for all plans
                {"compatible_plans": user_plan}
            ]

        # Filter by category
        if category:
            query["category"] = category

        addons = await mongodb.database["addons"].find(query).sort("display_order", 1).to_list(None)
        return addons

    async def get_addon_by_slug(self, addon_slug: str) -> Optional[Dict[str, Any]]:
        """Get add-on product by slug"""
        return await mongodb.database["addons"].find_one({"addon_slug": addon_slug})

    async def get_addon_by_id(self, addon_id: ObjectId) -> Optional[Dict[str, Any]]:
        """Get add-on product by ID"""
        return await mongodb.database["addons"].find_one({"_id": addon_id})

    async def get_user_addons(
        self,
        user_id: ObjectId,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """
        Get user's add-ons with enriched details

        Args:
            user_id: User ID
            status: Filter by status (active, canceled, expired)

        Returns:
            List of user's add-ons with product details
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
                    "addon_slug": addon_product["addon_slug"],
                    "quota_type": addon_product["quota_type"],
                    "quota_amount": addon_product["quota_amount"],
                    "total_quota": addon_product["quota_amount"] * ua.get("quantity", 1)
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
            Dict with base_limits, addon_contributions, total_limits, and active add-ons
        """
        from app.services.subscription_service import subscription_service

        # Get base plan limits
        subscription = await subscription_service.get_user_subscription(user_id)
        base_limits = subscription["limits"]

        # Get all active add-ons
        active_addons = await self.get_user_addons(user_id, status="active")

        # Initialize addon contributions
        addon_contributions = {
            "api_hits_per_month": 0,
            "model_generation_per_day": 0,
            "dataset_size_mb": 0,
            "azure_storage_gb": 0,
            "training_time_minutes_per_model": 0,
            "concurrent_trainings": 0
        }

        total_addon_cost = 0.0

        # Calculate contributions from each add-on
        for ua in active_addons:
            quantity = ua.get("quantity", 1)
            quota_type = ua.get("quota_type")
            quota_amount = ua.get("quota_amount", 0)

            if quota_type in addon_contributions:
                addon_contributions[quota_type] += quota_amount * quantity

            total_addon_cost += ua.get("amount_paid", 0)

        # Calculate total limits (base + add-ons)
        total_limits = {}
        for key in base_limits:
            base_value = base_limits[key]
            addon_value = addon_contributions.get(key, 0)
            total_limits[key] = base_value + addon_value

        return {
            "user_id": str(user_id),
            "plan": subscription["plan"],
            "base_limits": base_limits,
            "addon_contributions": addon_contributions,
            "total_limits": total_limits,
            "active_addons": active_addons,
            "addon_count": len(active_addons),
            "total_addon_cost": total_addon_cost
        }

    async def can_purchase_addon(
        self,
        user_id: ObjectId,
        addon_slug: str,
        quantity: int = 1
    ) -> tuple[bool, str]:
        """
        Check if user can purchase this add-on

        Args:
            user_id: User ID
            addon_slug: Add-on slug
            quantity: Quantity to purchase

        Returns:
            (can_purchase, reason_if_not)
        """
        # Validate quantity
        if quantity < 1:
            return False, "Quantity must be at least 1"

        # Get addon product
        addon_product = await self.get_addon_by_slug(addon_slug)
        if not addon_product:
            return False, "Add-on not found"

        if not addon_product["is_active"]:
            return False, "This add-on is currently unavailable"

        # Check user's plan eligibility
        from app.services.subscription_service import subscription_service
        subscription = await subscription_service.get_user_subscription(user_id)
        user_plan = subscription["plan"]

        compatible_plans = addon_product.get("compatible_plans", [])

        # Empty list means compatible with all plans
        if compatible_plans and user_plan not in compatible_plans:
            return False, f"This add-on is not available for the {user_plan} plan"

        # Check current quantity
        existing_addons = await mongodb.database["user_addons"].find({
            "user_id": user_id,
            "addon_id": addon_product["_id"],
            "status": "active"
        }).to_list(None)

        current_quantity = sum(ua.get("quantity", 1) for ua in existing_addons)

        # Check max quantity
        max_quantity = addon_product.get("max_quantity", 10)
        if current_quantity + quantity > max_quantity:
            available = max_quantity - current_quantity
            if available <= 0:
                return False, f"You've reached the maximum quantity ({max_quantity}) for this add-on"
            return False, f"You can only purchase {available} more of this add-on (max: {max_quantity})"

        return True, ""

    async def activate_addon(
        self,
        user_id: ObjectId,
        addon_slug: str,
        quantity: int,
        razorpay_payment_id: str,
        razorpay_order_id: str,
        amount_paid: float
    ) -> Dict[str, Any]:
        """
        Activate an add-on subscription for a user

        Args:
            user_id: User ID
            addon_slug: Add-on slug
            quantity: Quantity purchased
            razorpay_payment_id: Payment ID
            razorpay_order_id: Order ID
            amount_paid: Amount paid

        Returns:
            Activation result with user_addon_id
        """
        # Get add-on product
        addon_product = await self.get_addon_by_slug(addon_slug)
        if not addon_product:
            raise Exception(f"Add-on '{addon_slug}' not found")

        # Get user's subscription
        from app.services.subscription_service import subscription_service
        subscription = await subscription_service.get_user_subscription(user_id)
        subscription_id = subscription.get("_id")

        # Calculate period (30 days from now)
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)

        # Create user addon record
        user_addon = UserAddon(
            user_id=user_id,
            subscription_id=subscription_id,
            addon_id=addon_product["_id"],
            quantity=quantity,
            amount_paid=amount_paid,
            currency=addon_product["currency"],
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            status="active",
            period_start=period_start,
            period_end=period_end,
            auto_renew=True
        )

        result = await mongodb.database["user_addons"].insert_one(
            user_addon.dict(by_alias=True)
        )
        user_addon_id = result.inserted_id

        logger.info(f"Activated add-on {addon_slug} for user {user_id} (quantity: {quantity})")

        return {
            "success": True,
            "user_addon_id": str(user_addon_id),
            "addon_slug": addon_slug,
            "quantity": quantity,
            "period_start": period_start,
            "period_end": period_end,
            "message": f"Add-on '{addon_product['name']}' activated successfully"
        }

    async def cancel_addon(
        self,
        user_id: ObjectId,
        user_addon_id: str,
        immediate: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a user's add-on subscription

        Args:
            user_id: User ID
            user_addon_id: UserAddon ID to cancel
            immediate: True = cancel now, False = cancel at period end

        Returns:
            Cancellation result
        """
        # Validate user_addon_id
        if not ObjectId.is_valid(user_addon_id):
            raise Exception("Invalid add-on ID")

        user_addon_oid = ObjectId(user_addon_id)

        # Get user addon
        user_addon = await mongodb.database["user_addons"].find_one({
            "_id": user_addon_oid,
            "user_id": user_id,
            "status": "active"
        })

        if not user_addon:
            raise Exception("Active add-on not found")

        if immediate:
            # Cancel immediately
            await mongodb.database["user_addons"].update_one(
                {"_id": user_addon_oid},
                {
                    "$set": {
                        "status": "canceled",
                        "auto_renew": False,
                        "canceled_at": datetime.utcnow(),
                        "period_end": datetime.utcnow(),  # End now
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            message = "Add-on canceled immediately"
        else:
            # Cancel at period end
            await mongodb.database["user_addons"].update_one(
                {"_id": user_addon_oid},
                {
                    "$set": {
                        "auto_renew": False,
                        "canceled_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            message = f"Add-on will be canceled on {user_addon['period_end'].strftime('%Y-%m-%d')}"

        logger.info(f"User {user_id} canceled add-on {user_addon_id} (immediate: {immediate})")

        return {
            "success": True,
            "user_addon_id": user_addon_id,
            "immediate": immediate,
            "period_end": user_addon["period_end"],
            "message": message
        }

    async def check_and_expire_addons(self) -> Dict[str, Any]:
        """
        Check for expired add-ons and update their status
        Should be called by a cron job

        Returns:
            Statistics about expired add-ons
        """
        now = datetime.utcnow()

        # Find add-ons that have expired
        expired_addons = await mongodb.database["user_addons"].find({
            "status": "active",
            "period_end": {"$lte": now},
            "auto_renew": False  # Don't expire if auto-renewing
        }).to_list(None)

        expired_count = 0

        for addon in expired_addons:
            await mongodb.database["user_addons"].update_one(
                {"_id": addon["_id"]},
                {
                    "$set": {
                        "status": "expired",
                        "updated_at": now
                    }
                }
            )
            expired_count += 1

        logger.info(f"Expired {expired_count} add-ons")

        return {
            "expired_count": expired_count,
            "processed_at": now
        }


# Global add-on service instance
addon_service = AddonService()

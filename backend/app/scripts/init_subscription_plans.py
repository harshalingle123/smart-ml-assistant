"""
Initialize Subscription Plans in MongoDB
Run this script once to populate the plans collection
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


async def init_plans():
    """Initialize subscription plans in database"""

    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client.get_database()

    # Define subscription plans
    plans = [
        {
            "plan": "free",
            "name": "Free Plan",
            "description": "Get started with basic AutoML features",
            "price_monthly": 0.0,
            "currency": "INR",
            "api_hits_per_month": 500,
            "model_generation_per_day": 3,
            "dataset_size_mb": 50,
            "azure_storage_gb": 0.1,  # 100 MB
            "training_time_minutes_per_model": 5,
            "concurrent_trainings": 1,
            "features": [
                "Basic AutoML training",
                "Up to 3 models/day",
                "500 API calls/month",
                "50 MB dataset limit",
                "Community support"
            ],
            "priority_support": False,
            "razorpay_plan_id": None,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "plan": "pro",
            "name": "Pro Plan",
            "description": "Perfect for individual developers and small teams",
            "price_monthly": 99.0,
            "currency": "INR",
            "api_hits_per_month": 5000,
            "model_generation_per_day": 25,
            "dataset_size_mb": 500,
            "azure_storage_gb": 5,
            "training_time_minutes_per_model": 30,
            "concurrent_trainings": 3,
            "features": [
                "Advanced AutoML training",
                "Up to 25 models/day",
                "5,000 API calls/month",
                "500 MB dataset limit",
                "5 GB cloud storage",
                "Priority email support",
                "Advanced model metrics",
                "Custom hyperparameters"
            ],
            "priority_support": True,
            "razorpay_plan_id": None,  # Set this after creating plan in Razorpay
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "plan": "advanced",
            "name": "Advanced Plan",
            "description": "For production workloads and enterprise teams",
            "price_monthly": 299.0,
            "currency": "INR",
            "api_hits_per_month": 50000,
            "model_generation_per_day": 100,
            "dataset_size_mb": 2000,
            "azure_storage_gb": 20,
            "training_time_minutes_per_model": 120,
            "concurrent_trainings": 10,
            "features": [
                "Enterprise AutoML training",
                "Up to 100 models/day",
                "50,000 API calls/month",
                "2 GB dataset limit",
                "20 GB cloud storage",
                "24/7 priority support",
                "Advanced analytics",
                "Custom training pipelines",
                "Dedicated compute resources",
                "SLA guarantee"
            ],
            "priority_support": True,
            "razorpay_plan_id": None,  # Set this after creating plan in Razorpay
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    # Insert or update plans
    for plan in plans:
        existing = await db.plans.find_one({"plan": plan["plan"]})

        if existing:
            # Update existing plan (keep razorpay_plan_id if it exists)
            if existing.get("razorpay_plan_id"):
                plan["razorpay_plan_id"] = existing["razorpay_plan_id"]

            await db.plans.update_one(
                {"plan": plan["plan"]},
                {"$set": plan}
            )
            print(f"✓ Updated {plan['name']}")
        else:
            await db.plans.insert_one(plan)
            print(f"✓ Created {plan['name']}")

    print("\n✅ Subscription plans initialized successfully!")

    # Create indexes for all collections
    print("\n🔧 Creating database indexes...")

    # Plans
    await db.plans.create_index("plan", unique=True)
    print("  ✓ plans.plan (unique)")

    # Subscriptions
    await db.subscriptions.create_index("user_id")
    await db.subscriptions.create_index([("user_id", 1), ("status", 1)])
    await db.subscriptions.create_index("razorpay_subscription_id")
    print("  ✓ subscriptions indexes")

    # Usage Records
    await db.usage_records.create_index("user_id", unique=True)
    await db.usage_records.create_index("subscription_id")
    print("  ✓ usage_records indexes")

    # Payments
    await db.payments.create_index("user_id")
    await db.payments.create_index("razorpay_payment_id")
    await db.payments.create_index("razorpay_order_id")
    await db.payments.create_index("subscription_id")
    print("  ✓ payments indexes")

    # Webhook Events (NEW - Week 3)
    await db.webhook_events.create_index("event_id", unique=True)  # For idempotency
    await db.webhook_events.create_index("event_type")
    await db.webhook_events.create_index("status")
    await db.webhook_events.create_index([("status", 1), ("created_at", -1)])
    await db.webhook_events.create_index("created_at", expireAfterSeconds=7776000)  # Auto-delete after 90 days
    print("  ✓ webhook_events indexes (with TTL)")

    # Dunning Attempts (NEW - Week 3)
    await db.dunning_attempts.create_index("subscription_id")
    await db.dunning_attempts.create_index("user_id")
    await db.dunning_attempts.create_index([("subscription_id", 1), ("status", 1)])
    await db.dunning_attempts.create_index([("status", 1), ("scheduled_at", 1)])  # For cron job
    await db.dunning_attempts.create_index("created_at", expireAfterSeconds=15552000)  # Auto-delete after 180 days
    print("  ✓ dunning_attempts indexes (with TTL)")

    print("\n✅ All database indexes created successfully!")
    print("\n📝 Note: Webhook events auto-delete after 90 days")
    print("📝 Note: Dunning attempts auto-delete after 180 days")

    client.close()


if __name__ == "__main__":
    print("🚀 Initializing subscription plans...\n")
    asyncio.run(init_plans())

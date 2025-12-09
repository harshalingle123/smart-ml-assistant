"""
Simple script to initialize subscription plans (Windows-friendly)
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings


async def init_plans():
    """Initialize subscription plans in database"""
    print("Connecting to MongoDB...")
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
            "azure_storage_gb": 0.1,
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
            "razorpay_plan_id": None,
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
            "razorpay_plan_id": None,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    # Insert or update plans
    created = 0
    updated = 0

    for plan in plans:
        existing = await db.plans.find_one({"plan": plan["plan"]})

        if existing:
            if existing.get("razorpay_plan_id"):
                plan["razorpay_plan_id"] = existing["razorpay_plan_id"]

            await db.plans.update_one(
                {"plan": plan["plan"]},
                {"$set": plan}
            )
            print(f"Updated: {plan['name']}")
            updated += 1
        else:
            await db.plans.insert_one(plan)
            print(f"Created: {plan['name']}")
            created += 1

    print(f"\nSummary:")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    print(f"  Total: {len(plans)}")

    # Create indexes
    print("\nCreating indexes...")
    await db.plans.create_index("plan", unique=True)
    await db.subscriptions.create_index("user_id")
    await db.subscriptions.create_index([("user_id", 1), ("status", 1)])
    await db.usage_records.create_index("user_id", unique=True)
    await db.payments.create_index("user_id")
    print("  Done!")

    print("\nSubscription plans initialized successfully!")
    client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Smart ML Assistant - Subscription Plans Initialization")
    print("=" * 60)
    print()
    asyncio.run(init_plans())

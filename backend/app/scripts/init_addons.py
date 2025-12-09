"""
Initialize Add-on Products in MongoDB
Run this script once to populate the addons collection
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


async def init_addons():
    """Initialize add-on products in database"""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client.get_database()

    addons = [
        # Storage Add-ons
        {
            "addon_slug": "extra_storage_5gb",
            "name": "Extra Storage (+5 GB)",
            "description": "Add 5 GB of Azure Blob Storage to your plan. Perfect for storing more datasets and trained models.",
            "category": "storage",
            "price_monthly": 99.0,
            "price_annual": None,
            "currency": "INR",
            "quota_type": "azure_storage_gb",
            "quota_amount": 5.0,
            "compatible_plans": ["free", "pro"],  # Not for Advanced (already has 20GB)
            "max_quantity": 10,
            "is_active": True,
            "icon": "hard-drive",
            "badge_text": None,
            "display_order": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_slug": "extra_storage_10gb",
            "name": "Extra Storage (+10 GB)",
            "description": "Add 10 GB of Azure Blob Storage. Great value for data-intensive projects.",
            "category": "storage",
            "price_monthly": 179.0,
            "price_annual": None,
            "currency": "INR",
            "quota_type": "azure_storage_gb",
            "quota_amount": 10.0,
            "compatible_plans": ["free", "pro"],
            "max_quantity": 10,
            "is_active": True,
            "icon": "hard-drive",
            "badge_text": "POPULAR",
            "display_order": 2,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_slug": "extra_storage_50gb",
            "name": "Extra Storage (+50 GB)",
            "description": "Massive storage boost. Add 50 GB for enterprise-scale data processing.",
            "category": "storage",
            "price_monthly": 799.0,
            "price_annual": None,
            "currency": "INR",
            "quota_type": "azure_storage_gb",
            "quota_amount": 50.0,
            "compatible_plans": [],  # Available for all plans
            "max_quantity": 5,
            "is_active": True,
            "icon": "hard-drive",
            "badge_text": "BEST VALUE",
            "display_order": 3,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },

        # API Boost Add-ons
        {
            "addon_slug": "api_boost_5000",
            "name": "API Boost (+5,000 calls)",
            "description": "Add 5,000 API calls per month. Great for moderate usage spikes.",
            "category": "api_hits",
            "price_monthly": 149.0,
            "price_annual": None,
            "currency": "INR",
            "quota_type": "api_hits_per_month",
            "quota_amount": 5000.0,
            "compatible_plans": ["free", "pro"],
            "max_quantity": 10,
            "is_active": True,
            "icon": "zap",
            "badge_text": None,
            "display_order": 4,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_slug": "api_boost_10000",
            "name": "API Boost (+10,000 calls)",
            "description": "Add 10,000 API calls per month. Best value for high-volume applications.",
            "category": "api_hits",
            "price_monthly": 279.0,
            "price_annual": None,
            "currency": "INR",
            "quota_type": "api_hits_per_month",
            "quota_amount": 10000.0,
            "compatible_plans": ["free", "pro"],
            "max_quantity": 10,
            "is_active": True,
            "icon": "zap",
            "badge_text": "BEST VALUE",
            "display_order": 5,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_slug": "api_boost_50000",
            "name": "API Boost (+50,000 calls)",
            "description": "Massive API boost. Add 50,000 calls per month for production workloads.",
            "category": "api_hits",
            "price_monthly": 1299.0,
            "price_annual": None,
            "currency": "INR",
            "quota_type": "api_hits_per_month",
            "quota_amount": 50000.0,
            "compatible_plans": [],  # All plans
            "max_quantity": 5,
            "is_active": True,
            "icon": "zap",
            "badge_text": "ENTERPRISE",
            "display_order": 6,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },

        # Model Training Add-ons
        {
            "addon_slug": "model_boost_10",
            "name": "Model Boost (+10 models/day)",
            "description": "Train 10 additional models per day. Perfect for rapid experimentation.",
            "category": "training",
            "price_monthly": 199.0,
            "price_annual": None,
            "currency": "INR",
            "quota_type": "model_generation_per_day",
            "quota_amount": 10.0,
            "compatible_plans": ["free", "pro"],
            "max_quantity": 5,
            "is_active": True,
            "icon": "activity",
            "badge_text": None,
            "display_order": 7,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_slug": "model_boost_20",
            "name": "Model Boost (+20 models/day)",
            "description": "Train 20 additional models per day. Great value for intensive ML workflows.",
            "category": "training",
            "price_monthly": 379.0,
            "price_annual": None,
            "currency": "INR",
            "quota_type": "model_generation_per_day",
            "quota_amount": 20.0,
            "compatible_plans": ["free", "pro"],
            "max_quantity": 5,
            "is_active": True,
            "icon": "activity",
            "badge_text": "POPULAR",
            "display_order": 8,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "addon_slug": "model_boost_50",
            "name": "Model Boost (+50 models/day)",
            "description": "Massive model training capacity. Train 50 additional models daily.",
            "category": "training",
            "price_monthly": 899.0,
            "price_annual": None,
            "currency": "INR",
            "quota_type": "model_generation_per_day",
            "quota_amount": 50.0,
            "compatible_plans": [],  # All plans
            "max_quantity": 3,
            "is_active": True,
            "icon": "activity",
            "badge_text": "ENTERPRISE",
            "display_order": 9,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    # Insert or update add-ons
    created_count = 0
    updated_count = 0

    for addon in addons:
        existing = await db.addons.find_one({"addon_slug": addon["addon_slug"]})

        if existing:
            # Update existing
            await db.addons.update_one(
                {"addon_slug": addon["addon_slug"]},
                {"$set": addon}
            )
            print(f"Updated: {addon['name']}")
            updated_count += 1
        else:
            # Insert new
            await db.addons.insert_one(addon)
            print(f"Created: {addon['name']}")
            created_count += 1

    print(f"\nAdd-ons Summary:")
    print(f"  - Created: {created_count}")
    print(f"  - Updated: {updated_count}")
    print(f"  - Total: {len(addons)}")

    # Create indexes
    print("\nCreating indexes...")
    await db.addons.create_index("addon_slug", unique=True)
    await db.addons.create_index([("category", 1), ("is_active", 1)])
    await db.addons.create_index("display_order")
    print("  - addons.addon_slug (unique)")
    print("  - addons.category + is_active")
    print("  - addons.display_order")

    await db.user_addons.create_index("user_id")
    await db.user_addons.create_index([("user_id", 1), ("status", 1)])
    await db.user_addons.create_index("addon_id")
    await db.user_addons.create_index([("status", 1), ("period_end", 1)])
    print("  - user_addons.user_id")
    print("  - user_addons.user_id + status")
    print("  - user_addons.addon_id")
    print("  - user_addons.status + period_end")

    print("\nAdd-on system initialized successfully!")
    print("\nAvailable add-ons by category:")
    print("  Storage: 3 add-ons (5GB, 10GB, 50GB)")
    print("  API Hits: 3 add-ons (5K, 10K, 50K calls)")
    print("  Model Training: 3 add-ons (10, 20, 50 models/day)")

    client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Smart ML Assistant - Add-on Initialization")
    print("=" * 60)
    print()
    asyncio.run(init_addons())

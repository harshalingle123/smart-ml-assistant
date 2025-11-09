import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def verify_mongodb_data():
    """Verify data is stored in MongoDB"""
    print("=" * 70)
    print("Verifying MongoDB Data Storage")
    print("=" * 70)

    try:
        # Create MongoDB client
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client.get_database()

        # Check users collection
        print("\n[Users Collection]")
        users_count = await db["users"].count_documents({})
        print(f"Total users: {users_count}")

        if users_count > 0:
            print("\nRecent users:")
            users = await db["users"].find().sort("_id", -1).limit(3).to_list(length=3)
            for user in users:
                print(f"  - {user['email']} ({user['name']}) - Plan: {user['current_plan']}")

        # Check other collections
        collections = await db.list_collection_names()
        print(f"\n[All Collections]")
        print(f"Available collections: {', '.join(collections) if collections else '(none yet)'}")

        for coll_name in collections:
            if coll_name != "users":
                count = await db[coll_name].count_documents({})
                print(f"  - {coll_name}: {count} documents")

        client.close()

        print("\n" + "=" * 70)
        print("[SUCCESS] MongoDB data verification complete!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n[ERROR] Verification failed: {str(e)}")
        return False


if __name__ == "__main__":
    asyncio.run(verify_mongodb_data())

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import sys


async def test_mongodb_connection():
    """Test MongoDB connection"""
    print("=" * 60)
    print("Testing MongoDB Connection")
    print("=" * 60)
    print(f"\nConnection URI: {settings.MONGO_URI[:30]}...{settings.MONGO_URI[-20:]}")
    print("\nAttempting to connect...\n")

    try:
        # Create MongoDB client
        client = AsyncIOMotorClient(settings.MONGO_URI)

        # Test the connection
        await client.admin.command('ping')

        print("[SUCCESS] Successfully connected to MongoDB!")
        print("\n" + "=" * 60)
        print("Connection Details:")
        print("=" * 60)

        # Get server info
        server_info = await client.server_info()
        print(f"MongoDB Version: {server_info.get('version', 'N/A')}")

        # List databases
        db_list = await client.list_database_names()
        print(f"\nAvailable Databases: {', '.join(db_list)}")

        # Get database stats
        try:
            db = client.get_default_database()
        except:
            db = client.get_database("dualquery")

        if db is not None:
            print(f"\nDefault Database: {db.name}")
            collections = await db.list_collection_names()
            if collections:
                print(f"Collections: {', '.join(collections)}")
            else:
                print("Collections: (empty - no collections yet)")

        print("\n" + "=" * 60)
        print("[PASS] Connection Test PASSED")
        print("=" * 60)

        client.close()
        return True

    except Exception as e:
        print(f"\n[FAIL] Connection Test FAILED")
        print("=" * 60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("=" * 60)
        print("\nTroubleshooting Tips:")
        print("1. Check if your IP is whitelisted in MongoDB Atlas")
        print("2. Verify username and password are correct")
        print("3. Ensure the cluster is running")
        print("4. Check if network access allows your IP")
        print("=" * 60)
        return False


if __name__ == "__main__":
    result = asyncio.run(test_mongodb_connection())
    sys.exit(0 if result else 1)

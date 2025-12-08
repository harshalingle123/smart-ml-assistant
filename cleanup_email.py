"""
Cleanup script to remove user and OTP records for a specific email
Usage: python cleanup_email.py <email>
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.core.config import settings

async def cleanup_email(email: str):
    """Remove all records for a specific email"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    print(f"\n{'='*60}")
    print(f"CLEANUP FOR EMAIL: {email}")
    print(f"{'='*60}\n")

    # Normalize to lowercase
    email_lower = email.lower()

    # Delete from users collection (case-insensitive)
    print("1. Removing from users collection...")
    user_result = await db["users"].delete_many({
        "email": {"$regex": f"^{email}$", "$options": "i"}
    })
    print(f"   ✓ Deleted {user_result.deleted_count} user record(s)\n")

    # Delete from otp_codes collection
    print("2. Removing from otp_codes collection...")
    otp_result = await db["otp_codes"].delete_many({
        "$or": [
            {"email": email},
            {"email": email_lower},
            {"email": {"$regex": f"^{email}$", "$options": "i"}}
        ]
    })
    print(f"   ✓ Deleted {otp_result.deleted_count} OTP record(s)\n")

    # Clean up expired OTPs (bonus cleanup)
    print("3. Cleaning up expired OTPs (all emails)...")
    from datetime import datetime
    expired_result = await db["otp_codes"].delete_many({
        "expires_at": {"$lt": datetime.utcnow()}
    })
    print(f"   ✓ Deleted {expired_result.deleted_count} expired OTP record(s)\n")

    print(f"{'='*60}")
    print("CLEANUP COMPLETE!")
    print(f"{'='*60}\n")

    await client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup_email.py <email>")
        print("\nExample:")
        print("  python cleanup_email.py user@example.com")
        sys.exit(1)

    email = sys.argv[1]

    print("\nWARNING: This will permanently delete all data for this email!")
    confirm = input(f"Are you sure you want to cleanup '{email}'? (yes/no): ")

    if confirm.lower() in ['yes', 'y']:
        asyncio.run(cleanup_email(email))
    else:
        print("\nCleanup cancelled.")

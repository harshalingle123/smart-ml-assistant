"""
Clear rate limits for development/testing
Usage: python clear_rate_limits.py
"""
import asyncio
import sys

# Add backend to path
sys.path.insert(0, 'backend')

from app.middleware.auth_rate_limiter import rate_limiter

async def clear_all_rate_limits():
    """Clear all rate limits"""
    print("\n" + "="*60)
    print("CLEARING ALL RATE LIMITS")
    print("="*60 + "\n")

    # Clear the entire requests dictionary
    if hasattr(rate_limiter, 'requests'):
        rate_limiter.requests.clear()
        print("✓ All rate limits cleared!")
    else:
        print("✗ Rate limiter not initialized")

    print("\n" + "="*60)
    print("Rate limits reset. You can now test authentication.")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(clear_all_rate_limits())

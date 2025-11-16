from fastapi import Request, HTTPException, status
from app.mongodb import mongodb
from app.services.usage_tracker import usage_tracker
from bson import ObjectId
from typing import Optional


async def verify_api_key(authorization: str) -> Optional[dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None

    api_key = authorization.replace("Bearer ", "").strip()

    key_record = await mongodb.database["direct_access_keys"].find_one({
        "api_key": api_key,
        "status": "active"
    })

    return key_record


async def check_rate_limit(api_key_record: dict) -> bool:
    api_key_id = api_key_record["_id"]
    rate_limit = api_key_record.get("rate_limit", 10)

    return await usage_tracker.check_rate_limit(api_key_id, rate_limit)


async def check_usage_limits(api_key_record: dict) -> dict:
    api_key_id = api_key_record["_id"]
    free_tier_limit = api_key_record.get("free_tier_limit", 10000)
    requests_this_month = api_key_record.get("requests_this_month", 0)

    within_limit = await usage_tracker.check_free_tier(
        api_key_id,
        free_tier_limit,
        requests_this_month
    )

    return {
        "within_limit": within_limit,
        "requests_used": requests_this_month,
        "requests_remaining": max(0, free_tier_limit - requests_this_month)
    }


async def enforce_rate_limit(request: Request):
    authorization = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    api_key_record = await verify_api_key(authorization)

    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "Bearer"}
        )

    rate_limit_ok = await check_rate_limit(api_key_record)
    if not rate_limit_ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down your requests."
        )

    usage_limits = await check_usage_limits(api_key_record)
    if not usage_limits["within_limit"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Free tier limit exceeded. Please upgrade your plan."
        )

    request.state.api_key_record = api_key_record
    request.state.usage_info = usage_limits

    return api_key_record

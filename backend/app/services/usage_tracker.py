from datetime import datetime, timedelta
from app.mongodb import mongodb
from app.models.mongodb_models import ModelUsage
from bson import ObjectId
import secrets


class UsageTracker:
    @staticmethod
    async def track_request(
        api_key_id: ObjectId,
        user_id: ObjectId,
        model_id: str,
        latency_ms: int,
        status: str,
        cost: float,
        batch_size: int = 1,
        error_message: str = None
    ) -> str:
        request_id = f"req_{secrets.token_urlsafe(16)}"

        usage_record = ModelUsage(
            api_key_id=api_key_id,
            user_id=user_id,
            model_id=model_id,
            latency_ms=latency_ms,
            status=status,
            cost=cost,
            request_id=request_id,
            batch_size=batch_size,
            error_message=error_message
        )

        await mongodb.database["model_usage"].insert_one(usage_record.dict(by_alias=True))

        await mongodb.database["direct_access_keys"].update_one(
            {"_id": api_key_id},
            {
                "$inc": {"requests_used": batch_size, "requests_this_month": batch_size},
                "$set": {"last_used_at": datetime.utcnow()}
            }
        )

        return request_id

    @staticmethod
    async def check_rate_limit(api_key_id: ObjectId, rate_limit: int) -> bool:
        one_second_ago = datetime.utcnow() - timedelta(seconds=1)

        recent_requests = await mongodb.database["model_usage"].count_documents({
            "api_key_id": api_key_id,
            "timestamp": {"$gte": one_second_ago}
        })

        return recent_requests < rate_limit

    @staticmethod
    async def check_free_tier(api_key_id: ObjectId, free_tier_limit: int, requests_this_month: int) -> bool:
        return requests_this_month < free_tier_limit

    @staticmethod
    async def reset_monthly_usage():
        await mongodb.database["direct_access_keys"].update_many(
            {},
            {
                "$set": {
                    "requests_this_month": 0,
                    "last_reset_at": datetime.utcnow()
                }
            }
        )

    @staticmethod
    async def get_usage_stats(user_id: ObjectId, timeframe: str = "30d") -> dict:
        timeframe_map = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }

        time_delta = timeframe_map.get(timeframe, timedelta(days=30))
        start_time = datetime.utcnow() - time_delta

        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": start_time}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_requests": {"$sum": 1},
                    "successful_requests": {
                        "$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                    },
                    "failed_requests": {
                        "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
                    },
                    "average_latency": {"$avg": "$latency_ms"}
                }
            }
        ]

        result = await mongodb.database["model_usage"].aggregate(pipeline).to_list(1)

        if not result:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_latency_ms": 0.0
            }

        return {
            "total_requests": result[0]["total_requests"],
            "successful_requests": result[0]["successful_requests"],
            "failed_requests": result[0]["failed_requests"],
            "average_latency_ms": round(result[0]["average_latency"], 2)
        }

    @staticmethod
    async def get_usage_by_model(user_id: ObjectId, timeframe: str = "30d") -> dict:
        timeframe_map = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }

        time_delta = timeframe_map.get(timeframe, timedelta(days=30))
        start_time = datetime.utcnow() - time_delta

        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": start_time}
                }
            },
            {
                "$group": {
                    "_id": "$model_id",
                    "requests": {"$sum": 1},
                    "total_cost": {"$sum": "$cost"}
                }
            }
        ]

        results = await mongodb.database["model_usage"].aggregate(pipeline).to_list(None)

        by_model = {}
        for result in results:
            model_id = result["_id"]
            api_key = await mongodb.database["direct_access_keys"].find_one({
                "user_id": user_id,
                "model_id": model_id
            })

            if api_key:
                by_model[model_id] = {
                    "requests": result["requests"],
                    "cost": round(result["total_cost"], 4),
                    "free_tier_used": api_key["requests_this_month"],
                    "free_tier_remaining": max(0, api_key["free_tier_limit"] - api_key["requests_this_month"])
                }

        return by_model

    @staticmethod
    async def get_time_series(user_id: ObjectId, timeframe: str = "30d") -> list:
        timeframe_map = {
            "1h": (timedelta(hours=1), "minute"),
            "24h": (timedelta(hours=24), "hour"),
            "7d": (timedelta(days=7), "day"),
            "30d": (timedelta(days=30), "day")
        }

        time_delta, group_by = timeframe_map.get(timeframe, (timedelta(days=30), "day"))
        start_time = datetime.utcnow() - time_delta

        if group_by == "minute":
            date_format = "%Y-%m-%dT%H:%M:00Z"
        elif group_by == "hour":
            date_format = "%Y-%m-%dT%H:00:00Z"
        else:
            date_format = "%Y-%m-%dT00:00:00Z"

        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": start_time}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": date_format,
                            "date": "$timestamp"
                        }
                    },
                    "requests": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]

        results = await mongodb.database["model_usage"].aggregate(pipeline).to_list(None)

        return [
            {"timestamp": result["_id"], "requests": result["requests"]}
            for result in results
        ]

    @staticmethod
    def calculate_cost(model_id: str, requests: int, free_tier_limit: int) -> float:
        pricing_map = {
            "vader": 0.0001,
            "distilbert": 0.0006,
            "roberta": 0.002,
            "spam-detection": 0.0001,
            "language-id": 0.0001
        }

        price_per_request = pricing_map.get(model_id, 0.0001)

        if requests <= free_tier_limit:
            return 0.0

        paid_requests = requests - free_tier_limit
        return paid_requests * price_per_request


usage_tracker = UsageTracker()

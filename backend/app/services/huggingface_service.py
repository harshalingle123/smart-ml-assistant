from typing import List, Dict, Optional, Any
import httpx
from datetime import datetime, timedelta
from app.mongodb import mongodb
from bson import ObjectId


class HuggingFaceService:
    BASE_URL = "https://huggingface.co/api"
    CACHE_DURATION_HOURS = 24

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_models(
        self,
        query: Optional[str] = None,
        task: Optional[str] = None,
        limit: int = 20,
        sort: str = "downloads",
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        cache_key = f"{query}_{task}_{limit}_{sort}"

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        params = {
            "limit": limit,
            "sort": sort,
            "direction": -1
        }

        if query:
            params["search"] = query

        if task:
            params["filter"] = task

        try:
            response = await self.client.get(f"{self.BASE_URL}/models", params=params)
            response.raise_for_status()
            models = response.json()

            processed_models = [self._process_model(model) for model in models]

            await self._save_to_cache(cache_key, processed_models)

            return processed_models

        except httpx.HTTPError as e:
            raise Exception(f"HuggingFace API error: {str(e)}")

    async def get_model_details(self, model_id: str) -> Dict[str, Any]:
        cache_key = f"model_{model_id}"

        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            response = await self.client.get(f"{self.BASE_URL}/models/{model_id}")
            response.raise_for_status()
            model_data = response.json()

            processed = self._process_model_details(model_data)

            await self._save_to_cache(cache_key, processed)

            return processed

        except httpx.HTTPError as e:
            raise Exception(f"HuggingFace API error: {str(e)}")

    async def compare_models(self, model_ids: List[str]) -> List[Dict[str, Any]]:
        models = []
        for model_id in model_ids:
            try:
                model = await self.get_model_details(model_id)
                models.append(model)
            except Exception:
                continue

        return models

    def _process_model(self, model: Dict) -> Dict[str, Any]:
        return {
            "model_id": model.get("id", ""),
            "name": model.get("id", "").split("/")[-1] if "/" in model.get("id", "") else model.get("id", ""),
            "author": model.get("author", ""),
            "downloads": model.get("downloads", 0),
            "likes": model.get("likes", 0),
            "tags": model.get("tags", []),
            "pipeline_tag": model.get("pipeline_tag", ""),
            "library_name": model.get("library_name", ""),
            "created_at": model.get("createdAt", ""),
            "last_modified": model.get("lastModified", "")
        }

    def _process_model_details(self, model: Dict) -> Dict[str, Any]:
        config = model.get("config", {})
        card_data = model.get("cardData", {})

        return {
            "model_id": model.get("id", ""),
            "name": model.get("id", "").split("/")[-1] if "/" in model.get("id", "") else model.get("id", ""),
            "author": model.get("author", ""),
            "downloads": model.get("downloads", 0),
            "likes": model.get("likes", 0),
            "tags": model.get("tags", []),
            "pipeline_tag": model.get("pipeline_tag", ""),
            "library_name": model.get("library_name", ""),
            "languages": card_data.get("language", []) if isinstance(card_data.get("language"), list) else [card_data.get("language")] if card_data.get("language") else [],
            "datasets": card_data.get("datasets", []),
            "metrics": card_data.get("metrics", []),
            "model_type": config.get("model_type", ""),
            "parameters": self._estimate_parameters(model),
            "created_at": model.get("createdAt", ""),
            "last_modified": model.get("lastModified", ""),
            "description": model.get("description", "")
        }

    def _estimate_parameters(self, model: Dict) -> str:
        tags = model.get("tags", [])
        for tag in tags:
            if "billion" in tag.lower() or "million" in tag.lower():
                return tag

        model_id = model.get("id", "").lower()
        if "base" in model_id:
            return "~110M parameters"
        elif "large" in model_id:
            return "~340M parameters"
        elif "small" in model_id:
            return "~60M parameters"
        else:
            return "Unknown"

    async def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        try:
            cached = await mongodb.database["huggingface_cache"].find_one({
                "cache_key": cache_key,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            if cached:
                return cached.get("data")
        except Exception:
            pass
        return None

    async def _save_to_cache(self, cache_key: str, data: Any):
        try:
            await mongodb.database["huggingface_cache"].update_one(
                {"cache_key": cache_key},
                {
                    "$set": {
                        "cache_key": cache_key,
                        "data": data,
                        "expires_at": datetime.utcnow() + timedelta(hours=self.CACHE_DURATION_HOURS),
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception:
            pass

    async def close(self):
        await self.client.aclose()


huggingface_service = HuggingFaceService()

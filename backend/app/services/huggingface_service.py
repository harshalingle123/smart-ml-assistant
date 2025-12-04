from typing import List, Dict, Optional, Any
import httpx
from datetime import datetime, timedelta
from app.mongodb import mongodb
from bson import ObjectId
import os
from pathlib import Path
from app.core.config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

class HuggingFaceService:
    BASE_URL = "https://huggingface.co/api"
    CACHE_DURATION_HOURS = 24

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.hf_token = settings.HF_TOKEN
        self.is_configured = bool(self.hf_token)

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
            logger.error(f"HuggingFace API error: {str(e)}")
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
            logger.error(f"HuggingFace API error: {str(e)}")
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

    async def search_datasets(
        self,
        query: Optional[str] = None,
        limit: int = 15,
        sort: str = "downloads",
        direction: int = -1,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for datasets on HuggingFace using the HfApi.
        Uses asyncio.to_thread to prevent blocking the event loop.
        """
        cache_key = f"datasets_{query}_{limit}_{sort}_{direction}"

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        try:
            # Run blocking search in thread
            processed_datasets = await asyncio.to_thread(
                self._search_datasets_sync, query, limit, sort, direction
            )

            logger.info(f"✓ Found {len(processed_datasets)} from Hugging Face.")

            # Cache results
            await self._save_to_cache(cache_key, processed_datasets)

            return processed_datasets

        except Exception as e:
            logger.error(f"✗ HF Search Failed: {e}")
            return []

    def _search_datasets_sync(
        self,
        query: Optional[str],
        limit: int,
        sort: str,
        direction: int
    ) -> List[Dict[str, Any]]:
        """Synchronous helper for dataset search."""
        from huggingface_hub import HfApi

        hf_api = HfApi(token=self.hf_token) if self.hf_token else HfApi()

        hf_datasets = hf_api.list_datasets(
            search=query,
            limit=limit,
            sort=sort,
            direction=direction
        )

        processed_datasets = []
        for d in hf_datasets:
            # Try to get dataset size from multiple sources
            dataset_size = 0
            size_str = "Unknown"
            try:
                # Try card_data first
                card_data = getattr(d, 'card_data', None)
                if card_data:
                    # Extract size from card_data if available
                    dataset_info = getattr(card_data, 'dataset_info', None) or {}
                    if isinstance(dataset_info, dict):
                        size_str = dataset_info.get('dataset_size', 'Unknown')
                        # Try to parse size string like "100MB", "1.5GB"
                        if isinstance(size_str, str) and size_str != 'Unknown':
                            size_lower = size_str.lower()
                            if 'gb' in size_lower:
                                dataset_size = int(float(size_lower.replace('gb', '').strip()) * 1024 * 1024 * 1024)
                            elif 'mb' in size_lower:
                                dataset_size = int(float(size_lower.replace('mb', '').strip()) * 1024 * 1024)
                            elif 'kb' in size_lower:
                                dataset_size = int(float(size_lower.replace('kb', '').strip()) * 1024)

                # Try direct size attribute if card_data didn't work
                if dataset_size == 0 and hasattr(d, 'size_bytes') and d.size_bytes:
                    dataset_size = d.size_bytes
                    # Convert bytes to human-readable format
                    if dataset_size >= 1024 * 1024 * 1024:
                        size_str = f"{dataset_size / (1024 * 1024 * 1024):.2f}GB"
                    elif dataset_size >= 1024 * 1024:
                        size_str = f"{dataset_size / (1024 * 1024):.2f}MB"
                    elif dataset_size >= 1024:
                        size_str = f"{dataset_size / 1024:.2f}KB"
                    else:
                        size_str = f"{dataset_size}B"
            except Exception as e:
                logger.warning(f"Error extracting size for {d.id}: {e}")
                pass  # Keep default values if parsing fails

            processed_datasets.append({
                "id": d.id,
                "title": d.id.split('/')[-1],
                "description": getattr(d, 'description', '') or d.id,
                "source": "HuggingFace",
                "url": f"https://huggingface.co/datasets/{d.id}",
                "downloads": getattr(d, 'downloads', 0),
                "name": d.id.split('/')[-1],
                "likes": getattr(d, 'likes', 0),
                "tags": getattr(d, 'tags', []),
                "size": dataset_size,  # Add size information
                "size_str": size_str,  # Human-readable size
            })
        return processed_datasets

    async def download_dataset(
        self,
        dataset_id: str,
        download_path: str = "./data/huggingface"
    ) -> Dict[str, str]:
        """
        Download a dataset from HuggingFace.
        Uses asyncio.to_thread to prevent blocking.
        """
        try:
            return await asyncio.to_thread(
                self._download_dataset_sync, dataset_id, download_path
            )
        except Exception as e:
            logger.error(f"Error downloading HuggingFace dataset: {str(e)}")
            raise Exception(f"Error downloading HuggingFace dataset: {str(e)}")

    def _download_dataset_sync(self, dataset_id: str, download_path: str) -> Dict[str, str]:
        """Synchronous helper for dataset download."""
        from huggingface_hub import snapshot_download

        # Create download directory
        dataset_folder = os.path.join(download_path, dataset_id.replace('/', '_'))
        Path(dataset_folder).mkdir(parents=True, exist_ok=True)

        # Download dataset using snapshot_download
        snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            local_dir=dataset_folder,
            token=self.hf_token
        )

        return {
            'status': 'success',
            'dataset_id': dataset_id,
            'download_path': dataset_folder,
            'message': f'Dataset {dataset_id} downloaded successfully to {dataset_folder}'
        }

    async def close(self):
        await self.client.aclose()


huggingface_service = HuggingFaceService()

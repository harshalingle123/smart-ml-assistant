"""
Model Cache Service

Caches trained models locally to avoid downloading from Azure on every prediction.
Significantly improves prediction performance and reduces Azure egress costs.
"""

import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional
import hashlib


class ModelCacheService:
    """Service to manage local model caching"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the model cache service

        Args:
            cache_dir: Directory to store cached models. Defaults to ./model_cache
        """
        if cache_dir is None:
            # Default to backend/model_cache directory
            backend_dir = Path(__file__).parent.parent.parent
            cache_dir = backend_dir / "model_cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"[MODEL_CACHE] Cache directory: {self.cache_dir}")

    def _get_cache_key(self, model_id: str, blob_path: str) -> str:
        """
        Generate a unique cache key for a model

        Args:
            model_id: MongoDB model ID
            blob_path: Azure blob path

        Returns:
            Cache key (hash of model_id + blob_path)
        """
        # Use hash to create a filesystem-safe cache key
        key_string = f"{model_id}_{blob_path}"
        cache_key = hashlib.md5(key_string.encode()).hexdigest()
        return cache_key

    def get_cached_model_path(self, model_id: str, blob_path: str) -> Optional[Path]:
        """
        Check if model exists in cache and return its path

        Args:
            model_id: MongoDB model ID
            blob_path: Azure blob path

        Returns:
            Path to cached model directory if exists, None otherwise
        """
        cache_key = self._get_cache_key(model_id, blob_path)
        cache_path = self.cache_dir / cache_key / "model_files"

        if cache_path.exists():
            # Verify the model directory is valid
            if (cache_path / "predictor.pkl").exists() or list(cache_path.glob("*.pkl")):
                print(f"[MODEL_CACHE] HIT: Found cached model at {cache_path}")
                return cache_path
            else:
                print(f"[MODEL_CACHE] INVALID: Cache exists but no model files found, removing")
                # Remove invalid cache
                shutil.rmtree(cache_path.parent)
                return None
        else:
            print(f"[MODEL_CACHE] MISS: Model not in cache")
            return None

    def cache_model(
        self,
        model_id: str,
        blob_path: str,
        model_zip_bytes: bytes
    ) -> Path:
        """
        Cache a model by extracting it to the cache directory

        Args:
            model_id: MongoDB model ID
            blob_path: Azure blob path
            model_zip_bytes: Model zip file bytes

        Returns:
            Path to the cached model directory
        """
        cache_key = self._get_cache_key(model_id, blob_path)
        cache_base_path = self.cache_dir / cache_key
        cache_model_path = cache_base_path / "model_files"

        # Create cache directory
        cache_base_path.mkdir(parents=True, exist_ok=True)

        # Save zip file temporarily
        zip_path = cache_base_path / "model.zip"

        try:
            print(f"[MODEL_CACHE] Caching model...")

            # Write zip file
            with open(zip_path, 'wb') as f:
                f.write(model_zip_bytes)

            # Extract model
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(cache_model_path)

            # Remove zip file (keep only extracted model)
            zip_path.unlink()

            print(f"[MODEL_CACHE] Cached model at {cache_model_path}")
            print(f"[MODEL_CACHE] Cache size: {self._get_dir_size(cache_model_path) / 1024 / 1024:.2f} MB")

            return cache_model_path

        except Exception as e:
            # Clean up on error
            if cache_base_path.exists():
                shutil.rmtree(cache_base_path)
            raise Exception(f"Failed to cache model: {str(e)}")

    def clear_cache(self, model_id: Optional[str] = None, blob_path: Optional[str] = None):
        """
        Clear cached models

        Args:
            model_id: If provided, only clear this specific model
            blob_path: If provided with model_id, clear specific model version
        """
        if model_id and blob_path:
            # Clear specific model
            cache_key = self._get_cache_key(model_id, blob_path)
            cache_path = self.cache_dir / cache_key

            if cache_path.exists():
                shutil.rmtree(cache_path)
                print(f"[MODEL_CACHE] Cleared cache for model {model_id}")
            else:
                print(f"[MODEL_CACHE] No cache found for model {model_id}")

        else:
            # Clear all cache
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                print(f"[MODEL_CACHE] Cleared all cached models")

    def get_cache_stats(self) -> dict:
        """
        Get statistics about the cache

        Returns:
            Dictionary with cache statistics
        """
        if not self.cache_dir.exists():
            return {
                "total_models": 0,
                "total_size_mb": 0,
                "cache_dir": str(self.cache_dir)
            }

        total_models = len(list(self.cache_dir.iterdir()))
        total_size = self._get_dir_size(self.cache_dir)

        return {
            "total_models": total_models,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "cache_dir": str(self.cache_dir)
        }

    def _get_dir_size(self, path: Path) -> int:
        """
        Get total size of a directory in bytes

        Args:
            path: Directory path

        Returns:
            Total size in bytes
        """
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total


# Global instance
model_cache_service = ModelCacheService()

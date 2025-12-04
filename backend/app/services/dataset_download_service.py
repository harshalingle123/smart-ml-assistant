"""
Dataset Download Service

Centralized service for downloading datasets from both Kaggle and HuggingFace
Integrates the logic from chat.txt for comprehensive dataset management
"""

from typing import List, Dict, Optional, Any
from app.services.kaggle_service import kaggle_service
from app.services.huggingface_service import huggingface_service
from app.services.gemini_service import gemini_service
from app.core.config import settings
import os
from pathlib import Path


class DatasetDownloadService:

    def __init__(self):
        self.default_download_path = settings.DOWNLOAD_PATH

    async def search_all_sources(
        self,
        user_query: str,
        optimize_query: bool = True
    ) -> Dict[str, Any]:
        """
        EXACT IMPLEMENTATION combining extract_spec(), search_apis(), and rank_candidates()
        from dataset.py (lines 37-166)

        Args:
            user_query: User's search query
            optimize_query: Whether to optimize the query with Gemini

        Returns:
            Dict containing results from both sources
        """
        # Step 1: extract_spec() - Fix typos and extract keywords (dataset.py lines 37-72)
        if optimize_query and gemini_service.is_available():
            try:
                spec = await gemini_service.extract_spec(user_query)
                fixed_query = spec.get('fixed_query', user_query)
                keywords = spec.get('keywords', [user_query])
                search_term = " ".join(keywords)
                print(f"✓ Fixed query: '{fixed_query}'")
                print(f"✓ Keywords: {keywords}")
            except Exception as e:
                print(f"⚠ Query optimization failed: {str(e)}, using original query")
                fixed_query = user_query
                search_term = user_query
                keywords = [user_query]
        else:
            fixed_query = user_query
            search_term = user_query
            keywords = [user_query]

        print(f"\nSearching for: '{search_term}'...")

        candidates = []

        # Step 2: search_apis() - Search Kaggle and HuggingFace (dataset.py lines 75-128)

        # --- 1. Kaggle Search (EXACT from dataset.py lines 82-97) ---
        try:
            if kaggle_service.is_configured:
                k_datasets = kaggle_service.search_datasets(
                    query=search_term,
                    sort_by='votes',  # EXACT from dataset.py line 86
                    page=1
                )
                for ds in k_datasets[:15]:  # Top 15 (dataset.py line 88)
                    candidates.append(ds)
                print(f"✓ Found {len(k_datasets)} from Kaggle.")
        except Exception as e:
            print(f"✗ Kaggle Search Failed: {e}")

        # --- 2. HuggingFace Search (EXACT from dataset.py lines 102-123) ---
        # Note: HuggingFace API works without authentication (with rate limits)
        try:
            hf_datasets = await huggingface_service.search_datasets(
                query=search_term,
                limit=15,  # EXACT from dataset.py line 107
                sort="downloads",  # EXACT from dataset.py line 108
                direction=-1  # EXACT from dataset.py line 109
            )
            candidates.extend(hf_datasets)
            print(f"✓ Found {len(hf_datasets)} from Hugging Face.")
        except Exception as e:
            print(f"✗ HF Search Failed: {e}")

        # Step 3: rank_candidates() - Rank by semantic similarity (dataset.py lines 131-166)
        if gemini_service.is_available() and candidates:
            try:
                ranked_candidates = await gemini_service.rank_candidates(
                    query=fixed_query,
                    candidates=candidates
                )
                print(f"✓ Datasets ranked by semantic relevance")
            except Exception as e:
                print(f"⚠ Ranking failed: {e}, returning unranked results")
                ranked_candidates = candidates
        else:
            ranked_candidates = candidates
            print(f"⚠ Skipping ranking (Gemini not available or no candidates)")

        return {
            "original_query": user_query,
            "fixed_query": fixed_query,
            "keywords": keywords,
            "total_found": len(ranked_candidates),
            "datasets": ranked_candidates[:20],  # Return top 20
            "kaggle_count": len([d for d in ranked_candidates if d.get('source') == 'Kaggle']),
            "huggingface_count": len([d for d in ranked_candidates if d.get('source') == 'HuggingFace'])
        }


    async def download_dataset(
        self,
        dataset_id: str,
        source: str,
        download_path: Optional[str] = None
    ) -> Dict[str, Any]:
        if not download_path:
            download_path = self.default_download_path
        Path(download_path).mkdir(parents=True, exist_ok=True)
        try:
            if source == 'Kaggle':
                if not kaggle_service.is_configured:
                    return {
                        'success': False,
                        'dataset_id': dataset_id,
                        'source': source,
                        'message': 'Kaggle API is not configured',
                        'file_path': None
                    }
                result = kaggle_service.download_dataset(dataset_id, download_path)
                return {
                    'success': result.get('status') == 'success',
                    'dataset_id': dataset_id,
                    'source': source,
                    'message': result.get('message', 'Download completed'),
                    'file_path': result.get('download_path')
                }
            elif source == 'HuggingFace':
                if not huggingface_service.is_configured:
                    return {
                        'success': False,
                        'dataset_id': dataset_id,
                        'source': source,
                        'message': 'HuggingFace API is not configured',
                        'file_path': None
                    }
                result = await huggingface_service.download_dataset(dataset_id, download_path)
                return {
                    'success': result.get('status') == 'success',
                    'dataset_id': dataset_id,
                    'source': source,
                    'message': result.get('message', 'Download completed'),
                    'file_path': result.get('download_path')
                }
            else:
                return {
                    'success': False,
                    'dataset_id': dataset_id,
                    'source': source,
                    'message': f'Unknown source: {source}',
                    'file_path': None
                }
        except Exception as e:
            return {
                'success': False,
                'dataset_id': dataset_id,
                'source': source,
                'message': str(e),
                'file_path': None
            }

    async def download_multiple_datasets(
        self,
        datasets: List[Dict[str, str]],
        download_path: Optional[str] = None
    ) -> Dict[str, Any]:
        results = []
        success_count = 0
        fail_count = 0
        for dataset in datasets:
            dataset_id = dataset.get('dataset_id')
            source = dataset.get('source')
            if not dataset_id or not source:
                fail_count += 1
                continue
            result = await self.download_dataset(
                dataset_id=dataset_id,
                source=source,
                download_path=download_path
            )
            results.append(result)
            if result.get('success'):
                success_count += 1
            else:
                fail_count += 1
        return {
            'success': success_count > 0,
            'total_requested': len(datasets),
            'success_count': success_count,
            'fail_count': fail_count,
            'results': results,
            'download_path': download_path or self.default_download_path
        }


# Singleton instance
dataset_download_service = DatasetDownloadService()

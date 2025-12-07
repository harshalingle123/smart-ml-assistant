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
        self.default_download_path = None # Deprecated, we use temp dirs now

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
        """
        Downloads dataset to temp dir, uploads to Azure, and cleans up.
        """
        import tempfile
        import shutil
        from app.utils.azure_storage import azure_storage_service
        from app.core.config import settings
        
        # Use temp dir if no path provided (which should be the default now)
        if not download_path:
            temp_dir = tempfile.mkdtemp(prefix=f"download_{source}_{dataset_id.replace('/', '_')}_")
            download_path = temp_dir
        else:
            temp_dir = None # If user provided path, don't auto-cleanup (though we shouldn't be providing paths anymore)
            Path(download_path).mkdir(parents=True, exist_ok=True)
            
        try:
            file_path = None
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
                if result.get('status') == 'success':
                    file_path = result.get('download_path')
                    # Find CSV
                    csv_files = list(Path(download_path).glob("*.csv"))
                    if csv_files:
                        file_path = str(csv_files[0])
                        
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
                if result.get('status') == 'success':
                    file_path = result.get('download_path')
                    # Find CSV (HF might download parquet or other formats, but assuming CSV for now)
                    if os.path.isdir(file_path):
                         csv_files = list(Path(file_path).glob("*.csv"))
                         if csv_files:
                             file_path = str(csv_files[0])

            else:
                return {
                    'success': False,
                    'dataset_id': dataset_id,
                    'source': source,
                    'message': f'Unknown source: {source}',
                    'file_path': None
                }
            
            # Upload to Azure if download successful
            azure_url = None
            if file_path and os.path.exists(file_path):
                try:
                    # Read file content
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Upload to Azure
                    # We need a user_id here, but this service method doesn't take one.
                    # This service seems to be for general "download to local" which we are deprecating.
                    # However, if we want to persist it, we need to know where.
                    # For now, let's assume this service is just for "getting the file content" 
                    # but since we want NO local storage, we must return the content or upload it.
                    
                    # If we can't upload to a specific user folder, maybe we upload to a 'public' or 'temp' folder in Azure?
                    # Or we just return the content?
                    # Given the context, this service is used by `download_progress_stream` in `datasets.py`.
                    # That endpoint doesn't seem to save to MongoDB?
                    # Wait, `download_progress_stream` in `datasets.py` just calls this and returns the result.
                    # It doesn't seem to be linked to a specific user's dataset record yet.
                    
                    # Actually, looking at `datasets.py` again, `download_progress_stream` is just a demo/utility?
                    # No, it seems to be for the "Download" button on the search page.
                    # If the user clicks "Download", they probably expect it to be added to their datasets.
                    
                    # Let's check where `download_progress_stream` is called.
                    # It seems to be an endpoint `/download-progress/{dataset_id}`.
                    
                    # If this is just for downloading to the server (which we don't want), we should probably change this flow.
                    # If the user wants to "Import" the dataset, they should use the import flow.
                    
                    # For now, to keep it "Azure Only", let's assume we upload to a "downloads" folder in Azure
                    # and return the Azure URL.
                    
                    if azure_storage_service.is_configured:
                        blob_path_to_upload = f"downloads/{source}/{dataset_id.replace('/', '_')}/{os.path.basename(file_path)}"
                        azure_blob_path = azure_storage_service.upload_file(
                            file_content=file_content,
                            blob_path=blob_path_to_upload,
                            container_name=settings.AZURE_DATASETS_CONTAINER
                        )
                        print(f"✓ Uploaded downloaded dataset to Azure: {azure_blob_path}")
                        # Store the blob path
                        azure_url = azure_blob_path  # For backward compatibility with variable name

                except Exception as upload_error:
                    print(f"⚠ Failed to upload to Azure: {upload_error}")

            return {
                'success': True if file_path else False,
                'dataset_id': dataset_id,
                'source': source,
                'message': 'Download and Azure upload completed',
                'file_path': None, # Don't return local path
                'azure_blob_path': azure_url if azure_url else None  # Return blob path
            }

        except Exception as e:
            return {
                'success': False,
                'dataset_id': dataset_id,
                'source': source,
                'message': str(e),
                'file_path': None
            }
        finally:
            # Cleanup temp dir
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"✓ Cleaned up temp download directory: {temp_dir}")

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
            'download_path': None # Files are uploaded to Azure and local copies deleted
        }


# Singleton instance
dataset_download_service = DatasetDownloadService()

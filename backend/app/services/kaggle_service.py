import os
from typing import List, Dict, Optional
from pathlib import Path
import json
from app.core.config import settings


class KaggleService:
    """Service for interacting with Kaggle API"""

    def __init__(self):
        self.kaggle_username = settings.KAGGLE_USERNAME
        self.kaggle_key = settings.KAGGLE_KEY
        self.is_configured = bool(self.kaggle_username and self.kaggle_key)

        if self.is_configured:
            # Set Kaggle credentials as environment variables for the API
            os.environ['KAGGLE_USERNAME'] = self.kaggle_username
            os.environ['KAGGLE_KEY'] = self.kaggle_key

    def is_available(self) -> bool:
        """Check if Kaggle API is configured"""
        return self.is_configured

    def search_datasets(self, query: str, page: int = 1, max_size: int = 20, sort_by: str = 'hottest') -> List[Dict]:
        """
        Search for datasets on Kaggle
        EXACT IMPLEMENTATION from dataset.py (lines 75-128, Kaggle section)

        Args:
            query: Search query
            page: Page number (default 1)
            max_size: Max results per page (default 20)
            sort_by: Sort by (default 'hottest', use 'votes' for dataset.py compatibility)

        Returns:
            List of dataset info dictionaries
        """
        if not self.is_available():
            raise ValueError("Kaggle API is not configured. Please set KAGGLE_USERNAME and KAGGLE_KEY.")

        try:
            # Ensure environment variables are set before importing kaggle
            os.environ['KAGGLE_USERNAME'] = self.kaggle_username
            os.environ['KAGGLE_KEY'] = self.kaggle_key

            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()

            # Search datasets with EXACT parameters from dataset.py
            datasets = api.dataset_list(
                search=query,
                sort_by=sort_by,
                page=page
            )

            # Format results with EXACT structure from dataset.py (lines 89-96)
            results = []
            for d in datasets[:15]:  # Take top 15 as per dataset.py line 88
                results.append({
                    'id': d.ref,
                    'title': d.title,
                    'description': getattr(d, 'description', '') or d.title,
                    'source': 'Kaggle',
                    'url': f'https://www.kaggle.com/{d.ref}',  # d.ref already contains 'datasets/' prefix
                    'downloads': getattr(d, 'downloadCount', 0),
                    # Additional fields for compatibility
                    'ref': d.ref,
                    'size': getattr(d, 'size', 0),
                    'last_updated': str(getattr(d, 'lastUpdated', '')),
                    'download_count': getattr(d, 'downloadCount', 0),
                    'vote_count': getattr(d, 'voteCount', 0),
                    'usability_rating': getattr(d, 'usabilityRating', 0.0),
                })

            return results

        except Exception as e:
            print(f"✗ Kaggle Search Failed: {e}")
            raise Exception(f"Error searching Kaggle datasets: {str(e)}")

    def download_dataset(
        self,
        dataset_ref: str,
        download_path: str = "./data/kaggle"
    ) -> Dict[str, str]:
        """
        Download a dataset from Kaggle

        Args:
            dataset_ref: Dataset reference (e.g., 'username/dataset-name')
            download_path: Path to download the dataset

        Returns:
            Dict with download information
        """
        if not self.is_available():
            raise ValueError("Kaggle API is not configured. Please set KAGGLE_USERNAME and KAGGLE_KEY.")

        try:
            # Ensure environment variables are set before importing kaggle
            os.environ['KAGGLE_USERNAME'] = self.kaggle_username
            os.environ['KAGGLE_KEY'] = self.kaggle_key

            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()

            # Create download directory
            Path(download_path).mkdir(parents=True, exist_ok=True)

            # Download dataset
            api.dataset_download_files(
                dataset_ref,
                path=download_path,
                unzip=True
            )

            return {
                'status': 'success',
                'dataset_ref': dataset_ref,
                'download_path': download_path,
                'message': f'Dataset {dataset_ref} downloaded successfully'
            }

        except Exception as e:
            raise Exception(f"Error downloading Kaggle dataset: {str(e)}")

    def get_dataset_metadata(self, dataset_ref: str) -> Dict:
        """
        Get metadata for a specific dataset

        Args:
            dataset_ref: Dataset reference (e.g., 'username/dataset-name')

        Returns:
            Dataset metadata dictionary
        """
        if not self.is_available():
            raise ValueError("Kaggle API is not configured. Please set KAGGLE_USERNAME and KAGGLE_KEY.")

        try:
            # Ensure environment variables are set before importing kaggle
            os.environ['KAGGLE_USERNAME'] = self.kaggle_username
            os.environ['KAGGLE_KEY'] = self.kaggle_key

            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()

            # Get dataset metadata
            metadata = api.dataset_metadata(dataset_ref, path='.')

            # Read the downloaded metadata file
            metadata_file = Path('./dataset-metadata.json')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                metadata_file.unlink()  # Delete temp file
                return data
            else:
                return {'error': 'Metadata not found'}

        except Exception as e:
            raise Exception(f"Error getting dataset metadata: {str(e)}")

    def list_dataset_files(self, dataset_ref: str) -> List[str]:
        """
        List files in a dataset

        Args:
            dataset_ref: Dataset reference (e.g., 'username/dataset-name')

        Returns:
            List of filenames
        """
        if not self.is_available():
            raise ValueError("Kaggle API is not configured. Please set KAGGLE_USERNAME and KAGGLE_KEY.")

        try:
            # Ensure environment variables are set before importing kaggle
            os.environ['KAGGLE_USERNAME'] = self.kaggle_username
            os.environ['KAGGLE_KEY'] = self.kaggle_key

            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()

            # List dataset files
            files = api.dataset_list_files(dataset_ref)

            return [f.name for f in files.files]

        except Exception as e:
            raise Exception(f"Error listing dataset files: {str(e)}")


# Singleton instance
kaggle_service = KaggleService()

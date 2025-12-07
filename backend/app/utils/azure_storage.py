"""
Azure Blob Storage Service
Handles file uploads, downloads, and management for training data and models
"""
from typing import Optional, List, BinaryIO
from datetime import datetime, timedelta
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class AzureBlobStorageService:
    """Service for managing files in Azure Blob Storage"""
    
    def __init__(self):
        """Initialize Azure Blob Storage client"""
        from app.core.config import settings

        self.account_url = settings.AZURE_ACCOUNT_URL
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET

        # Container names from settings
        self.datasets_container = settings.AZURE_DATASETS_CONTAINER
        self.models_container = settings.AZURE_MODELS_CONTAINER
        
        self._blob_service_client = None
        self._is_configured = False
        
        # Check if Azure is configured
        if self.account_url and self.client_id and self.client_secret and self.tenant_id:
            self._is_configured = True
            logger.info("[AZURE] Azure Blob Storage is configured")
        else:
            logger.warning("[AZURE] Azure Blob Storage is not configured - using local filesystem fallback")
    
    @property
    def is_configured(self) -> bool:
        """Check if Azure Blob Storage is properly configured"""
        return self._is_configured
    
    def _get_blob_service_client(self):
        """Get or create blob service client with Azure AD authentication"""
        if not self._is_configured:
            raise ValueError("Azure Blob Storage is not configured")
        
        if self._blob_service_client is None:
            try:
                from azure.storage.blob import BlobServiceClient
                from azure.identity import ClientSecretCredential
                
                # Create credential using Azure AD
                credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                
                # Create blob service client
                self._blob_service_client = BlobServiceClient(
                    account_url=self.account_url,
                    credential=credential
                )
                
                logger.info("[AZURE] Blob service client initialized successfully")
                
            except Exception as e:
                logger.error(f"[AZURE] Failed to initialize blob service client: {str(e)}")
                raise
        
        return self._blob_service_client
    
    def _ensure_container_exists(self, container_name: str):
        """Ensure container exists, create if it doesn't"""
        try:
            blob_service_client = self._get_blob_service_client()
            container_client = blob_service_client.get_container_client(container_name)
            
            # Check if container exists
            if not container_client.exists():
                logger.info(f"[AZURE] Creating container: {container_name}")
                container_client.create_container()
                logger.info(f"[AZURE] Container created: {container_name}")
            
        except Exception as e:
            logger.error(f"[AZURE] Error ensuring container exists: {str(e)}")
            raise
    
    def upload_file(
        self,
        file_content: bytes,
        blob_path: str,
        container_name: Optional[str] = None,
        overwrite: bool = True
    ) -> str:
        """
        Upload file to Azure Blob Storage

        Args:
            file_content: File content as bytes
            blob_path: Path within the container (e.g., "user_123/dataset_456/data.csv")
            container_name: Container name (defaults to datasets_container)
            overwrite: Whether to overwrite existing blob

        Returns:
            Blob path (not full URL)
        """
        if not self._is_configured:
            raise ValueError("Azure Blob Storage is not configured")

        container_name = container_name or self.datasets_container

        try:
            # Ensure container exists
            self._ensure_container_exists(container_name)

            # Get blob client
            blob_service_client = self._get_blob_service_client()
            blob_client = blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_path
            )

            # Upload file
            logger.info(f"[AZURE] Uploading to: {container_name}/{blob_path}")
            blob_client.upload_blob(file_content, overwrite=overwrite)

            logger.info(f"[AZURE] Upload successful: {blob_path}")

            return blob_path  # Return blob path instead of full URL

        except Exception as e:
            logger.error(f"[AZURE] Upload failed: {str(e)}")
            raise
    
    def download_file(
        self, 
        blob_path: str, 
        container_name: Optional[str] = None
    ) -> bytes:
        """
        Download file from Azure Blob Storage
        
        Args:
            blob_path: Path within the container
            container_name: Container name (defaults to datasets_container)
            
        Returns:
            File content as bytes
        """
        if not self._is_configured:
            raise ValueError("Azure Blob Storage is not configured")
        
        container_name = container_name or self.datasets_container
        
        try:
            blob_service_client = self._get_blob_service_client()
            blob_client = blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_path
            )
            
            logger.info(f"[AZURE] Downloading from: {container_name}/{blob_path}")
            download_stream = blob_client.download_blob()
            file_content = download_stream.readall()
            
            logger.info(f"[AZURE] Download successful: {len(file_content)} bytes")
            return file_content
            
        except Exception as e:
            logger.error(f"[AZURE] Download failed: {str(e)}")
            raise
    
    def delete_file(
        self, 
        blob_path: str, 
        container_name: Optional[str] = None
    ) -> bool:
        """
        Delete file from Azure Blob Storage
        
        Args:
            blob_path: Path within the container
            container_name: Container name (defaults to datasets_container)
            
        Returns:
            True if deleted successfully
        """
        if not self._is_configured:
            raise ValueError("Azure Blob Storage is not configured")
        
        container_name = container_name or self.datasets_container
        
        try:
            blob_service_client = self._get_blob_service_client()
            blob_client = blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_path
            )
            
            logger.info(f"[AZURE] Deleting: {container_name}/{blob_path}")
            blob_client.delete_blob()
            logger.info(f"[AZURE] Delete successful")
            
            return True
            
        except Exception as e:
            logger.error(f"[AZURE] Delete failed: {str(e)}")
            return False
    
    def list_files(
        self, 
        prefix: str, 
        container_name: Optional[str] = None
    ) -> List[str]:
        """
        List files in Azure Blob Storage with given prefix
        
        Args:
            prefix: Blob path prefix (e.g., "user_123/")
            container_name: Container name (defaults to datasets_container)
            
        Returns:
            List of blob paths
        """
        if not self._is_configured:
            raise ValueError("Azure Blob Storage is not configured")
        
        container_name = container_name or self.datasets_container
        
        try:
            blob_service_client = self._get_blob_service_client()
            container_client = blob_service_client.get_container_client(container_name)
            
            logger.info(f"[AZURE] Listing files with prefix: {prefix}")
            blob_list = container_client.list_blobs(name_starts_with=prefix)
            
            file_paths = [blob.name for blob in blob_list]
            logger.info(f"[AZURE] Found {len(file_paths)} files")
            
            return file_paths
            
        except Exception as e:
            logger.error(f"[AZURE] List files failed: {str(e)}")
            raise
    
    def get_sas_url(
        self, 
        blob_path: str, 
        container_name: Optional[str] = None,
        expiry_hours: int = 24
    ) -> str:
        """
        Generate SAS URL for temporary file access
        
        Args:
            blob_path: Path within the container
            container_name: Container name (defaults to datasets_container)
            expiry_hours: Hours until SAS token expires
            
        Returns:
            SAS URL
        """
        if not self._is_configured:
            raise ValueError("Azure Blob Storage is not configured")
        
        container_name = container_name or self.datasets_container
        
        try:
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            
            blob_service_client = self._get_blob_service_client()
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=blob_service_client.account_name,
                container_name=container_name,
                blob_name=blob_path,
                account_key=None,  # Using Azure AD, not account key
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            # Construct SAS URL
            blob_client = blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_path
            )
            sas_url = f"{blob_client.url}?{sas_token}"
            
            logger.info(f"[AZURE] Generated SAS URL (expires in {expiry_hours}h)")
            return sas_url
            
        except Exception as e:
            logger.error(f"[AZURE] SAS URL generation failed: {str(e)}")
            raise
    
    def delete_folder(
        self, 
        folder_path: str, 
        container_name: Optional[str] = None
    ) -> int:
        """
        Delete all files in a folder (prefix)
        
        Args:
            folder_path: Folder path prefix (e.g., "user_123/dataset_456/")
            container_name: Container name (defaults to datasets_container)
            
        Returns:
            Number of files deleted
        """
        if not self._is_configured:
            raise ValueError("Azure Blob Storage is not configured")
        
        container_name = container_name or self.datasets_container
        
        try:
            # List all files with the prefix
            files = self.list_files(folder_path, container_name)
            
            logger.info(f"[AZURE] Deleting folder: {folder_path} ({len(files)} files)")
            
            # Delete each file
            deleted_count = 0
            for file_path in files:
                if self.delete_file(file_path, container_name):
                    deleted_count += 1
            
            logger.info(f"[AZURE] Deleted {deleted_count} files from folder")
            return deleted_count
            
        except Exception as e:
            logger.error(f"[AZURE] Delete folder failed: {str(e)}")
            raise
    
    # ==================== DATASET-SPECIFIC METHODS ====================
    
    def upload_dataset(
        self,
        user_id: str,
        dataset_id: str,
        file_content: bytes,
        filename: str
    ) -> str:
        """
        Upload dataset to Azure Blob Storage

        Args:
            user_id: User ID
            dataset_id: Dataset ID
            file_content: CSV file content as bytes
            filename: Original filename

        Returns:
            Blob path (e.g., "user_id/dataset_id/filename.csv")
        """
        blob_path = f"{user_id}/{dataset_id}/{filename}"
        return self.upload_file(
            file_content=file_content,
            blob_path=blob_path,
            container_name=self.datasets_container
        )
    
    def _extract_blob_path_from_url(self, azure_url: str, expected_container: str) -> str:
        """
        Extract blob path from Azure URL

        Args:
            azure_url: Full Azure Blob URL
            expected_container: Expected container name

        Returns:
            Blob path

        Example:
            Input: https://account.blob.core.windows.net/datasets/user_id/dataset_id/file.csv
            Output: user_id/dataset_id/file.csv
        """
        # URL format: https://{account}.blob.core.windows.net/{container}/{blob_path}
        url_parts = azure_url.split("/")

        if len(url_parts) < 5:
            raise ValueError(f"Invalid Azure URL format: {azure_url}")

        # Extract container name (index 3) and blob path (index 4+)
        container_name = url_parts[3]
        blob_path = "/".join(url_parts[4:])

        logger.info(f"[AZURE] Extracted container: {container_name}")
        logger.info(f"[AZURE] Extracted blob path: {blob_path}")

        # Verify container matches expected
        if container_name != expected_container:
            logger.warning(f"[AZURE] Container mismatch: expected '{expected_container}', got '{container_name}'")

        return blob_path

    def download_dataset(self, path_or_url: str) -> bytes:
        """
        Download dataset from Azure Blob Storage

        Args:
            path_or_url: Either a blob path (user_id/dataset_id/file.csv)
                        OR a full Azure URL (for backward compatibility)

        Returns:
            File content as bytes
        """
        logger.info(f"[AZURE] Downloading dataset: {path_or_url}")

        try:
            if path_or_url.startswith("http"):
                # Legacy: Full URL provided, extract blob path
                logger.info(f"[AZURE] Detected full URL, extracting blob path for backward compatibility")
                blob_path = self._extract_blob_path_from_url(path_or_url, self.datasets_container)
            else:
                # New: Blob path provided directly
                blob_path = path_or_url

            return self.download_file(
                blob_path=blob_path,
                container_name=self.datasets_container
            )

        except Exception as e:
            logger.error(f"[AZURE] Failed to download dataset: {path_or_url}")
            logger.error(f"[AZURE] Error: {str(e)}")
            raise ValueError(f"Failed to download dataset: {path_or_url}. Error: {str(e)}")
    
    def delete_dataset(self, user_id: str, dataset_id: str) -> int:
        """
        Delete all files for a dataset
        
        Args:
            user_id: User ID
            dataset_id: Dataset ID
            
        Returns:
            Number of files deleted
        """
        folder_path = f"{user_id}/{dataset_id}/"
        return self.delete_folder(
            folder_path=folder_path,
            container_name=self.datasets_container
        )
    
    # ==================== MODEL-SPECIFIC METHODS ====================
    
    def upload_model(
        self,
        user_id: str,
        model_id: str,
        model_bytes: bytes,
        version: str = "v1"
    ) -> str:
        """
        Upload trained model to Azure Blob Storage

        Args:
            user_id: User ID
            model_id: Model ID
            model_bytes: Model zip file content as bytes
            version: Model version (e.g., "v1", "v2")

        Returns:
            Blob path (e.g., "user_id/model_id/model-v1.zip")
        """
        blob_path = f"{user_id}/{model_id}/model-{version}.zip"
        return self.upload_file(
            file_content=model_bytes,
            blob_path=blob_path,
            container_name=self.models_container
        )
    
    def download_model(self, path_or_url: str) -> bytes:
        """
        Download model from Azure Blob Storage

        Args:
            path_or_url: Either a blob path (user_id/model_id/model-v1.zip)
                        OR a full Azure URL (for backward compatibility)

        Returns:
            Model zip file content as bytes
        """
        logger.info(f"[AZURE] Downloading model: {path_or_url}")

        try:
            if path_or_url.startswith("http"):
                # Legacy: Full URL provided, extract blob path
                logger.info(f"[AZURE] Detected full URL, extracting blob path for backward compatibility")
                blob_path = self._extract_blob_path_from_url(path_or_url, self.models_container)
            else:
                # New: Blob path provided directly
                blob_path = path_or_url

            return self.download_file(
                blob_path=blob_path,
                container_name=self.models_container
            )

        except Exception as e:
            logger.error(f"[AZURE] Failed to download model: {path_or_url}")
            logger.error(f"[AZURE] Error: {str(e)}")
            raise ValueError(f"Failed to download model: {path_or_url}. Error: {str(e)}")
    
    def delete_model(self, user_id: str, model_id: str) -> int:
        """
        Delete all files for a model (all versions)
        
        Args:
            user_id: User ID
            model_id: Model ID
            
        Returns:
            Number of files deleted
        """
        folder_path = f"{user_id}/{model_id}/"
        return self.delete_folder(
            folder_path=folder_path,
            container_name=self.models_container
        )


# Global instance
azure_storage_service = AzureBlobStorageService()

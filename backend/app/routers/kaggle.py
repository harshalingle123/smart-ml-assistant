from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from app.models.mongodb_models import User
from app.dependencies import get_current_user
from app.services.kaggle_service import kaggle_service

router = APIRouter(prefix="/api/kaggle", tags=["Kaggle"])


class DatasetSearchRequest(BaseModel):
    query: str
    page: int = 1
    max_size: int = 20


class DatasetDownloadRequest(BaseModel):
    dataset_ref: str
    # Removed: download_path (deprecated - using Azure Blob Storage only)


@router.get("/status")
async def check_kaggle_status(current_user: User = Depends(get_current_user)):
    """Check if Kaggle API is configured"""
    return {
        "configured": kaggle_service.is_available(),
        "message": "Kaggle API is configured" if kaggle_service.is_available() else "Kaggle API credentials not set. Please configure KAGGLE_USERNAME and KAGGLE_KEY."
    }


@router.post("/search")
async def search_datasets(
    search_request: DatasetSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for datasets on Kaggle

    Args:
        search_request: Search parameters

    Returns:
        List of datasets matching the search query
    """
    if not kaggle_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kaggle API is not configured. Please set KAGGLE_USERNAME and KAGGLE_KEY."
        )

    try:
        datasets = kaggle_service.search_datasets(
            query=search_request.query,
            page=search_request.page,
            max_size=search_request.max_size
        )

        return {
            "success": True,
            "count": len(datasets),
            "datasets": datasets
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search datasets: {str(e)}"
        )


@router.post("/download")
async def download_dataset(
    download_request: DatasetDownloadRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Download a dataset from Kaggle to Azure Blob Storage (uses temp directory, auto-cleaned)

    Args:
        download_request: Dataset reference (e.g., "username/dataset-name")

    Returns:
        Download status with Azure URL
    """
    if not kaggle_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kaggle API is not configured. Please set KAGGLE_USERNAME and KAGGLE_KEY."
        )

    try:
        # Use dataset_download_service which handles temp dir + Azure upload
        from app.services.dataset_download_service import dataset_download_service

        result = await dataset_download_service.download_dataset(
            dataset_id=download_request.dataset_ref,
            source="Kaggle",
            download_path=None  # Uses temp dir, uploads to Azure, auto-cleanup
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download dataset: {str(e)}"
        )


@router.get("/dataset/{dataset_ref:path}/files")
async def list_dataset_files(
    dataset_ref: str,
    current_user: User = Depends(get_current_user)
):
    """
    List files in a Kaggle dataset

    Args:
        dataset_ref: Dataset reference (e.g., 'username/dataset-name')

    Returns:
        List of filenames
    """
    if not kaggle_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kaggle API is not configured. Please set KAGGLE_USERNAME and KAGGLE_KEY."
        )

    try:
        files = kaggle_service.list_dataset_files(dataset_ref)

        return {
            "success": True,
            "dataset_ref": dataset_ref,
            "files": files,
            "count": len(files)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list dataset files: {str(e)}"
        )


@router.get("/dataset/{dataset_ref:path}/metadata")
async def get_dataset_metadata(
    dataset_ref: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get metadata for a Kaggle dataset

    Args:
        dataset_ref: Dataset reference (e.g., 'username/dataset-name')

    Returns:
        Dataset metadata
    """
    if not kaggle_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kaggle API is not configured. Please set KAGGLE_USERNAME and KAGGLE_KEY."
        )

    try:
        metadata = kaggle_service.get_dataset_metadata(dataset_ref)

        return {
            "success": True,
            "dataset_ref": dataset_ref,
            "metadata": metadata
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dataset metadata: {str(e)}"
        )

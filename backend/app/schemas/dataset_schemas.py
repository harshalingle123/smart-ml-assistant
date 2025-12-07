from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, Any, List, Dict
from datetime import datetime
from app.models.mongodb_models import PyObjectId


class DatasetCreate(BaseModel):
    name: str
    file_name: str
    row_count: int
    column_count: int
    file_size: int
    status: str = "processing"
    # Removed: preview_data (legacy field - use sample_data instead)


class DatasetDownloadRequest(BaseModel):
    dataset_id: str = Field(..., serialization_alias="datasetId")
    source: str
    # Removed: download_path (Azure-only storage, no local paths)

    model_config = ConfigDict(
        populate_by_name=True
    )


class DatasetDownloadResponse(BaseModel):
    success: bool
    dataset_id: str = Field(serialization_alias="datasetId")
    source: str
    message: str
    azure_url: Optional[str] = Field(default=None, serialization_alias="azureUrl")  # Azure Blob Storage URL

    model_config = ConfigDict(
        populate_by_name=True
    )


class MultipleDatasetDownloadRequest(BaseModel):
    datasets: List[Dict[str, str]]
    # Removed: download_path (Azure-only storage, no local paths)

    model_config = ConfigDict(
        populate_by_name=True
    )


class MultipleDatasetDownloadResponse(BaseModel):
    success: bool
    total_requested: int = Field(serialization_alias="totalRequested")
    success_count: int = Field(serialization_alias="successCount")
    fail_count: int = Field(serialization_alias="failCount")
    results: List[Dict[str, Any]]
    # Removed: download_path (files uploaded to Azure, no local paths)

    model_config = ConfigDict(
        populate_by_name=True
    )


class DatasetSearchRequest(BaseModel):
    query: str
    optimize_query: bool = Field(default=True, serialization_alias="optimizeQuery")

    model_config = ConfigDict(
        populate_by_name=True
    )


class DatasetSearchResponse(BaseModel):
    success: bool
    original_query: str = Field(serialization_alias="originalQuery")
    fixed_query: str = Field(serialization_alias="fixedQuery")
    total_found: int = Field(serialization_alias="totalFound")
    kaggle_count: int = Field(serialization_alias="kaggleCount")
    huggingface_count: int = Field(serialization_alias="huggingfaceCount")
    datasets: List[Dict[str, Any]]

    model_config = ConfigDict(
        populate_by_name=True
    )


class DatasetResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    user_id: PyObjectId = Field(serialization_alias="userId")
    name: str
    file_name: str = Field(serialization_alias="fileName")
    row_count: int = Field(serialization_alias="rowCount")
    column_count: int = Field(serialization_alias="columnCount")
    file_size: int = Field(serialization_alias="fileSize")
    status: str
    azure_dataset_url: Optional[str] = Field(default=None, serialization_alias="azureDatasetUrl")  # Azure Blob Storage URL
    uploaded_at: datetime = Field(serialization_alias="uploadedAt")
    source: Optional[str] = None
    kaggle_ref: Optional[str] = Field(default=None, serialization_alias="kaggleRef")
    huggingface_dataset_id: Optional[str] = Field(default=None, serialization_alias="huggingfaceDatasetId")
    huggingface_url: Optional[str] = Field(default=None, serialization_alias="huggingfaceUrl")
    # Removed: download_path (local filesystem), preview_data (legacy - use sample_data)
    # Metadata fields (OK to keep for preview purposes):
    schema: Optional[list] = None
    sample_data: Optional[list] = Field(default=None, serialization_alias="sampleData")
    target_column: Optional[str] = Field(default=None, serialization_alias="targetColumn")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        protected_namespaces=(),
        json_encoders={PyObjectId: str}
    )

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
    preview_data: Optional[Any] = None


class DatasetDownloadRequest(BaseModel):
    dataset_id: str = Field(..., serialization_alias="datasetId")
    source: str
    download_path: Optional[str] = Field(default=None, serialization_alias="downloadPath")

    model_config = ConfigDict(
        populate_by_name=True
    )


class DatasetDownloadResponse(BaseModel):
    success: bool
    dataset_id: str = Field(serialization_alias="datasetId")
    source: str
    message: str
    file_path: Optional[str] = Field(default=None, serialization_alias="filePath")

    model_config = ConfigDict(
        populate_by_name=True
    )


class MultipleDatasetDownloadRequest(BaseModel):
    datasets: List[Dict[str, str]]
    download_path: Optional[str] = Field(default=None, serialization_alias="downloadPath")

    model_config = ConfigDict(
        populate_by_name=True
    )


class MultipleDatasetDownloadResponse(BaseModel):
    success: bool
    total_requested: int = Field(serialization_alias="totalRequested")
    success_count: int = Field(serialization_alias="successCount")
    fail_count: int = Field(serialization_alias="failCount")
    results: List[Dict[str, Any]]
    download_path: str = Field(serialization_alias="downloadPath")

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
    preview_data: Optional[Any] = Field(default=None, serialization_alias="previewData")
    uploaded_at: datetime = Field(serialization_alias="uploadedAt")
    source: Optional[str] = None
    kaggle_ref: Optional[str] = Field(default=None, serialization_alias="kaggleRef")
    huggingface_dataset_id: Optional[str] = Field(default=None, serialization_alias="huggingfaceDatasetId")
    huggingface_url: Optional[str] = Field(default=None, serialization_alias="huggingfaceUrl")
    download_path: Optional[str] = Field(default=None, serialization_alias="downloadPath")
    schema: Optional[list] = None
    sample_data: Optional[list] = Field(default=None, serialization_alias="sampleData")
    target_column: Optional[str] = Field(default=None, serialization_alias="targetColumn")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        protected_namespaces=(),
        json_encoders={PyObjectId: str}
    )

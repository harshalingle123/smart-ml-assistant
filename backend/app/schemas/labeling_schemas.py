from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class LabelDataResponse(BaseModel):
    """Labeling result structure"""
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    objects: Optional[List[dict]] = None
    topics: Optional[List[str]] = None
    events: Optional[List[dict]] = None
    entities: Optional[List[dict]] = None
    safety_flags: Optional[List[str]] = None


class CreateDatasetRequest(BaseModel):
    """Request to create a new labeling dataset"""
    name: str = Field(..., min_length=1, max_length=100)
    task: str = Field(...)  # "general_analysis", "object_detection", etc.
    target_labels: Optional[List[str]] = None


class UpdateDatasetRequest(BaseModel):
    """Request to update a dataset"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_labels: Optional[List[str]] = None


class LabelingFileResponse(BaseModel):
    """Response for a single labeling file"""
    id: str
    dataset_id: str
    filename: str
    original_name: str
    media_type: str
    file_size: int
    azure_blob_path: str
    preview_url: Optional[str] = None
    status: str
    result: Optional[LabelDataResponse] = None
    error_message: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None


class LabelingDatasetResponse(BaseModel):
    """Response for a labeling dataset"""
    id: str
    name: str
    task: str
    target_labels: Optional[List[str]] = None
    total_files: int
    completed_files: int
    failed_files: int
    status: str
    created_at: datetime
    updated_at: datetime


class LabelingDatasetDetailResponse(BaseModel):
    """Detailed dataset response with files"""
    id: str
    name: str
    task: str
    target_labels: Optional[List[str]] = None
    total_files: int
    completed_files: int
    failed_files: int
    status: str
    created_at: datetime
    updated_at: datetime
    files: List[LabelingFileResponse] = []


class RefineLabelsRequest(BaseModel):
    """Request to refine labels after user edits"""
    verified_labels: List[str] = Field(...)


class LabelSuggestionsRequest(BaseModel):
    """Request to get label suggestions"""
    file_ids: List[str] = Field(..., max_items=10)


class LabelSuggestionsResponse(BaseModel):
    """Response with suggested labels"""
    suggested_labels: List[str] = Field(...)


class ExportDatasetRequest(BaseModel):
    """Request to export dataset"""
    format: str = Field(..., pattern="^(json|csv|zip)$")


class AnalyzeFilesRequest(BaseModel):
    """Request to analyze files"""
    file_ids: List[str] = Field(..., min_items=1)

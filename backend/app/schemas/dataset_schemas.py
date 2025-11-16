from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, Any
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

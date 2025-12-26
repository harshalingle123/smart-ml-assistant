from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict
from enum import Enum


class LabelingTaskType(str, Enum):
    """Enum for different labeling task types"""
    IMAGE_CLASSIFICATION = "image_classification"
    OBJECT_DETECTION = "object_detection"
    TEXT_CLASSIFICATION = "text_classification"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    VIDEO_ANALYSIS = "video_analysis"
    ENTITY_EXTRACTION = "entity_extraction"
    NER = "ner"


class LabelingConfig(BaseModel):
    """Configuration for labeling tasks"""
    task_type: LabelingTaskType
    target_labels: Optional[List[str]] = Field(
        None,
        description="Optional predefined labels for classification tasks"
    )
    num_suggestions: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of label suggestions to generate"
    )
    confidence_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for labels"
    )


class DetectedObject(BaseModel):
    """Object detected in an image"""
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: Optional[Dict[str, float]] = Field(
        None,
        description="Bounding box coordinates {x, y, width, height}"
    )


class ImageLabel(BaseModel):
    """Labeling results for images"""
    filename: str
    task_type: str
    classification: Optional[str] = None
    objects: Optional[List[DetectedObject]] = None
    scene_description: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class TextLabel(BaseModel):
    """Labeling results for text"""
    text: str
    label: str
    sentiment: Optional[str] = None  # positive, negative, neutral
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: Optional[str] = None


class Entity(BaseModel):
    """Named entity extracted from text"""
    text: str
    type: str  # PERSON, ORG, LOCATION, DATE, etc.
    start_index: int = Field(ge=0)
    end_index: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class EntityExtraction(BaseModel):
    """Entity extraction results"""
    text: str
    entities: List[Entity]
    summary: Optional[str] = None


class Transcript(BaseModel):
    """Transcription results for audio/video"""
    filename: str
    transcript: str
    language: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None


class RefineLabelRequest(BaseModel):
    """Request to refine labels based on user feedback"""
    labels: List[Union[ImageLabel, TextLabel, EntityExtraction, Transcript]]
    feedback: str = Field(
        ...,
        description="User feedback or corrections to apply"
    )


class LabelingResponse(BaseModel):
    """Response containing labeling results"""
    results: List[Union[ImageLabel, TextLabel, EntityExtraction, Transcript]]
    task_type: str
    total_processed: int
    success_count: int
    error_count: int = 0
    errors: Optional[List[str]] = None

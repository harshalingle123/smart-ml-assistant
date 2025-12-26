from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List
import logging
import json

from app.services.labeling_service import labeling_service
from app.schemas.labeling_schemas import (
    LabelingConfig,
    LabelingResponse,
    RefineLabelRequest,
    LabelingTaskType,
    ImageLabel,
    TextLabel,
    EntityExtraction,
    Transcript
)
from app.dependencies import get_current_user
from app.models.mongodb_models import User

router = APIRouter(prefix="/api/labeling", tags=["labeling"])
logger = logging.getLogger(__name__)


@router.post("/generate-labels", response_model=LabelingResponse)
async def generate_labels(
    files: List[UploadFile] = File(...),
    config: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    Generate labels for uploaded files using AI

    Args:
        files: List of files to label
        config: JSON string containing LabelingConfig
        current_user: Authenticated user

    Returns:
        LabelingResponse with labeled results
    """
    try:
        # Parse configuration
        try:
            config_dict = json.loads(config)
            labeling_config = LabelingConfig(**config_dict)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid config JSON: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")

        logger.info(f"User {current_user.email} requesting labeling for {len(files)} files with task type: {labeling_config.task_type}")

        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        if len(files) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 files allowed per request")

        # Process files based on task type
        results = []
        success_count = 0
        error_count = 0
        errors = []

        # Group files by content type
        image_files = []
        text_files = []
        audio_video_files = []

        for file in files:
            content = await file.read()

            # Detect file type
            content_type = file.content_type or ""
            filename = file.filename or "unknown"

            if content_type.startswith("image/") or filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                image_files.append((filename, content))
            elif content_type.startswith("text/") or filename.lower().endswith(('.txt', '.csv', '.md')):
                try:
                    text_content = content.decode('utf-8')
                    text_files.append((filename, text_content))
                except UnicodeDecodeError:
                    errors.append(f"Could not decode text file: {filename}")
                    error_count += 1
            elif content_type.startswith(("audio/", "video/")) or filename.lower().endswith(('.mp3', '.wav', '.mp4', '.avi', '.mov')):
                audio_video_files.append((filename, content))
            else:
                errors.append(f"Unsupported file type: {filename} ({content_type})")
                error_count += 1

        # Process based on task type
        try:
            if labeling_config.task_type in [LabelingTaskType.IMAGE_CLASSIFICATION, LabelingTaskType.OBJECT_DETECTION]:
                if image_files:
                    image_results = await labeling_service.label_images(image_files, labeling_config)
                    results.extend(image_results)
                    success_count += len(image_results)
                else:
                    file_types = ", ".join(set([f.content_type or "unknown" for f in files]))
                    raise HTTPException(
                        status_code=400,
                        detail=f"No image files found for image labeling task. Uploaded file types: {file_types}. Please upload image files (.jpg, .png, etc.) or change the task type to match your files."
                    )

            elif labeling_config.task_type in [LabelingTaskType.TEXT_CLASSIFICATION, LabelingTaskType.SENTIMENT_ANALYSIS]:
                if text_files:
                    text_results = await labeling_service.label_text(text_files, labeling_config)
                    results.extend(text_results)
                    success_count += len(text_results)
                else:
                    file_types = ", ".join(set([f.content_type or "unknown" for f in files]))
                    raise HTTPException(
                        status_code=400,
                        detail=f"No text files found for text labeling task. Uploaded file types: {file_types}. Please upload text files (.txt, .csv, .md) or change the task type to match your files."
                    )

            elif labeling_config.task_type in [LabelingTaskType.ENTITY_EXTRACTION, LabelingTaskType.NER]:
                if text_files:
                    entity_results = await labeling_service.extract_entities(text_files, labeling_config)
                    results.extend(entity_results)
                    success_count += len(entity_results)
                else:
                    file_types = ", ".join(set([f.content_type or "unknown" for f in files]))
                    raise HTTPException(
                        status_code=400,
                        detail=f"No text files found for entity extraction task. Uploaded file types: {file_types}. Please upload text files (.txt, .csv, .md) or change the task type to match your files."
                    )

            elif labeling_config.task_type in [LabelingTaskType.AUDIO_TRANSCRIPTION, LabelingTaskType.VIDEO_ANALYSIS]:
                if audio_video_files:
                    transcript_results = await labeling_service.transcribe_audio_video(audio_video_files, labeling_config)
                    results.extend(transcript_results)
                    success_count += len(transcript_results)
                else:
                    file_types = ", ".join(set([f.content_type or "unknown" for f in files]))
                    raise HTTPException(
                        status_code=400,
                        detail=f"No audio/video files found for transcription task. Uploaded file types: {file_types}. Please upload audio/video files (.mp3, .mp4, etc.) or change the task type to match your files."
                    )

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported task type: {labeling_config.task_type}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during labeling: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Labeling failed: {str(e)}")

        # Return response
        return LabelingResponse(
            results=results,
            task_type=labeling_config.task_type.value,
            total_processed=len(files),
            success_count=success_count,
            error_count=error_count,
            errors=errors if errors else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_labels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/refine-analysis")
async def refine_analysis(
    request: RefineLabelRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Refine labels based on user feedback

    Args:
        request: Refine label request with labels and feedback
        current_user: Authenticated user

    Returns:
        Refined labels
    """
    try:
        logger.info(f"User {current_user.email} requesting label refinement")

        # Refine labels
        refined_labels = await labeling_service.refine_labels(
            request.labels,
            request.feedback
        )

        return {
            "refined_labels": refined_labels,
            "message": "Labels refined successfully"
        }

    except Exception as e:
        logger.error(f"Error refining labels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refine labels: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for labeling service"""
    try:
        is_available = labeling_service.gemini_service.is_available()

        return {
            "status": "healthy" if is_available else "degraded",
            "gemini_available": is_available,
            "service": "labeling"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "labeling"
        }

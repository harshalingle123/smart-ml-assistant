from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional
import asyncio
import json
import io
import os
import csv
import zipfile
from datetime import datetime
from bson import ObjectId

from app.mongodb import mongodb
from app.models.mongodb_models import User, LabelingDataset, LabelingFile, LabelData
from app.schemas.labeling_schemas import (
    CreateDatasetRequest,
    UpdateDatasetRequest,
    LabelingDatasetResponse,
    LabelingDatasetDetailResponse,
    LabelingFileResponse,
    RefineLabelsRequest,
    LabelSuggestionsRequest,
    LabelSuggestionsResponse,
    AnalyzeFilesRequest,
    LabelDataResponse
)
from app.dependencies import get_current_user
from app.services.labeling_service import labeling_service
from app.utils.azure_storage import azure_storage_service
from app.core.config import settings

router = APIRouter(prefix="/api/labeling", tags=["Labeling"])


def get_media_type(filename: str) -> str:
    """Determine media type from filename"""
    ext = filename.lower().split('.')[-1]

    image_exts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
    video_exts = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
    audio_exts = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a']
    text_exts = ['txt', 'md', 'csv', 'json', 'xml', 'html', 'py', 'js', 'java', 'cpp', 'c', 'h']
    pdf_exts = ['pdf']

    if ext in image_exts:
        return "image"
    elif ext in video_exts:
        return "video"
    elif ext in audio_exts:
        return "audio"
    elif ext in text_exts:
        return "text"
    elif ext in pdf_exts:
        return "pdf"
    else:
        return "unknown"


@router.post("/datasets", response_model=LabelingDatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    request: CreateDatasetRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new labeling dataset"""
    try:
        dataset = LabelingDataset(
            user_id=current_user.id,
            name=request.name,
            task=request.task,
            target_labels=request.target_labels,
            total_files=0,
            completed_files=0,
            failed_files=0,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        result = await mongodb.db.labeling_datasets.insert_one(dataset.dict(by_alias=True, exclude={"id"}))
        dataset.id = result.inserted_id

        return LabelingDatasetResponse(
            id=str(dataset.id),
            name=dataset.name,
            task=dataset.task,
            target_labels=dataset.target_labels,
            total_files=dataset.total_files,
            completed_files=dataset.completed_files,
            failed_files=dataset.failed_files,
            status=dataset.status,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dataset: {str(e)}"
        )


@router.get("/datasets", response_model=List[LabelingDatasetResponse])
async def list_datasets(current_user: User = Depends(get_current_user)):
    """List all datasets for the current user"""
    try:
        datasets = await mongodb.db.labeling_datasets.find(
            {"user_id": current_user.id, "status": {"$ne": "archived"}}
        ).sort("created_at", -1).to_list(length=100)

        return [
            LabelingDatasetResponse(
                id=str(ds["_id"]),
                name=ds["name"],
                task=ds["task"],
                target_labels=ds.get("target_labels"),
                total_files=ds.get("total_files", 0),
                completed_files=ds.get("completed_files", 0),
                failed_files=ds.get("failed_files", 0),
                status=ds["status"],
                created_at=ds["created_at"],
                updated_at=ds["updated_at"]
            )
            for ds in datasets
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list datasets: {str(e)}"
        )


@router.get("/datasets/{dataset_id}", response_model=LabelingDatasetDetailResponse)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific dataset with all its files"""
    try:
        dataset = await mongodb.db.labeling_datasets.find_one({
            "_id": ObjectId(dataset_id),
            "user_id": current_user.id
        })

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        # Get all files in the dataset
        files = await mongodb.db.labeling_files.find(
            {"dataset_id": ObjectId(dataset_id)}
        ).sort("uploaded_at", -1).to_list(length=1000)

        file_responses = [
            LabelingFileResponse(
                id=str(f["_id"]),
                dataset_id=str(f["dataset_id"]),
                filename=f["filename"],
                original_name=f["original_name"],
                media_type=f["media_type"],
                file_size=f["file_size"],
                azure_blob_path=f["azure_blob_path"],
                preview_url=f.get("preview_url"),
                status=f["status"],
                result=LabelDataResponse(**f["result"]) if f.get("result") else None,
                error_message=f.get("error_message"),
                uploaded_at=f["uploaded_at"],
                processed_at=f.get("processed_at")
            )
            for f in files
        ]

        return LabelingDatasetDetailResponse(
            id=str(dataset["_id"]),
            name=dataset["name"],
            task=dataset["task"],
            target_labels=dataset.get("target_labels"),
            total_files=dataset.get("total_files", 0),
            completed_files=dataset.get("completed_files", 0),
            failed_files=dataset.get("failed_files", 0),
            status=dataset["status"],
            created_at=dataset["created_at"],
            updated_at=dataset["updated_at"],
            files=file_responses
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dataset: {str(e)}"
        )


@router.patch("/datasets/{dataset_id}", response_model=LabelingDatasetResponse)
async def update_dataset(
    dataset_id: str,
    request: UpdateDatasetRequest,
    current_user: User = Depends(get_current_user)
):
    """Update a dataset"""
    try:
        update_data = {}
        if request.name:
            update_data["name"] = request.name
        if request.target_labels is not None:
            update_data["target_labels"] = request.target_labels

        update_data["updated_at"] = datetime.utcnow()

        result = await mongodb.db.labeling_datasets.find_one_and_update(
            {"_id": ObjectId(dataset_id), "user_id": current_user.id},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        return LabelingDatasetResponse(
            id=str(result["_id"]),
            name=result["name"],
            task=result["task"],
            target_labels=result.get("target_labels"),
            total_files=result.get("total_files", 0),
            completed_files=result.get("completed_files", 0),
            failed_files=result.get("failed_files", 0),
            status=result["status"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dataset: {str(e)}"
        )


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a dataset and all its files"""
    try:
        # Get all files to delete from Azure
        files = await mongodb.db.labeling_files.find(
            {"dataset_id": ObjectId(dataset_id)}
        ).to_list(length=None)

        # Delete from Azure Storage
        for file_doc in files:
            try:
                await asyncio.to_thread(azure_storage_service.delete_file, file_doc["azure_blob_path"])
            except Exception as e:
                print(f"Warning: Failed to delete blob {file_doc['azure_blob_path']}: {e}")

        # Delete files from database
        await mongodb.db.labeling_files.delete_many({"dataset_id": ObjectId(dataset_id)})

        # Delete dataset
        result = await mongodb.db.labeling_datasets.delete_one({
            "_id": ObjectId(dataset_id),
            "user_id": current_user.id
        })

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dataset: {str(e)}"
        )


@router.post("/datasets/{dataset_id}/files", response_model=List[LabelingFileResponse])
async def upload_files(
    dataset_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload files to a dataset"""
    try:
        # Verify dataset exists
        dataset = await mongodb.db.labeling_datasets.find_one({
            "_id": ObjectId(dataset_id),
            "user_id": current_user.id
        })

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        # Check subscription limits
        from app.services.subscription_service import subscription_service
        await subscription_service.check_labeling_limit(current_user.id, len(files))

        uploaded_files = []

        for file in files:
            # Read file content
            content = await file.read()
            file_size = len(content)

            # Check file size limit
            await subscription_service.check_labeling_file_size(current_user.id, file_size)

            # Determine media type
            media_type = get_media_type(file.filename)

            # Generate unique filename
            file_id = ObjectId()
            filename = f"{file_id}_{file.filename}"

            # Upload to Azure
            blob_path = f"labeling/{current_user.id}/{dataset_id}/{filename}"
            await asyncio.to_thread(azure_storage_service.upload_file, content, blob_path)

            # Create file record
            labeling_file = LabelingFile(
                id=file_id,
                dataset_id=ObjectId(dataset_id),
                user_id=current_user.id,
                filename=filename,
                original_name=file.filename,
                media_type=media_type,
                file_size=file_size,
                azure_blob_path=blob_path,
                status="pending",
                uploaded_at=datetime.utcnow()
            )

            await mongodb.db.labeling_files.insert_one(labeling_file.dict(by_alias=True))

            uploaded_files.append(LabelingFileResponse(
                id=str(labeling_file.id),
                dataset_id=str(labeling_file.dataset_id),
                filename=labeling_file.filename,
                original_name=labeling_file.original_name,
                media_type=labeling_file.media_type,
                file_size=labeling_file.file_size,
                azure_blob_path=labeling_file.azure_blob_path,
                status=labeling_file.status,
                uploaded_at=labeling_file.uploaded_at
            ))

        # Update dataset file count
        await mongodb.db.labeling_datasets.update_one(
            {"_id": ObjectId(dataset_id)},
            {"$inc": {"total_files": len(files)}, "$set": {"updated_at": datetime.utcnow()}}
        )

        return uploaded_files

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload files: {str(e)}"
        )


@router.post("/analyze")
async def analyze_files(
    request: AnalyzeFilesRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze files with AI labeling"""
    try:
        # Process files asynchronously
        for file_id in request.file_ids:
            # Update status to processing
            await mongodb.db.labeling_files.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": {"status": "processing"}}
            )

            # Get file and dataset info
            file_doc = await mongodb.db.labeling_files.find_one({"_id": ObjectId(file_id)})
            if not file_doc:
                continue

            dataset_doc = await mongodb.db.labeling_datasets.find_one({"_id": file_doc["dataset_id"]})
            if not dataset_doc:
                continue

            try:
                # Download from Azure
                file_content = await asyncio.to_thread(azure_storage_service.download_file, file_doc["azure_blob_path"])

                # Generate labels
                label_data = await labeling_service.generate_labels(
                    file_content=file_content,
                    media_type=file_doc["media_type"],
                    task=dataset_doc["task"],
                    filename=file_doc["original_name"],
                    target_labels=dataset_doc.get("target_labels")
                )

                if label_data:
                    # Update file with results
                    await mongodb.db.labeling_files.update_one(
                        {"_id": ObjectId(file_id)},
                        {
                            "$set": {
                                "status": "completed",
                                "result": label_data.dict(),
                                "processed_at": datetime.utcnow()
                            }
                        }
                    )

                    # Update dataset stats
                    await mongodb.db.labeling_datasets.update_one(
                        {"_id": file_doc["dataset_id"]},
                        {"$inc": {"completed_files": 1}}
                    )

                    # Update usage
                    from app.services.subscription_service import subscription_service
                    await subscription_service.increment_labeling_usage(current_user.id)

                else:
                    # Mark as failed
                    await mongodb.db.labeling_files.update_one(
                        {"_id": ObjectId(file_id)},
                        {
                            "$set": {
                                "status": "failed",
                                "error_message": "Failed to generate labels"
                            }
                        }
                    )

                    await mongodb.db.labeling_datasets.update_one(
                        {"_id": file_doc["dataset_id"]},
                        {"$inc": {"failed_files": 1}}
                    )

            except Exception as e:
                # Mark as failed
                await mongodb.db.labeling_files.update_one(
                    {"_id": ObjectId(file_id)},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": str(e)
                        }
                    }
                )

                await mongodb.db.labeling_datasets.update_one(
                    {"_id": file_doc["dataset_id"]},
                    {"$inc": {"failed_files": 1}}
                )

        return {"message": f"Processing {len(request.file_ids)} files"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze files: {str(e)}"
        )


@router.post("/files/{file_id}/refine", response_model=LabelingFileResponse)
async def refine_labels(
    file_id: str,
    request: RefineLabelsRequest,
    current_user: User = Depends(get_current_user)
):
    """Refine labels after user edits"""
    try:
        file_doc = await mongodb.db.labeling_files.find_one({
            "_id": ObjectId(file_id),
            "user_id": current_user.id
        })

        if not file_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        dataset_doc = await mongodb.db.labeling_datasets.find_one({"_id": file_doc["dataset_id"]})

        # Download file
        file_content = await asyncio.to_thread(azure_storage_service.download_file, file_doc["azure_blob_path"])

        # Refine analysis
        label_data = await labeling_service.refine_analysis(
            file_content=file_content,
            media_type=file_doc["media_type"],
            task=dataset_doc["task"],
            filename=file_doc["original_name"],
            verified_labels=request.verified_labels
        )

        if label_data:
            await mongodb.db.labeling_files.update_one(
                {"_id": ObjectId(file_id)},
                {
                    "$set": {
                        "result": label_data.dict(),
                        "processed_at": datetime.utcnow()
                    }
                }
            )

            return LabelingFileResponse(
                id=str(file_doc["_id"]),
                dataset_id=str(file_doc["dataset_id"]),
                filename=file_doc["filename"],
                original_name=file_doc["original_name"],
                media_type=file_doc["media_type"],
                file_size=file_doc["file_size"],
                azure_blob_path=file_doc["azure_blob_path"],
                status=file_doc["status"],
                result=LabelDataResponse(**label_data.dict()),
                uploaded_at=file_doc["uploaded_at"],
                processed_at=datetime.utcnow()
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refine labels"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine labels: {str(e)}"
        )


@router.post("/suggestions", response_model=LabelSuggestionsResponse)
async def get_label_suggestions(
    request: LabelSuggestionsRequest,
    current_user: User = Depends(get_current_user)
):
    """Get AI-suggested labels based on files"""
    try:
        # Get file info
        files = await mongodb.db.labeling_files.find({
            "_id": {"$in": [ObjectId(fid) for fid in request.file_ids]}
        }).to_list(length=10)

        filenames = [f["original_name"] for f in files]

        if not filenames:
            return LabelSuggestionsResponse(suggested_labels=[])

        # Get dataset task
        dataset_doc = await mongodb.db.labeling_datasets.find_one({"_id": files[0]["dataset_id"]})

        suggestions = await labeling_service.get_label_suggestions(
            filenames=filenames,
            task=dataset_doc["task"]
        )

        return LabelSuggestionsResponse(suggested_labels=suggestions)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.get("/datasets/{dataset_id}/export")
async def export_dataset(
    dataset_id: str,
    format: str = "json",
    current_user: User = Depends(get_current_user)
):
    """Export dataset in various formats"""
    try:
        dataset = await mongodb.db.labeling_datasets.find_one({
            "_id": ObjectId(dataset_id),
            "user_id": current_user.id
        })

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        files = await mongodb.db.labeling_files.find(
            {"dataset_id": ObjectId(dataset_id), "status": "completed"}
        ).to_list(length=None)

        if format == "json":
            # Export as JSON
            export_data = {
                "dataset": {
                    "name": dataset["name"],
                    "task": dataset["task"],
                    "created_at": dataset["created_at"].isoformat(),
                    "total_files": len(files)
                },
                "files": [
                    {
                        "filename": f["original_name"],
                        "media_type": f["media_type"],
                        "result": f.get("result", {})
                    }
                    for f in files
                ]
            }

            return JSONResponse(content=export_data)

        elif format == "csv":
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(["filename", "summary", "sentiment", "topics", "entities", "safety_flags"])

            # Write data
            for f in files:
                result = f.get("result", {})
                writer.writerow([
                    f["original_name"],
                    result.get("summary", ""),
                    result.get("sentiment", ""),
                    ";".join(result.get("topics", [])),
                    ";".join([f"{e['name']}({e['type']})" for e in result.get("entities", [])]),
                    ";".join(result.get("safety_flags", []))
                ])

            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={dataset['name']}.csv"}
            )

        elif format == "zip":
            # Export as ZIP for fine-tuning
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Create training data JSONL
                jsonl_content = ""
                for f in files:
                    result = f.get("result", {})
                    jsonl_content += json.dumps({
                        "prompt": f"Analyze this {f['media_type']} file",
                        "completion": json.dumps(result)
                    }) + "\n"

                zip_file.writestr("training_data.jsonl", jsonl_content)

                # Add metadata
                metadata = {
                    "dataset_name": dataset["name"],
                    "task": dataset["task"],
                    "total_files": len(files),
                    "created_at": dataset["created_at"].isoformat()
                }
                zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))

            zip_buffer.seek(0)
            return StreamingResponse(
                iter([zip_buffer.getvalue()]),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={dataset['name']}.zip"}
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Choose 'json', 'csv', or 'zip'"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export dataset: {str(e)}"
        )


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a file"""
    try:
        file_doc = await mongodb.db.labeling_files.find_one({
            "_id": ObjectId(file_id),
            "user_id": current_user.id
        })

        if not file_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        # Delete from Azure
        try:
            await asyncio.to_thread(azure_storage_service.delete_file, file_doc["azure_blob_path"])
        except Exception as e:
            print(f"Warning: Failed to delete blob: {e}")

        # Delete from database
        await mongodb.db.labeling_files.delete_one({"_id": ObjectId(file_id)})

        # Update dataset stats
        await mongodb.db.labeling_datasets.update_one(
            {"_id": file_doc["dataset_id"]},
            {"$inc": {"total_files": -1}}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/files/{file_id}", response_model=LabelingFileResponse)
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific file"""
    try:
        file_doc = await mongodb.db.labeling_files.find_one({
            "_id": ObjectId(file_id),
            "user_id": current_user.id
        })

        if not file_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        return LabelingFileResponse(
            id=str(file_doc["_id"]),
            dataset_id=str(file_doc["dataset_id"]),
            filename=file_doc["filename"],
            original_name=file_doc["original_name"],
            media_type=file_doc["media_type"],
            file_size=file_doc["file_size"],
            azure_blob_path=file_doc["azure_blob_path"],
            preview_url=file_doc.get("preview_url"),
            status=file_doc["status"],
            result=LabelDataResponse(**file_doc["result"]) if file_doc.get("result") else None,
            error_message=file_doc.get("error_message"),
            uploaded_at=file_doc["uploaded_at"],
            processed_at=file_doc.get("processed_at")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file: {str(e)}"
        )

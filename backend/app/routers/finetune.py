from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from app.mongodb import mongodb
from app.models.mongodb_models import User, FineTuneJob, Dataset
from app.schemas.finetune_schemas import FineTuneJobCreate, FineTuneJobResponse
from app.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/finetune", tags=["Fine-tuning"])


@router.post("", response_model=FineTuneJobResponse, status_code=status.HTTP_201_CREATED)
async def create_finetune_job(
    job_data: FineTuneJobCreate,
    current_user: User = Depends(get_current_user),
):
    dataset = await mongodb.database["datasets"].find_one(
        {"_id": job_data.dataset_id, "user_id": current_user.id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    new_job = FineTuneJob(
        user_id=current_user.id,
        model_id=job_data.model_id,
        dataset_id=job_data.dataset_id,
        base_model=job_data.base_model,
        status=job_data.status,
        progress=job_data.progress,
        current_step=job_data.current_step,
        logs=job_data.logs,
    )

    result = await mongodb.database["finetune_jobs"].insert_one(new_job.dict(by_alias=True))
    new_job.id = result.inserted_id

    # Update user's fine_tune_jobs count
    await mongodb.database["users"].update_one(
        {"_id": current_user.id},
        {"$inc": {"fine_tune_jobs": 1}}
    )

    return FineTuneJobResponse(**new_job.dict(by_alias=True))


@router.get("", response_model=List[FineTuneJobResponse])
async def get_finetune_jobs(
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    jobs_cursor = mongodb.database["finetune_jobs"].find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).skip(offset).limit(limit)
    jobs = await jobs_cursor.to_list(length=limit)
    return [FineTuneJobResponse(**job) for job in jobs]


@router.get("/{job_id}", response_model=FineTuneJobResponse)
async def get_finetune_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    job = await mongodb.database["finetune_jobs"].find_one(
        {"_id": ObjectId(job_id), "user_id": current_user.id}
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fine-tune job not found"
        )

    return FineTuneJobResponse(**job)


@router.patch("/{job_id}/status", response_model=FineTuneJobResponse)
async def update_finetune_job_status(
    job_id: str,
    status_update: str,
    progress: int = None,
    current_step: str = None,
    logs: str = None,
    current_user: User = Depends(get_current_user),
):
    update_data = {"status": status_update}

    if progress is not None:
        update_data["progress"] = progress

    if current_step is not None:
        update_data["current_step"] = current_step

    if logs is not None:
        update_data["logs"] = logs

    if status_update == "completed":
        update_data["completed_at"] = datetime.utcnow()

    result = await mongodb.database["finetune_jobs"].update_one(
        {"_id": ObjectId(job_id), "user_id": current_user.id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fine-tune job not found or no changes made"
        )

    updated_job = await mongodb.database["finetune_jobs"].find_one({"_id": ObjectId(job_id)})
    return FineTuneJobResponse(**updated_job)

"""
Training Jobs Router - ML Model Training Execution
Handles training job creation, execution, monitoring, and progress tracking
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import random
import asyncio

from app.models.mongodb_models import User, TrainingJob
from app.routers.auth import get_current_user
from app.mongodb import mongodb
from app.services.gemini_service import GeminiService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/training/jobs", tags=["training"])

# Initialize services
gemini_service = GeminiService()


# Request/Response Models
class CreateTrainingJobRequest(BaseModel):
    model_id: str = Field(..., description="HuggingFace model ID to fine-tune")
    dataset_id: str = Field(..., description="Dataset ID for training")
    task_type: str = Field(..., description="ML task type")
    job_name: str = Field(..., description="Name for the training job")
    hyperparameters: dict = Field(default_factory=dict, description="Training hyperparameters")
    training_config: dict = Field(default_factory=dict, description="Additional training config")


class UpdateJobStatusRequest(BaseModel):
    status: str = Field(..., description="New status: queued, training, completed, failed, cancelled")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")


# ==================== BACKGROUND TASKS ====================

async def simulate_training_job(job_id: str):
    """
    Simulate training job execution with progress updates

    In production, this would:
    1. Spin up GPU instance
    2. Load dataset
    3. Fine-tune model
    4. Save trained model
    5. Deploy to inference endpoint
    """
    try:
        # Training phases with estimated durations
        phases = [
            {"name": "Initializing", "duration": 5, "progress": 10},
            {"name": "Loading dataset", "duration": 10, "progress": 25},
            {"name": "Preprocessing data", "duration": 15, "progress": 40},
            {"name": "Training model (Epoch 1/3)", "duration": 30, "progress": 60},
            {"name": "Training model (Epoch 2/3)", "duration": 30, "progress": 75},
            {"name": "Training model (Epoch 3/3)", "duration": 30, "progress": 90},
            {"name": "Evaluating model", "duration": 10, "progress": 95},
            {"name": "Saving model", "duration": 5, "progress": 100}
        ]

        for phase in phases:
            # Update job progress
            await mongodb.db.training_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "progress": phase["progress"],
                        "current_phase": phase["name"],
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "logs": {
                            "timestamp": datetime.utcnow(),
                            "level": "INFO",
                            "message": f"Phase: {phase['name']}"
                        }
                    }
                }
            )

            # Simulate processing time (in production, this would be actual training)
            await asyncio.sleep(phase["duration"])

        # Training complete - update final metrics
        final_metrics = {
            "accuracy": round(random.uniform(0.85, 0.95), 4),
            "loss": round(random.uniform(0.1, 0.3), 4),
            "f1_score": round(random.uniform(0.82, 0.93), 4),
            "precision": round(random.uniform(0.83, 0.94), 4),
            "recall": round(random.uniform(0.81, 0.92), 4),
            "training_time_seconds": sum(p["duration"] for p in phases),
            "total_epochs": 3,
            "best_epoch": 2
        }

        await mongodb.db.training_jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": "completed",
                    "progress": 100,
                    "metrics": final_metrics,
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "logs": {
                        "timestamp": datetime.utcnow(),
                        "level": "INFO",
                        "message": f"Training completed! Accuracy: {final_metrics['accuracy']}"
                    }
                }
            }
        )

    except Exception as e:
        # Handle training failure
        await mongodb.db.training_jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": "failed",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "logs": {
                        "timestamp": datetime.utcnow(),
                        "level": "ERROR",
                        "message": f"Training failed: {str(e)}"
                    }
                }
            }
        )


# ==================== ENDPOINTS ====================

@router.get("/")
async def get_training_jobs(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all training jobs for the current user"""
    try:
        # Build query filter
        query_filter = {"user_id": str(current_user.id)}
        if status:
            query_filter["status"] = status

        # Get jobs from database
        jobs_cursor = mongodb.db.training_jobs.find(query_filter).sort("created_at", -1)
        jobs = await jobs_cursor.to_list(length=100)

        # Convert ObjectId to string
        for job in jobs:
            job["id"] = str(job["_id"])
            job.pop("_id", None)

        return {
            "success": True,
            "jobs": jobs,
            "total": len(jobs),
            "filter": {"status": status} if status else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training jobs: {str(e)}")


@router.post("/")
async def create_training_job(
    request: CreateTrainingJobRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Create and start a new training job

    This is the core of the ML training pipeline
    """
    try:
        # Validate dataset exists
        dataset = await mongodb.db.datasets.find_one({
            "_id": ObjectId(request.dataset_id),
            "user_id": str(current_user.id)
        })

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Estimate cost and time (simple calculation)
        dataset_size = dataset.get("num_rows", 10000)
        epochs = request.hyperparameters.get("epochs", 3)

        # Rough estimates
        estimated_hours = (dataset_size / 10000) * epochs * 0.5  # 0.5 hours per 10k samples per epoch
        gpu_cost_per_hour = 0.50
        estimated_cost = estimated_hours * gpu_cost_per_hour

        # Create training job
        training_job = TrainingJob(
            user_id=str(current_user.id),
            chat_id=None,  # Optional: link to chat if created from conversation
            model_id=request.model_id,
            dataset_id=request.dataset_id,
            task_type=request.task_type,
            status="queued",
            progress=0,
            estimated_cost=round(estimated_cost, 2),
            estimated_duration_hours=round(estimated_hours, 2),
            hyperparameters=request.hyperparameters or {
                "epochs": 3,
                "batch_size": 8,
                "learning_rate": 2e-5,
                "warmup_steps": 500
            },
            training_config=request.training_config or {
                "model_name": request.model_id,
                "training_type": "lora",  # LoRA fine-tuning by default (faster & cheaper)
                "gpu_type": "T4"
            },
            logs=[{
                "timestamp": datetime.utcnow(),
                "level": "INFO",
                "message": f"Training job '{request.job_name}' created and queued"
            }],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Save to database
        result = await mongodb.db.training_jobs.insert_one(training_job.model_dump(by_alias=True))
        job_id = str(result.inserted_id)

        # Start training in background
        background_tasks.add_task(simulate_training_job, job_id)

        # Update status to training
        await mongodb.db.training_jobs.update_one(
            {"_id": result.inserted_id},
            {
                "$set": {
                    "status": "training",
                    "started_at": datetime.utcnow()
                }
            }
        )

        # Get the created job
        created_job = await mongodb.db.training_jobs.find_one({"_id": result.inserted_id})
        created_job["id"] = str(created_job["_id"])
        created_job.pop("_id", None)

        return {
            "success": True,
            "message": "Training job created and started successfully!",
            "job": created_job,
            "estimates": {
                "cost_usd": round(estimated_cost, 2),
                "duration_hours": round(estimated_hours, 2),
                "duration_minutes": round(estimated_hours * 60, 1)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create training job: {str(e)}")


@router.get("/{job_id}")
async def get_training_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific training job"""
    try:
        # Find job
        job = await mongodb.db.training_jobs.find_one({
            "_id": ObjectId(job_id),
            "user_id": str(current_user.id)
        })

        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")

        # Convert ObjectId to string
        job["id"] = str(job["_id"])
        job.pop("_id", None)

        return {
            "success": True,
            "job": job
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training job: {str(e)}")


@router.patch("/{job_id}/status")
async def update_job_status(
    job_id: str,
    request: UpdateJobStatusRequest,
    current_user: User = Depends(get_current_user)
):
    """Update the status of a training job"""
    try:
        # Build update dict
        update_dict = {
            "status": request.status,
            "updated_at": datetime.utcnow()
        }

        if request.progress is not None:
            update_dict["progress"] = request.progress

        # Add log entry
        log_entry = {
            "timestamp": datetime.utcnow(),
            "level": "INFO",
            "message": request.message or f"Status changed to {request.status}"
        }

        # Update job
        result = await mongodb.db.training_jobs.update_one(
            {
                "_id": ObjectId(job_id),
                "user_id": str(current_user.id)
            },
            {
                "$set": update_dict,
                "$push": {"logs": log_entry}
            }
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Training job not found")

        # Get updated job
        job = await mongodb.db.training_jobs.find_one({"_id": ObjectId(job_id)})
        job["id"] = str(job["_id"])
        job.pop("_id", None)

        return {
            "success": True,
            "message": "Job status updated successfully",
            "job": job
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update job status: {str(e)}")


@router.post("/{job_id}/cancel")
async def cancel_training_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a running training job"""
    try:
        # Find job
        job = await mongodb.db.training_jobs.find_one({
            "_id": ObjectId(job_id),
            "user_id": str(current_user.id)
        })

        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")

        if job.get("status") not in ["queued", "training"]:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled in its current status")

        # Update job to cancelled
        await mongodb.db.training_jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": "cancelled",
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "logs": {
                        "timestamp": datetime.utcnow(),
                        "level": "WARNING",
                        "message": "Training job cancelled by user"
                    }
                }
            }
        )

        return {
            "success": True,
            "message": "Training job cancelled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/{job_id}/logs")
async def get_training_logs(
    job_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get logs for a training job"""
    try:
        # Find job
        job = await mongodb.db.training_jobs.find_one({
            "_id": ObjectId(job_id),
            "user_id": str(current_user.id)
        })

        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")

        # Get logs (most recent first)
        logs = job.get("logs", [])
        logs = logs[-limit:]  # Get last N logs

        return {
            "success": True,
            "logs": logs,
            "total": len(logs),
            "job_id": job_id,
            "status": job.get("status"),
            "progress": job.get("progress", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.get("/{job_id}/metrics")
async def get_training_metrics(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get training metrics for a job"""
    try:
        # Find job
        job = await mongodb.db.training_jobs.find_one({
            "_id": ObjectId(job_id),
            "user_id": str(current_user.id)
        })

        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")

        metrics = job.get("metrics", {})

        if not metrics:
            return {
                "success": True,
                "message": "Training in progress - metrics not yet available",
                "job_id": job_id,
                "status": job.get("status"),
                "progress": job.get("progress", 0)
            }

        return {
            "success": True,
            "metrics": metrics,
            "job_id": job_id,
            "status": job.get("status")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/{job_id}/deploy")
async def deploy_trained_model(
    job_id: str,
    deployment_name: str = Query(..., description="Name for the deployment"),
    current_user: User = Depends(get_current_user)
):
    """Deploy a completed training job to production"""
    try:
        # Find job
        job = await mongodb.db.training_jobs.find_one({
            "_id": ObjectId(job_id),
            "user_id": str(current_user.id)
        })

        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")

        if job.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Only completed jobs can be deployed")

        # Generate API endpoint
        deployment_id = str(ObjectId())
        api_endpoint = f"/api/deployed/{deployment_id}/predict"

        # Create deployment
        from app.models.mongodb_models import Deployment

        deployment = Deployment(
            user_id=str(current_user.id),
            model_id=job.get("model_id"),
            name=deployment_name,
            description=f"Deployment of training job {job_id}",
            status="active",
            api_endpoint=api_endpoint,
            model_type="finetuned",
            task_type=job.get("task_type"),
            created_at=datetime.utcnow(),
            metadata={
                "training_job_id": job_id,
                "metrics": job.get("metrics", {})
            }
        )

        result = await mongodb.db.deployments.insert_one(deployment.model_dump(by_alias=True))

        # Get created deployment
        created_deployment = await mongodb.db.deployments.find_one({"_id": result.inserted_id})
        created_deployment["id"] = str(created_deployment["_id"])
        created_deployment.pop("_id", None)

        return {
            "success": True,
            "message": "Model deployed successfully!",
            "deployment": created_deployment,
            "api_endpoint": f"https://api.yourplatform.com{api_endpoint}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deploy model: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for training jobs service"""
    try:
        total = await mongodb.db.training_jobs.count_documents({})
        active = await mongodb.db.training_jobs.count_documents({"status": "training"})
        queued = await mongodb.db.training_jobs.count_documents({"status": "queued"})

        return {
            "success": True,
            "status": "operational",
            "total_jobs": total,
            "active_jobs": active,
            "queued_jobs": queued,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "status": "degraded",
            "error": str(e)
        }

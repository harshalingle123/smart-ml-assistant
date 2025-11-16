"""
Deployments Router - Model Deployment Management
Handles deployment lifecycle, API endpoints, monitoring, and metrics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import random

from app.models.mongodb_models import User, Deployment
from app.routers.auth import get_current_user
from app.mongodb import mongodb
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/deployments", tags=["deployments"])


# Request/Response Models
class CreateDeploymentRequest(BaseModel):
    model_id: str = Field(..., description="Model ID to deploy")
    name: str = Field(..., description="Deployment name")
    description: Optional[str] = Field(None, description="Deployment description")
    model_type: str = Field("custom", description="Model type: custom, prebuilt, finetuned")
    task_type: Optional[str] = Field(None, description="Task type")


class UpdateDeploymentRequest(BaseModel):
    status: Optional[str] = Field(None, description="Deployment status")
    name: Optional[str] = Field(None, description="Update deployment name")
    description: Optional[str] = Field(None, description="Update description")


class TestDeploymentRequest(BaseModel):
    input_data: dict = Field(..., description="Input data for testing")


# ==================== ENDPOINTS ====================

@router.get("/")
async def get_deployments(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all deployments for the current user"""
    try:
        # Build query filter
        query_filter = {"user_id": str(current_user.id)}
        if status:
            query_filter["status"] = status

        # Get deployments from database
        deployments_cursor = mongodb.db.deployments.find(query_filter).sort("created_at", -1)
        deployments = await deployments_cursor.to_list(length=100)

        # Convert ObjectId to string
        for deployment in deployments:
            deployment["id"] = str(deployment["_id"])
            deployment.pop("_id", None)

        return {
            "success": True,
            "deployments": deployments,
            "total": len(deployments),
            "filter": {"status": status} if status else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployments: {str(e)}")


@router.post("/")
async def create_deployment(
    request: CreateDeploymentRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new deployment"""
    try:
        # Generate unique API endpoint
        deployment_id = str(ObjectId())
        api_endpoint = f"/api/deployed/{deployment_id}/predict"

        # Create deployment record
        deployment = Deployment(
            user_id=str(current_user.id),
            model_id=request.model_id,
            name=request.name,
            description=request.description or f"Deployment of model {request.model_id}",
            status="deploying",
            api_endpoint=api_endpoint,
            model_type=request.model_type,
            task_type=request.task_type,
            created_at=datetime.utcnow(),
            metadata={
                "deployment_started": datetime.utcnow().isoformat()
            }
        )

        # Save to database
        result = await mongodb.db.deployments.insert_one(deployment.model_dump(by_alias=True))

        # Get the created deployment
        created_deployment = await mongodb.db.deployments.find_one({"_id": result.inserted_id})
        created_deployment["id"] = str(created_deployment["_id"])
        created_deployment.pop("_id", None)

        # Simulate deployment process (in production, this would trigger actual deployment)
        # Update status to active after a delay (in real implementation, this would be handled by a background task)
        await mongodb.db.deployments.update_one(
            {"_id": result.inserted_id},
            {
                "$set": {
                    "status": "active",
                    "metadata.deployment_completed": datetime.utcnow().isoformat()
                }
            }
        )

        # Get updated deployment
        created_deployment = await mongodb.db.deployments.find_one({"_id": result.inserted_id})
        created_deployment["id"] = str(created_deployment["_id"])
        created_deployment.pop("_id", None)

        return {
            "success": True,
            "message": "Deployment created successfully!",
            "deployment": created_deployment,
            "api_endpoint": f"https://api.yourplatform.com{api_endpoint}",
            "usage_example": {
                "curl": f"""curl -X POST https://api.yourplatform.com{api_endpoint} \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"text": "Your input here"}}'""",
                "python": f"""import requests

response = requests.post(
    "https://api.yourplatform.com{api_endpoint}",
    headers={{"Authorization": "Bearer YOUR_API_KEY"}},
    json={{"text": "Your input here"}}
)
print(response.json())"""
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create deployment: {str(e)}")


@router.get("/{deployment_id}")
async def get_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific deployment"""
    try:
        # Find deployment
        deployment = await mongodb.db.deployments.find_one({
            "_id": ObjectId(deployment_id),
            "user_id": str(current_user.id)
        })

        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")

        # Convert ObjectId to string
        deployment["id"] = str(deployment["_id"])
        deployment.pop("_id", None)

        return {
            "success": True,
            "deployment": deployment
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployment: {str(e)}")


@router.patch("/{deployment_id}")
async def update_deployment(
    deployment_id: str,
    request: UpdateDeploymentRequest,
    current_user: User = Depends(get_current_user)
):
    """Update deployment settings"""
    try:
        # Build update dict
        update_dict = {}
        if request.status:
            update_dict["status"] = request.status
        if request.name:
            update_dict["name"] = request.name
        if request.description:
            update_dict["description"] = request.description

        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Update deployment
        result = await mongodb.db.deployments.update_one(
            {
                "_id": ObjectId(deployment_id),
                "user_id": str(current_user.id)
            },
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Deployment not found")

        # Get updated deployment
        deployment = await mongodb.db.deployments.find_one({"_id": ObjectId(deployment_id)})
        deployment["id"] = str(deployment["_id"])
        deployment.pop("_id", None)

        return {
            "success": True,
            "message": "Deployment updated successfully",
            "deployment": deployment
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update deployment: {str(e)}")


@router.delete("/{deployment_id}")
async def delete_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a deployment"""
    try:
        # Delete deployment
        result = await mongodb.db.deployments.delete_one({
            "_id": ObjectId(deployment_id),
            "user_id": str(current_user.id)
        })

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Deployment not found")

        return {
            "success": True,
            "message": "Deployment deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete deployment: {str(e)}")


@router.post("/{deployment_id}/test")
async def test_deployment(
    deployment_id: str,
    request: TestDeploymentRequest,
    current_user: User = Depends(get_current_user)
):
    """Test a deployment with sample input"""
    try:
        # Find deployment
        deployment = await mongodb.db.deployments.find_one({
            "_id": ObjectId(deployment_id),
            "user_id": str(current_user.id)
        })

        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")

        if deployment.get("status") != "active":
            raise HTTPException(status_code=400, detail="Deployment is not active")

        # Simulate model inference
        task_type = deployment.get("task_type", "")

        if task_type == "sentiment-analysis" or "sentiment" in task_type:
            result = {
                "label": "POSITIVE" if "good" in str(request.input_data).lower() else "NEGATIVE",
                "confidence": 0.92
            }
        elif task_type == "text-classification":
            result = {
                "label": "Technology",
                "confidence": 0.88
            }
        elif task_type == "question-answering":
            result = {
                "answer": "This is a sample answer based on the context provided.",
                "confidence": 0.85
            }
        else:
            result = {
                "output": "Sample prediction from deployed model",
                "confidence": 0.90
            }

        return {
            "success": True,
            "deployment_id": deployment_id,
            "input": request.input_data,
            "output": result,
            "latency_ms": random.randint(50, 150),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment test failed: {str(e)}")


@router.get("/{deployment_id}/metrics")
async def get_deployment_metrics(
    deployment_id: str,
    timeframe: str = "24h",
    current_user: User = Depends(get_current_user)
):
    """
    Get metrics for a deployment

    Timeframes: 1h, 24h, 7d, 30d
    """
    try:
        # Find deployment
        deployment = await mongodb.db.deployments.find_one({
            "_id": ObjectId(deployment_id),
            "user_id": str(current_user.id)
        })

        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")

        # Generate sample metrics (in production, these would come from monitoring system)
        now = datetime.utcnow()

        # Parse timeframe
        if timeframe == "1h":
            hours = 1
            data_points = 12  # 5-minute intervals
        elif timeframe == "24h":
            hours = 24
            data_points = 24  # hourly intervals
        elif timeframe == "7d":
            hours = 24 * 7
            data_points = 7  # daily intervals
        elif timeframe == "30d":
            hours = 24 * 30
            data_points = 30  # daily intervals
        else:
            hours = 24
            data_points = 24

        # Generate sample metrics
        request_counts = [random.randint(50, 200) for _ in range(data_points)]
        latencies = [random.randint(50, 150) for _ in range(data_points)]
        error_rates = [random.uniform(0, 2) for _ in range(data_points)]

        metrics = {
            "deployment_id": deployment_id,
            "timeframe": timeframe,
            "summary": {
                "total_requests": sum(request_counts),
                "average_latency_ms": sum(latencies) / len(latencies),
                "error_rate_percent": sum(error_rates) / len(error_rates),
                "uptime_percent": 99.9,
                "p50_latency_ms": sorted(latencies)[len(latencies) // 2],
                "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)],
                "p99_latency_ms": sorted(latencies)[int(len(latencies) * 0.99)]
            },
            "time_series": {
                "requests_per_interval": request_counts,
                "average_latency_per_interval": latencies,
                "error_rate_per_interval": error_rates
            },
            "status": deployment.get("status"),
            "last_updated": datetime.utcnow().isoformat()
        }

        return {
            "success": True,
            "metrics": metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get recent logs for a deployment"""
    try:
        # Find deployment
        deployment = await mongodb.db.deployments.find_one({
            "_id": ObjectId(deployment_id),
            "user_id": str(current_user.id)
        })

        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")

        # Generate sample logs (in production, these would come from logging system)
        log_levels = ["INFO", "WARNING", "ERROR"]
        sample_logs = []

        for i in range(min(limit, 20)):
            level = random.choice(log_levels)
            timestamp = datetime.utcnow() - timedelta(minutes=i * 5)

            if level == "INFO":
                message = f"Request processed successfully in {random.randint(50, 150)}ms"
            elif level == "WARNING":
                message = "High latency detected in model inference"
            else:
                message = "Rate limit exceeded for API key"

            sample_logs.append({
                "timestamp": timestamp.isoformat(),
                "level": level,
                "message": message,
                "metadata": {
                    "deployment_id": deployment_id,
                    "request_id": str(ObjectId())
                }
            })

        return {
            "success": True,
            "logs": sample_logs,
            "total": len(sample_logs),
            "limit": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.post("/{deployment_id}/scale")
async def scale_deployment(
    deployment_id: str,
    replicas: int = Query(..., ge=1, le=10, description="Number of replicas (1-10)"),
    current_user: User = Depends(get_current_user)
):
    """Scale deployment to handle more traffic"""
    try:
        # Find deployment
        deployment = await mongodb.db.deployments.find_one({
            "_id": ObjectId(deployment_id),
            "user_id": str(current_user.id)
        })

        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")

        # Update metadata with scaling info
        await mongodb.db.deployments.update_one(
            {"_id": ObjectId(deployment_id)},
            {
                "$set": {
                    "metadata.replicas": replicas,
                    "metadata.last_scaled": datetime.utcnow().isoformat()
                }
            }
        )

        return {
            "success": True,
            "message": f"Deployment scaled to {replicas} replicas",
            "replicas": replicas,
            "estimated_capacity": f"{replicas * 100} requests/second"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scale deployment: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for deployments service"""
    try:
        count = await mongodb.db.deployments.count_documents({})
        active_count = await mongodb.db.deployments.count_documents({"status": "active"})

        return {
            "success": True,
            "status": "operational",
            "total_deployments": count,
            "active_deployments": active_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "status": "degraded",
            "error": str(e)
        }

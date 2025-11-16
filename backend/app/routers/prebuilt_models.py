"""
Pre-built Models Router - CASE 4 Implementation
Provides instant deployment of production-ready pre-trained models
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.mongodb_models import User, PrebuiltModel, Deployment
from app.routers.auth import get_current_user
from app.mongodb import mongodb
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/prebuilt-models", tags=["prebuilt-models"])


# Request/Response Models
class TestModelRequest(BaseModel):
    input_data: dict = Field(..., description="Input data for testing")


class DeployModelRequest(BaseModel):
    model_id: str = Field(..., description="Pre-built model ID to deploy")
    deployment_name: str = Field(..., description="Name for the deployment")
    description: Optional[str] = Field(None, description="Deployment description")


# ==================== ENDPOINTS ====================

@router.get("/")
async def get_prebuilt_models(
    task: Optional[str] = None,
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all available pre-built models

    This is the core of CASE 4: Pre-built Model Deployment
    """
    try:
        # Build query filter
        query_filter = {}
        if task:
            query_filter["task_type"] = task
        if language:
            query_filter["languages"] = language

        # Get models from database
        models_cursor = mongodb.db.prebuilt_models.find(query_filter)
        models = await models_cursor.to_list(length=100)

        # Convert ObjectId to string
        for model in models:
            model["id"] = str(model["_id"])
            model.pop("_id", None)

        return {
            "success": True,
            "models": models,
            "total": len(models),
            "filters": {
                "task": task,
                "language": language
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pre-built models: {str(e)}")


@router.get("/{model_id}")
async def get_prebuilt_model(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific pre-built model"""
    try:
        # Find model
        model = await mongodb.db.prebuilt_models.find_one({"_id": ObjectId(model_id)})

        if not model:
            raise HTTPException(status_code=404, detail="Pre-built model not found")

        # Convert ObjectId to string
        model["id"] = str(model["_id"])
        model.pop("_id", None)

        return {
            "success": True,
            "model": model
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model details: {str(e)}")


@router.post("/{model_id}/test")
async def test_prebuilt_model(
    model_id: str,
    request: TestModelRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Test a pre-built model with sample input

    This allows users to try the model before deploying
    """
    try:
        # Find model
        model = await mongodb.db.prebuilt_models.find_one({"_id": ObjectId(model_id)})

        if not model:
            raise HTTPException(status_code=404, detail="Pre-built model not found")

        # Simulate model inference (in production, this would call the actual model)
        # For demo purposes, we'll return a mock response based on model type
        task_type = model.get("task_type", "")

        if task_type == "sentiment-analysis":
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
                "output": "Sample output from the model",
                "confidence": 0.90
            }

        return {
            "success": True,
            "model_id": model_id,
            "model_name": model.get("name"),
            "input": request.input_data,
            "output": result,
            "latency_ms": 45,  # Simulated latency
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model test failed: {str(e)}")


@router.post("/{model_id}/deploy")
async def deploy_prebuilt_model(
    model_id: str,
    request: DeployModelRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Instantly deploy a pre-built model with a production API endpoint

    This is the key feature of CASE 4: Instant deployment without training
    """
    try:
        # Find model
        model = await mongodb.db.prebuilt_models.find_one({"_id": ObjectId(model_id)})

        if not model:
            raise HTTPException(status_code=404, detail="Pre-built model not found")

        # Generate unique API endpoint
        deployment_id = str(ObjectId())
        api_endpoint = f"/api/deployed/{deployment_id}/predict"

        # Create deployment record
        deployment = Deployment(
            user_id=str(current_user.id),
            model_id=model_id,
            name=request.deployment_name,
            description=request.description or f"Deployment of {model.get('name')}",
            status="active",
            api_endpoint=api_endpoint,
            model_type="prebuilt",
            task_type=model.get("task_type"),
            created_at=datetime.utcnow()
        )

        # Save to database
        result = await mongodb.db.deployments.insert_one(deployment.model_dump(by_alias=True))

        # Get the created deployment
        created_deployment = await mongodb.db.deployments.find_one({"_id": result.inserted_id})
        created_deployment["id"] = str(created_deployment["_id"])
        created_deployment.pop("_id", None)

        return {
            "success": True,
            "message": "Pre-built model deployed successfully!",
            "deployment": created_deployment,
            "api_endpoint": f"https://api.yourplatform.com{api_endpoint}",
            "api_key_required": True,
            "model_info": {
                "name": model.get("name"),
                "task_type": model.get("task_type"),
                "accuracy": model.get("accuracy"),
                "latency_ms": model.get("latency_ms")
            },
            "usage_example": {
                "curl": f"""curl -X POST https://api.yourplatform.com{api_endpoint} \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"text": "Your input text here"}}'""",
                "python": f"""import requests

response = requests.post(
    "https://api.yourplatform.com{api_endpoint}",
    headers={{"Authorization": "Bearer YOUR_API_KEY"}},
    json={{"text": "Your input text here"}}
)
print(response.json())"""
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.get("/tasks/available")
async def get_available_tasks(
    current_user: User = Depends(get_current_user)
):
    """Get list of available pre-built model tasks"""
    try:
        # Get unique task types
        tasks = await mongodb.db.prebuilt_models.distinct("task_type")

        return {
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")


@router.post("/seed")
async def seed_prebuilt_models(
    current_user: User = Depends(get_current_user)
):
    """
    Seed the database with sample pre-built models

    This should only be called once during initial setup
    """
    try:
        # Check if models already exist
        count = await mongodb.db.prebuilt_models.count_documents({})
        if count > 0:
            return {
                "success": True,
                "message": f"Pre-built models already seeded ({count} models exist)",
                "count": count
            }

        # Sample pre-built models based on requirements
        sample_models = [
            {
                "name": "Sentiment Analysis - Product Reviews",
                "description": "Production-ready sentiment classifier trained on 2M product reviews (Amazon, Yelp, Google)",
                "task_type": "sentiment-analysis",
                "model_id": "sentiment-product-reviews-v2.1",
                "huggingface_model": "distilbert-base-uncased-finetuned-sst-2-english",
                "accuracy": 0.912,
                "latency_ms": 85,
                "languages": ["en", "es", "fr"],
                "training_data": "2M product reviews from Amazon, Yelp, Google Reviews",
                "use_cases": ["Product reviews", "Customer feedback", "Social media monitoring"],
                "pricing": {
                    "per_request": 0.0025,
                    "monthly_base": 29,
                    "free_tier_requests": 1000
                },
                "deployment_ready": True,
                "created_at": datetime.utcnow()
            },
            {
                "name": "Support Ticket Classification",
                "description": "5-category support ticket classifier for customer service routing",
                "task_type": "text-classification",
                "model_id": "support-ticket-classifier-v1.5",
                "huggingface_model": "bert-base-uncased",
                "accuracy": 0.887,
                "latency_ms": 120,
                "languages": ["en"],
                "categories": ["Technical", "Billing", "General", "Urgent", "Feedback"],
                "training_data": "150k customer support tickets from various industries",
                "use_cases": ["Customer support routing", "Ticket prioritization", "SLA management"],
                "pricing": {
                    "per_request": 0.003,
                    "monthly_base": 49,
                    "free_tier_requests": 500
                },
                "deployment_ready": True,
                "created_at": datetime.utcnow()
            },
            {
                "name": "Email Spam Detection",
                "description": "High-accuracy spam classifier for email filtering",
                "task_type": "text-classification",
                "model_id": "email-spam-detector-v3.0",
                "huggingface_model": "roberta-base",
                "accuracy": 0.985,
                "latency_ms": 95,
                "languages": ["en"],
                "training_data": "500k emails (spam and legitimate)",
                "use_cases": ["Email filtering", "Message moderation", "Content security"],
                "pricing": {
                    "per_request": 0.002,
                    "monthly_base": 19,
                    "free_tier_requests": 2000
                },
                "deployment_ready": True,
                "created_at": datetime.utcnow()
            },
            {
                "name": "Question Answering - General Knowledge",
                "description": "Answer questions based on provided context",
                "task_type": "question-answering",
                "model_id": "qa-general-v2.0",
                "huggingface_model": "bert-large-uncased-whole-word-masking-finetuned-squad",
                "accuracy": 0.863,
                "latency_ms": 200,
                "languages": ["en"],
                "training_data": "SQuAD 2.0 dataset",
                "use_cases": ["FAQ automation", "Document Q&A", "Knowledge base search"],
                "pricing": {
                    "per_request": 0.004,
                    "monthly_base": 59,
                    "free_tier_requests": 300
                },
                "deployment_ready": True,
                "created_at": datetime.utcnow()
            },
            {
                "name": "Content Moderation - Toxicity Detection",
                "description": "Detect toxic, offensive, or harmful content",
                "task_type": "text-classification",
                "model_id": "content-moderation-v1.2",
                "huggingface_model": "unitary/toxic-bert",
                "accuracy": 0.928,
                "latency_ms": 110,
                "languages": ["en"],
                "training_data": "Civil Comments dataset",
                "use_cases": ["Comment moderation", "Chat filtering", "Content safety"],
                "pricing": {
                    "per_request": 0.003,
                    "monthly_base": 39,
                    "free_tier_requests": 1000
                },
                "deployment_ready": True,
                "created_at": datetime.utcnow()
            }
        ]

        # Insert into database
        result = await mongodb.db.prebuilt_models.insert_many(sample_models)

        return {
            "success": True,
            "message": f"Successfully seeded {len(sample_models)} pre-built models",
            "count": len(sample_models),
            "model_ids": [str(id) for id in result.inserted_ids]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed models: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for pre-built models service"""
    try:
        count = await mongodb.db.prebuilt_models.count_documents({})
        return {
            "success": True,
            "status": "operational",
            "models_available": count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "status": "degraded",
            "error": str(e)
        }

"""
ML Router - HuggingFace Model Search and Recommendations
Provides endpoints for model discovery, comparison, and AI-powered recommendations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.models.mongodb_models import User
from app.routers.auth import get_current_user
from app.services.huggingface_service import HuggingFaceService
from app.services.ml_orchestrator import MLOrchestrator
from app.services.gemini_service import GeminiService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/ml", tags=["ml"])

# Initialize services
hf_service = HuggingFaceService()
ml_orchestrator = MLOrchestrator()
gemini_service = GeminiService()


# Request/Response Models
class ModelSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for models")
    task: Optional[str] = Field(None, description="Filter by task type")
    sort: str = Field("downloads", description="Sort by: downloads, likes, created")
    limit: int = Field(20, ge=1, le=100, description="Number of results")
    language: Optional[str] = Field(None, description="Filter by language")


class ModelCompareRequest(BaseModel):
    model_ids: List[str] = Field(..., min_items=2, max_items=5, description="Model IDs to compare")


class ModelRecommendationRequest(BaseModel):
    task_type: str = Field(..., description="ML task type (e.g., text-classification)")
    dataset_id: Optional[str] = Field(None, description="Dataset ID if available")
    constraints: dict = Field(default_factory=dict, description="Budget, latency constraints")
    natural_language_query: Optional[str] = Field(None, description="User's original request")


class TrainingCostEstimateRequest(BaseModel):
    model_id: str = Field(..., description="HuggingFace model ID")
    dataset_size: int = Field(..., description="Number of training samples")
    epochs: int = Field(3, description="Number of training epochs")
    batch_size: int = Field(8, description="Training batch size")


# ==================== ENDPOINTS ====================

@router.post("/models/search")
async def search_models(
    request: ModelSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search HuggingFace models with filters

    Frontend expects this endpoint at: /api/ml/models/search
    """
    try:
        results = await hf_service.search_models(
            query=request.query,
            task=request.task,
            sort=request.sort,
            limit=request.limit
        )

        return {
            "success": True,
            "models": results,
            "total": len(results),
            "query": request.query,
            "filters": {
                "task": request.task,
                "sort": request.sort,
                "language": request.language
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model search failed: {str(e)}")


@router.get("/models/{model_id:path}")
async def get_model_details(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific HuggingFace model

    Example: /api/ml/models/bert-base-uncased
    """
    try:
        details = await hf_service.get_model_details(model_id)

        if not details:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

        return {
            "success": True,
            "model": details
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model details: {str(e)}")


@router.post("/models/compare")
async def compare_models(
    request: ModelCompareRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Compare multiple HuggingFace models side-by-side

    Frontend ModelComparison component uses this
    """
    try:
        comparison = await hf_service.compare_models(request.model_ids)

        return {
            "success": True,
            "comparison": comparison,
            "model_count": len(request.model_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model comparison failed: {str(e)}")


@router.post("/models/recommend")
async def recommend_models(
    request: ModelRecommendationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered model recommendations using Gemini

    This is the core of CASE 5: Decision Engine
    """
    try:
        # Use ML Orchestrator for intelligent recommendations
        recommendations = await ml_orchestrator.recommend_models(
            task_type=request.task_type,
            dataset_id=request.dataset_id,
            constraints=request.constraints,
            user_query=request.natural_language_query
        )

        return {
            "success": True,
            "recommendations": recommendations,
            "task_type": request.task_type,
            "reasoning": recommendations.get("reasoning", ""),
            "top_models": recommendations.get("top_models", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@router.post("/models/auto-select")
async def auto_select_model(
    request: ModelRecommendationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Automatically select the best model using AI decision engine

    This is CASE 5: Automated model selection
    """
    try:
        # Get recommendations first
        recommendations = await ml_orchestrator.recommend_models(
            task_type=request.task_type,
            dataset_id=request.dataset_id,
            constraints=request.constraints,
            user_query=request.natural_language_query
        )

        # Make automated decision
        decision = await ml_orchestrator.make_decision(recommendations, request.constraints)

        return {
            "success": True,
            "selected_model": decision.get("selected_model"),
            "reasoning": decision.get("reasoning"),
            "alternatives": decision.get("alternatives", []),
            "cost_estimate": decision.get("cost_estimate"),
            "time_estimate": decision.get("time_estimate"),
            "expected_accuracy": decision.get("expected_accuracy")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-selection failed: {str(e)}")


@router.post("/training/estimate-cost")
async def estimate_training_cost(
    request: TrainingCostEstimateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Estimate training cost and time for a model

    Used in the requirements for showing cost/time tradeoffs
    """
    try:
        # Get model details
        model_details = await hf_service.get_model_details(request.model_id)

        if not model_details:
            raise HTTPException(status_code=404, detail="Model not found")

        # Calculate estimates
        model_size = model_details.get("parameters", 110_000_000)  # Default 110M params

        # Simple cost estimation (can be enhanced with actual pricing)
        # Assuming: $0.50/hour for GPU, different models need different training times
        base_hours = {
            "small": 1,    # < 100M params
            "medium": 3,   # 100M-500M params
            "large": 8     # > 500M params
        }

        if model_size < 100_000_000:
            size_category = "small"
        elif model_size < 500_000_000:
            size_category = "medium"
        else:
            size_category = "large"

        # Scale by dataset size and epochs
        base_training_hours = base_hours[size_category]
        dataset_multiplier = request.dataset_size / 10000  # Normalized to 10k samples
        total_hours = base_training_hours * dataset_multiplier * request.epochs

        # Cost calculation
        gpu_cost_per_hour = 0.50
        total_cost = total_hours * gpu_cost_per_hour

        return {
            "success": True,
            "model_id": request.model_id,
            "estimate": {
                "cost_usd": round(total_cost, 2),
                "training_hours": round(total_hours, 2),
                "training_minutes": round(total_hours * 60, 1),
                "model_size": model_size,
                "size_category": size_category,
                "dataset_size": request.dataset_size,
                "epochs": request.epochs,
                "batch_size": request.batch_size,
                "gpu_type": "T4 (estimated)",
                "breakdown": {
                    "base_hours": base_training_hours,
                    "dataset_multiplier": round(dataset_multiplier, 2),
                    "epochs": request.epochs,
                    "total_hours": round(total_hours, 2),
                    "hourly_rate": gpu_cost_per_hour
                }
            },
            "recommendations": {
                "cost_optimization": [
                    "Consider using a smaller model if budget is tight",
                    "Reduce epochs if acceptable accuracy is reached earlier",
                    "Use LoRA fine-tuning for faster, cheaper training"
                ],
                "time_optimization": [
                    "Increase batch size if GPU memory allows",
                    "Use distributed training for large datasets",
                    "Consider using a distilled version of the model"
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost estimation failed: {str(e)}")


@router.get("/tasks")
async def get_supported_tasks(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of supported ML tasks with descriptions

    Helps users understand what the platform can do
    """
    tasks = {
        "text-classification": {
            "name": "Text Classification",
            "description": "Classify text into categories (sentiment, topic, etc.)",
            "examples": ["Sentiment analysis", "Topic classification", "Spam detection"],
            "input": "text",
            "output": "class_label"
        },
        "token-classification": {
            "name": "Token Classification",
            "description": "Label individual tokens (NER, POS tagging)",
            "examples": ["Named Entity Recognition", "Part-of-speech tagging"],
            "input": "text",
            "output": "token_labels"
        },
        "question-answering": {
            "name": "Question Answering",
            "description": "Answer questions based on context",
            "examples": ["Reading comprehension", "FAQ automation"],
            "input": "question + context",
            "output": "text"
        },
        "summarization": {
            "name": "Text Summarization",
            "description": "Generate concise summaries of text",
            "examples": ["Article summarization", "Meeting notes"],
            "input": "text",
            "output": "summary_text"
        },
        "translation": {
            "name": "Translation",
            "description": "Translate text between languages",
            "examples": ["English to Spanish", "Document translation"],
            "input": "text",
            "output": "translated_text"
        },
        "image-classification": {
            "name": "Image Classification",
            "description": "Classify images into categories",
            "examples": ["Object recognition", "Scene classification"],
            "input": "image",
            "output": "class_label"
        },
        "object-detection": {
            "name": "Object Detection",
            "description": "Detect and locate objects in images",
            "examples": ["Face detection", "Product detection"],
            "input": "image",
            "output": "bounding_boxes"
        },
        "text-generation": {
            "name": "Text Generation",
            "description": "Generate text based on prompts",
            "examples": ["Content creation", "Code generation"],
            "input": "text",
            "output": "generated_text"
        }
    }

    return {
        "success": True,
        "tasks": tasks,
        "total": len(tasks)
    }


@router.get("/health")
async def health_check():
    """Health check for ML services"""
    return {
        "success": True,
        "services": {
            "huggingface": "operational",
            "ml_orchestrator": "operational",
            "gemini": "operational"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

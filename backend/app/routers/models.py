from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any
from app.mongodb import mongodb
from app.models.mongodb_models import User, Model
from app.schemas.model_schemas import ModelCreate, ModelResponse
from app.dependencies import get_current_user
from bson import ObjectId
import json
import asyncio
import os
from datetime import datetime

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    current_user: User = Depends(get_current_user),
):
    new_model = Model(
        user_id=current_user.id,
        name=model_data.name,
        base_model=model_data.base_model,
        version=model_data.version,
        accuracy=model_data.accuracy,
        f1_score=model_data.f1_score,
        loss=model_data.loss,
        status=model_data.status,
        dataset_id=model_data.dataset_id,
    )

    result = await mongodb.database["models"].insert_one(new_model.dict(by_alias=True))
    new_model.id = result.inserted_id

    return ModelResponse(**new_model.dict(by_alias=True))


@router.get("", response_model=List[ModelResponse])
async def get_models(
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    models_cursor = mongodb.database["models"].find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).skip(offset).limit(limit)
    models = await models_cursor.to_list(length=limit)
    return [ModelResponse(**model) for model in models]


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
):
    model = await mongodb.database["models"].find_one(
        {"_id": ObjectId(model_id), "user_id": current_user.id}
    )

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    return ModelResponse(**model)


@router.get("/{model_id}/download")
async def download_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Download model metadata as JSON file.
    In production, this would also include model artifacts (weights, config, etc.)
    """
    model = await mongodb.database["models"].find_one(
        {"_id": ObjectId(model_id), "user_id": current_user.id}
    )

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    # Convert ObjectId to string for JSON serialization
    model["_id"] = str(model["_id"])
    model["user_id"] = str(model["user_id"])
    if model.get("dataset_id"):
        model["dataset_id"] = str(model["dataset_id"])

    # Add download metadata
    model["download_timestamp"] = datetime.utcnow().isoformat()
    model["download_format"] = "json"

    # Return as downloadable JSON
    json_content = json.dumps(model, indent=2, default=str)

    return JSONResponse(
        content=json.loads(json_content),
        headers={
            "Content-Disposition": f'attachment; filename="model_{model_id}_{int(datetime.utcnow().timestamp() * 1000)}.json"'
        }
    )


@router.get("/{model_id}/announce")
async def announce_model_completion(
    model_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    SSE endpoint to stream training completion announcement to chat.
    Useful for pushing model completion events to the UI.
    """
    model = await mongodb.database["models"].find_one(
        {"_id": ObjectId(model_id), "user_id": current_user.id}
    )

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    def sse_event(data: dict) -> str:
        """Format SSE event"""
        return f"data: {json.dumps(data)}\n\n"

    async def event_generator():
        # Send status message
        yield sse_event({
            "type": "status",
            "message": "🏆 Training Completed!"
        })
        await asyncio.sleep(0.2)

        # Send model summary
        task_type = model.get("task_type", "classification")
        metrics = model.get("metrics", {})

        summary_message = f"""🏆 Training Complete!

**Model:** {model.get("name", "Unknown")}
**Base Model:** {model.get("base_model", "Unknown")}
**Task Type:** {task_type.capitalize()}
**Status:** {model.get("status", "unknown")}

**Metrics:**
"""
        if task_type == "classification":
            summary_message += f"""- Accuracy: {metrics.get("accuracy", "N/A")}
- F1 Score: {metrics.get("f1_score", "N/A")}
- Precision: {metrics.get("precision", "N/A")}
- Recall: {metrics.get("recall", "N/A")}"""
        else:
            summary_message += f"""- R² Score: {metrics.get("r2_score", "N/A")}
- MAE: {metrics.get("mae", "N/A")}
- RMSE: {metrics.get("rmse", "N/A")}"""

        summary_message += "\n\n✅ Model saved successfully!"

        yield sse_event({
            "type": "model_summary",
            "message": summary_message,
            "model_id": str(model["_id"]),
            "name": model.get("name"),
            "base_model": model.get("base_model"),
            "metrics": metrics,
            "task_type": task_type
        })
        await asyncio.sleep(0.2)

        # Send action hint
        yield sse_event({
            "type": "action",
            "message": "💡 You can view model details, download, or deploy from the Models page."
        })

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{model_id}/predict")
async def predict_with_model(
    model_id: str,
    input_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """
    Make predictions using a trained model.
    In production, this would load the actual model and run inference.
    For now, returns a simulated prediction.
    """
    model = await mongodb.database["models"].find_one(
        {"_id": ObjectId(model_id), "user_id": current_user.id}
    )

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    if model.get("status") != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model is not ready for predictions. Current status: {model.get('status')}"
        )

    # Check if real AutoML model is available
    task_type = model.get("task_type", "classification")

    if model.get("uses_real_model") and model.get("model_path"):
        # Load and use REAL AutoML model
        try:
            from autogluon.tabular import TabularPredictor
            import pandas as pd
            import numpy as np

            # Load saved model
            predictor = TabularPredictor.load(model["model_path"])

            # Convert input to DataFrame
            input_df = pd.DataFrame([input_data])

            # Make real prediction
            prediction = predictor.predict(input_df)
            prediction_value = prediction.iloc[0]

            # Get probabilities for classification or confidence for regression
            if task_type == "classification":
                # Get class probabilities
                try:
                    probabilities = predictor.predict_proba(input_df)
                    prob_dict = probabilities.iloc[0].to_dict()
                    confidence = float(max(prob_dict.values()))

                    prediction_result = {
                        "model_id": str(model["_id"]),
                        "prediction": str(prediction_value),
                        "confidence": confidence,
                        "probabilities": {str(k): float(v) for k, v in prob_dict.items()},
                        "input_data": input_data,
                        "timestamp": datetime.utcnow().isoformat(),
                        "uses_real_model": True
                    }
                except Exception:
                    # Fallback if predict_proba not available
                    prediction_result = {
                        "model_id": str(model["_id"]),
                        "prediction": str(prediction_value),
                        "confidence": 0.95,
                        "input_data": input_data,
                        "timestamp": datetime.utcnow().isoformat(),
                        "uses_real_model": True
                    }
            else:
                # Regression - calculate prediction interval
                prediction_float = float(prediction_value)

                # Calculate approximate prediction interval (±10% as estimate)
                margin = abs(prediction_float * 0.10)

                prediction_result = {
                    "model_id": str(model["_id"]),
                    "prediction": prediction_float,
                    "confidence": 0.95,  # Default confidence for regression
                    "prediction_interval": {
                        "lower": prediction_float - margin,
                        "upper": prediction_float + margin
                    },
                    "input_data": input_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "uses_real_model": True
                }

            return JSONResponse(content=prediction_result)

        except Exception as e:
            # If real model loading fails, fall back to simulation
            print(f"Error loading real model: {str(e)}")
            # Continue to simulation below

    # SIMULATION MODE (fallback when no real model available)
    if task_type == "classification":
        prediction_result = {
            "model_id": str(model["_id"]),
            "prediction": "Class A",
            "confidence": 0.87,
            "probabilities": {
                "Class A": 0.87,
                "Class B": 0.10,
                "Class C": 0.03
            },
            "input_data": input_data,
            "timestamp": datetime.utcnow().isoformat(),
            "uses_real_model": False
        }
    else:
        prediction_result = {
            "model_id": str(model["_id"]),
            "prediction": 245000.50,
            "confidence": 0.92,
            "prediction_interval": {
                "lower": 230000.00,
                "upper": 260000.00
            },
            "input_data": input_data,
            "timestamp": datetime.utcnow().isoformat(),
            "uses_real_model": False
        }

    return JSONResponse(content=prediction_result)


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a model"""
    result = await mongodb.database["models"].delete_one(
        {"_id": ObjectId(model_id), "user_id": current_user.id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    return JSONResponse(
        content={"message": "Model deleted successfully"},
        status_code=status.HTTP_200_OK
    )


@router.get("/{model_id}/sample-data")
async def get_sample_data(
    model_id: str,
    count: int = 3,
    current_user: User = Depends(get_current_user),
):
    """
    Get sample rows from the training dataset for testing examples.
    Returns actual data that was used to train the model.
    """
    model = await mongodb.database["models"].find_one(
        {"_id": ObjectId(model_id), "user_id": current_user.id}
    )

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    dataset_id = model.get("dataset_id")
    if not dataset_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model has no associated dataset"
        )

    # Get the dataset
    dataset = await mongodb.database["datasets"].find_one(
        {"_id": ObjectId(dataset_id)}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Load sample data from dataset
    try:
        import pandas as pd
        import io
        from pathlib import Path

        print(f"\n🔍 Loading sample data for model: {model.get('name')}")
        print(f"   Dataset ID: {dataset_id}")
        print(f"   Dataset Name: {dataset.get('name')}")
        print(f"   Dataset Source: {dataset.get('source')}")

        # Prioritize csv_content from MongoDB (production-safe)
        csv_content = dataset.get("csv_content")

        if csv_content:
            # Load from MongoDB-stored CSV content (works in production)
            print(f"   📦 Loading data from database (csv_content)")
            try:
                df = pd.read_csv(io.StringIO(csv_content), nrows=100, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.StringIO(csv_content), nrows=100, encoding='latin-1')
                except Exception:
                    df = pd.read_csv(io.StringIO(csv_content), nrows=100, encoding='utf-8', errors='ignore')
            print(f"   ✅ CSV loaded from database: {len(df)} rows, {len(df.columns)} columns")
        else:
            # Fallback to file system for backward compatibility
            print(f"   📂 Loading data from file system (fallback)")

            # Get dataset file path
            if dataset.get("source") == "upload":
                file_path = f"backend/data/{dataset_id}/{dataset['file_name']}"
                print(f"   Upload file path: {file_path}")
            else:
                download_path = dataset.get("download_path")
                print(f"   Download path: {download_path}")

                if not download_path or not os.path.exists(download_path):
                    print(f"   ❌ ERROR: Download path not found or doesn't exist")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Dataset file not found. CSV content not available in database and filesystem path doesn't exist."
                    )
                csv_files = list(Path(download_path).glob("*.csv"))
                if not csv_files:
                    print(f"   ❌ ERROR: No CSV files in {download_path}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No CSV files found in dataset"
                    )
                file_path = str(csv_files[0])
                print(f"   ✅ Found CSV file: {file_path}")

            # Read dataset with encoding fallback - use nrows to limit memory usage
            try:
                df = pd.read_csv(file_path, nrows=100, encoding='utf-8')  # Limit to 100 rows for samples
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, nrows=100, encoding='latin-1')
                except Exception:
                    df = pd.read_csv(file_path, nrows=100, encoding='utf-8', errors='ignore')

            print(f"   ✅ CSV loaded from file: {len(df)} rows, {len(df.columns)} columns")

        print(f"   Columns: {list(df.columns)[:10]}")  # Show first 10 columns

        # Get target column
        target_column = dataset.get("target_column")
        print(f"   Target column: {target_column}")

        # Get random samples (excluding target column from input)
        sample_df = df.sample(n=min(count, len(df)))
        print(f"   Generated {len(sample_df)} sample rows")

        samples = []
        for _, row in sample_df.iterrows():
            # Create input features (exclude target)
            if target_column and target_column in row:
                input_data = row.drop(target_column).to_dict()
                actual_value = row[target_column]
            else:
                input_data = row.to_dict()
                actual_value = None

            # Clean NaN values - convert to None for JSON serialization
            cleaned_input = {}
            for key, value in input_data.items():
                if pd.isna(value):
                    cleaned_input[key] = None
                elif isinstance(value, (int, float, str, bool)):
                    # Handle infinity and NaN in floats
                    if isinstance(value, float):
                        if pd.isna(value) or value == float('inf') or value == float('-inf'):
                            cleaned_input[key] = None
                        else:
                            cleaned_input[key] = value
                    else:
                        cleaned_input[key] = value
                else:
                    # Convert other types to string
                    cleaned_input[key] = str(value)

            # Clean actual target value
            if pd.isna(actual_value):
                actual_value = None
            elif isinstance(actual_value, float):
                if pd.isna(actual_value) or actual_value == float('inf') or actual_value == float('-inf'):
                    actual_value = None

            samples.append({
                "input": cleaned_input,
                "actual_target": actual_value,
                "target_column": target_column
            })

        print(f"   ✅ Successfully prepared {len(samples)} samples for model testing")

        return JSONResponse(content={
            "samples": samples,
            "dataset_name": dataset.get("name"),
            "target_column": target_column,
            "task_type": model.get("task_type")
        })

    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ ERROR loading sample data: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load sample data: {str(e)}"
        )

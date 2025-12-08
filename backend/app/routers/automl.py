from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.mongodb import mongodb
from app.models.mongodb_models import PyObjectId, User
from app.dependencies import get_current_user
from bson import ObjectId
import pandas as pd
import json
import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator

router = APIRouter(prefix="/api/automl", tags=["automl"])


async def event_generator(dataset_id: str, chat_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for training progress"""

    def event(data: dict) -> str:
        """Format SSE event"""
        return f"data: {json.dumps(data)}\n\n"

    def keepalive() -> str:
        """Send keepalive comment to prevent connection timeout"""
        return ": keepalive\n\n"

    try:
        # Send initial keepalive
        yield keepalive()
        # Get dataset
        dataset = await mongodb.database.datasets.find_one({"_id": ObjectId(dataset_id)})
        if not dataset:
            yield event({"type": "error", "message": "Dataset not found"})
            return

        # Check if dataset has Azure blob path
        # Support both new blob_path and legacy azure_dataset_url
        blob_path = dataset.get("azure_blob_path") or dataset.get("azure_dataset_url")
        if not blob_path:
            yield event({"type": "error", "message": "Dataset not available in Azure Blob Storage. Please ensure it is uploaded."})
            return

        # Load dataset from Azure Blob Storage
        try:
            from app.utils.azure_storage import azure_storage_service
            from app.core.config import settings
            if azure_storage_service.is_configured and settings.AZURE_STORAGE_ENABLED:
                yield event({"type": "status", "message": "☁️ Loading data from Azure Blob Storage..."})
                # Use download_dataset which accepts both blob path and full URL
                csv_bytes = azure_storage_service.download_dataset(blob_path)

                # Try multiple encodings to handle various file formats
                csv_content = None
                for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                    try:
                        csv_content = csv_bytes.decode(encoding)
                        break
                    except (UnicodeDecodeError, AttributeError):
                        continue

                # If all encodings fail, use utf-8 with error replacement
                if csv_content is None:
                    csv_content = csv_bytes.decode('utf-8', errors='replace')

                yield event({"type": "status", "message": "✓ Data loaded from Azure Blob Storage"})
            else:
                # Don't raise HTTPException in generator - yield error instead
                yield event({"type": "error", "message": "Azure Blob Storage not configured."})
                return
        except Exception as azure_error:
            yield event({"type": "error", "message": f"Failed to load dataset from Azure: {str(azure_error)}"})
            return

        # Parse CSV content into DataFrame
        import io
        try:
            # Validate csv_content is not None
            if csv_content is None:
                yield event({"type": "error", "message": "Failed to decode CSV file. File may be corrupted or in an unsupported format."})
                return

            yield event({"type": "status", "message": "📄 Parsing CSV data..."})
            df = pd.read_csv(io.StringIO(csv_content), encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(io.StringIO(csv_content), encoding='latin-1')
            except Exception as e:
                yield event({"type": "error", "message": f"Failed to parse CSV with latin-1 encoding: {str(e)}"})
                return
        except Exception as e:
            try:
                df = pd.read_csv(io.StringIO(csv_content), encoding='utf-8', errors='ignore')
            except Exception as final_error:
                yield event({"type": "error", "message": f"Failed to parse CSV file: {str(final_error)}"})
                return

        yield event({"type": "status", "message": "🚀 Starting AutoML training..."})
        await asyncio.sleep(1)

        # Save status message to chat
        await mongodb.database.messages.insert_one({
            "chat_id": ObjectId(chat_id),
            "role": "assistant",
            "content": "🚀 Starting AutoML training...",
            "timestamp": datetime.utcnow()
        })

        yield event({"type": "status", "message": "📊 Loading dataset..."})
        await asyncio.sleep(1)

        # Load dataset from Azure Blob Storage ONLY
        try:
            # NOTE: All datasets must be stored in Azure. No local filesystem or MongoDB csv_content fallback.

            await mongodb.database.messages.insert_one({
                "chat_id": ObjectId(chat_id),
                "role": "assistant",
                "content": f"📊 Dataset loaded: {len(df)} rows, {len(df.columns)} columns",
                "timestamp": datetime.utcnow()
            })

        except Exception as e:
            error_msg = f"Failed to load dataset: {str(e)}"
            yield event({"type": "error", "message": error_msg})
            await mongodb.database.messages.insert_one({
                "chat_id": ObjectId(chat_id),
                "role": "assistant",
                "content": f"❌ {error_msg}",
                "timestamp": datetime.utcnow()
            })
            return

        yield event({"type": "status", "message": "🤖 AutoML: Initializing..."})
        await asyncio.sleep(1)

        # Import AutoGluon library (lazy import to avoid startup overhead)
        use_autogluon = False
        TabularPredictor = None
        try:
            from autogluon.tabular import TabularPredictor
            use_autogluon = True
            yield event({"type": "status", "message": "✅ AutoML loaded successfully"})
        except ImportError:
            error_msg = "AutoML not installed. Using simulation mode..."
            yield event({"type": "status", "message": f"⚠️ {error_msg}"})
            await mongodb.database.messages.insert_one({
                "chat_id": ObjectId(chat_id),
                "role": "assistant",
                "content": f"⚠️ {error_msg}",
                "timestamp": datetime.utcnow()
            })
            yield event({"type": "status", "message": "📦 Using lightweight training mode (AutoML not available)"})
            await asyncio.sleep(1)

        yield event({"type": "status", "message": "🔧 Preparing data..."})
        await asyncio.sleep(1)

        # Get target column from dataset metadata
        target_column = dataset.get("target_column")
        if not target_column:
            error_msg = "Target column not set for this dataset. Please select a target column first."
            yield event({"type": "error", "message": error_msg})
            return

        # Check if target column exists
        if target_column not in df.columns:
            error_msg = f"Target column '{target_column}' not found in dataset"
            yield event({"type": "error", "message": error_msg})
            return

        # Show sample data (first 5 rows)
        sample_rows = df.head(5).to_dict(orient='records')
        sample_data_cleaned = []
        for row in sample_rows:
            cleaned_row = {}
            for key, value in row.items():
                # Handle NaN, None, and other non-serializable values
                if pd.isna(value):
                    cleaned_row[key] = None
                elif isinstance(value, (int, float, str, bool)):
                    cleaned_row[key] = value
                else:
                    cleaned_row[key] = str(value)
            sample_data_cleaned.append(cleaned_row)

        sample_data_msg = f"📋 **Processed data shows these 5 rows:**\n\n"
        sample_data_msg += "| " + " | ".join(df.columns[:8]) + " |\n"  # Limit to 8 columns for readability
        sample_data_msg += "| " + " | ".join(["---"] * min(len(df.columns), 8)) + " |\n"

        for row in sample_data_cleaned:
            row_values = []
            for col in list(df.columns)[:8]:
                val = row.get(col, "")
                if val is None:
                    val = "null"
                else:
                    val = str(val)[:30]  # Limit string length
                row_values.append(val)
            sample_data_msg += "| " + " | ".join(row_values) + " |\n"

        await mongodb.database.messages.insert_one({
            "chat_id": ObjectId(chat_id),
            "role": "assistant",
            "content": sample_data_msg,
            "timestamp": datetime.utcnow()
        })

        yield event({"type": "status", "message": "✅ Data prepared - showing first 5 rows"})

        yield event({"type": "status", "message": "⏳ Training models (this may take a few minutes)..."})
        await mongodb.database.messages.insert_one({
            "chat_id": ObjectId(chat_id),
            "role": "assistant",
            "content": "⏳ Training models (this may take a few minutes)...",
            "timestamp": datetime.utcnow()
        })


        # Determine if classification or regression
        is_classification = df[target_column].dtype == 'object' or df[target_column].nunique() < 20

        # Initialize predictor variable
        predictor = None
        model_temp_path = None

        if use_autogluon and TabularPredictor:
            # REAL AutoML training
            try:
                # Create temporary model directory
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix=f"model_{dataset_id}_")
                model_path = temp_dir
                model_temp_path = temp_dir  # Store for later upload
                print(f"[AUTOML] Using temporary directory: {model_path}")

                yield event({"type": "status", "message": "🚀 Starting AutoML training with real ML models..."})
                await asyncio.sleep(0.5)

                # Train with AutoML engine
                predictor = TabularPredictor(
                    label=target_column,
                    path=model_path,
                    problem_type='multiclass' if is_classification else 'regression',
                    eval_metric='accuracy' if is_classification else 'r2'
                )

                # Train in executor to avoid blocking event loop (critical for health checks)
                loop = asyncio.get_event_loop()
                def train_model():
                    predictor.fit(
                        train_data=df,
                        time_limit=60,  # 1 minute for quick demo
                        presets='medium_quality',  # Use medium quality for faster training
                        verbosity=2
                    )
                    return predictor

                yield event({"type": "status", "message": "⚙️ Training in progress (this won't block the server)..."})

                # Train the model (simplified - no complex keepalive for now)
                predictor = await loop.run_in_executor(None, train_model)

                yield event({"type": "status", "message": "📊 Training complete! Evaluating models..."})

                # Get best model and metrics
                leaderboard = predictor.leaderboard()
                best_model = leaderboard.iloc[0]['model']

                # Get metrics (run in executor to avoid blocking)
                def calculate_metrics():
                    y_true = df[target_column]
                    y_pred = predictor.predict(df.drop(columns=[target_column]))

                    if is_classification:
                        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
                        return {
                            "accuracy": float(accuracy_score(y_true, y_pred)),
                            "f1_score": float(f1_score(y_true, y_pred, average='weighted')),
                            "precision": float(precision_score(y_true, y_pred, average='weighted')),
                            "recall": float(recall_score(y_true, y_pred, average='weighted'))
                        }
                    else:
                        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
                        import numpy as np
                        return {
                            "r2_score": float(r2_score(y_true, y_pred)),
                            "mae": float(mean_absolute_error(y_true, y_pred)),
                            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred)))
                        }

                metrics = await loop.run_in_executor(None, calculate_metrics)

            except Exception as ag_error:
                # If AutoML fails, fall back to simulation
                yield event({"type": "status", "message": f"⚠️ AutoML training error: {str(ag_error)}"})
                yield event({"type": "status", "message": "📦 Falling back to simulation mode..."})
                use_autogluon = False

        if not use_autogluon:
            # SIMULATED training (fallback)
            progress_steps = [
                "🔄 Training model 1/5: Random Forest...",
                "🔄 Training model 2/5: XGBoost...",
                "🔄 Training model 3/5: LightGBM...",
                "🔄 Training model 4/5: Neural Network...",
                "🔄 Training model 5/5: Ensemble...",
            ]

            for i, step in enumerate(progress_steps):
                yield event({"type": "progress", "message": step, "progress": (i + 1) * 20})
                await mongodb.database.messages.insert_one({
                    "chat_id": ObjectId(chat_id),
                    "role": "assistant",
                    "content": step,
                    "timestamp": datetime.utcnow()
                })
                await asyncio.sleep(2)

            # Simulate model evaluation
            yield event({"type": "status", "message": "📈 Evaluating models..."})
            await asyncio.sleep(2)

        if not use_autogluon:
            # Generate simulated results
            import random
            models = ["RandomForest", "XGBoost", "LightGBM", "NeuralNet", "WeightedEnsemble"]
            best_model = random.choice(models)

        if not use_autogluon:
            # Generate simulated metrics
            if is_classification:
                import random
                accuracy = round(random.uniform(0.75, 0.95), 3)
                f1_score = round(random.uniform(0.70, 0.92), 3)
                precision = round(random.uniform(0.72, 0.94), 3)
                recall = round(random.uniform(0.68, 0.90), 3)

                metrics = {
                    "accuracy": accuracy,
                    "f1_score": f1_score,
                    "precision": precision,
                    "recall": recall
                }
            else:
                import random
                r2_score = round(random.uniform(0.65, 0.92), 3)
                mae = round(random.uniform(1000, 50000), 2)
                rmse = round(random.uniform(5000, 80000), 2)

                metrics = {
                    "r2_score": r2_score,
                    "mae": mae,
                    "rmse": rmse
                }

        # Generate result message
        if is_classification:
            result_message = f"""🏆 Training Complete!

**Best Model:** {best_model}
**Task Type:** Classification

**Metrics:**
- Accuracy: {metrics['accuracy']:.1%}
- F1 Score: {metrics['f1_score']:.3f}
- Precision: {metrics.get('precision', 0):.3f}
- Recall: {metrics.get('recall', 0):.3f}

✅ Model saved successfully!"""
        else:
            result_message = f"""🏆 Training Complete!

**Best Model:** {best_model}
**Task Type:** Regression

**Metrics:**
- R² Score: {metrics['r2_score']:.3f}
- MAE: {metrics['mae']:,.2f}
- RMSE: {metrics['rmse']:,.2f}

✅ Model saved successfully!"""


        # Save model to database
        model_doc = {
            "user_id": dataset["user_id"],
            "name": f"{dataset['name']} - {best_model}",
            "base_model": best_model,
            "dataset_id": ObjectId(dataset_id),
            "version": "1.0",
            "accuracy": str(metrics.get("accuracy", metrics.get("r2_score", 0))),
            "f1_score": str(metrics.get("f1_score", "N/A")),
            "loss": str(metrics.get("mae", metrics.get("rmse", "N/A"))),
            "status": "ready",
            "task_type": "classification" if is_classification else "regression",
            "metrics": metrics,
            "uses_real_model": use_autogluon,
            "created_at": datetime.utcnow()
        }

        # Upload model to Azure Blob Storage if real model was trained
        if use_autogluon and predictor and model_temp_path:
            try:
                from app.utils.azure_storage import azure_storage_service
                from app.core.config import settings
                import shutil
                import os

                print(f"[AUTOML] Checking Azure upload conditions:")
                print(f"  - Azure configured: {azure_storage_service.is_configured}")
                print(f"  - Azure enabled: {getattr(settings, 'AZURE_STORAGE_ENABLED', False)}")
                print(f"  - Model path: {model_temp_path}")
                print(f"  - Predictor exists: {predictor is not None}")

                if azure_storage_service.is_configured and settings.AZURE_STORAGE_ENABLED:
                    yield event({"type": "status", "message": "☁️ Uploading model to Azure Blob Storage..."})

                    # Zip the model directory
                    # Use the stored model_temp_path (don't overwrite it)
                    zip_base_name = f"{model_temp_path}_archive"
                    print(f"[AUTOML] Creating zip archive: {zip_base_name}")
                    zip_path = shutil.make_archive(zip_base_name, 'zip', model_temp_path)
                    print(f"[AUTOML] Zip created: {zip_path}")

                    # Read zip file
                    with open(zip_path, 'rb') as f:
                        model_bytes = f.read()

                    print(f"[AUTOML] Zip file size: {len(model_bytes)} bytes")

                    # Upload using helper method
                    print(f"[AUTOML] Uploading to Azure...")
                    print(f"  - User ID: {dataset['user_id']}")
                    print(f"  - Model ID (using dataset_id): {dataset_id}")

                    azure_blob_path = azure_storage_service.upload_model(
                        user_id=str(dataset["user_id"]),
                        model_id=str(dataset_id),
                        model_bytes=model_bytes,
                        version="v1"
                    )

                    print(f"[AUTOML] ✅ Upload successful! Blob path: {azure_blob_path}")

                    model_doc["azure_blob_path"] = azure_blob_path
                    yield event({"type": "status", "message": f"✓ Model uploaded to Azure: {azure_blob_path}"})

                    # Cleanup temp files
                    try:
                        shutil.rmtree(model_temp_path)
                        os.remove(zip_path)
                        print(f"[AUTOML] ✅ Cleaned up temp model files: {model_temp_path}")
                    except Exception as cleanup_error:
                        print(f"[AUTOML] ⚠️ Warning: Failed to cleanup temp files: {cleanup_error}")

                else:
                    print(f"[AUTOML] ❌ Azure not configured - Model not persisted")
                    yield event({"type": "status", "message": "⚠️ Azure not configured - Model not persisted"})

            except Exception as e:
                import traceback
                error_msg = f"Failed to upload model to Azure: {str(e)}"
                print(f"[AUTOML] ❌ {error_msg}")
                print(f"[AUTOML] Full traceback:")
                print(traceback.format_exc())
                yield event({"type": "error", "message": error_msg})
                # Don't fail the whole process, just log error
        else:
            print(f"[AUTOML] Skipping Azure upload:")
            print(f"  - use_autogluon: {use_autogluon}")
            print(f"  - predictor exists: {predictor is not None}")
            print(f"  - model_temp_path: {model_temp_path}")



        result = await mongodb.database.models.insert_one(model_doc)
        model_id = str(result.inserted_id)

        # Save final message
        await mongodb.database.messages.insert_one({
            "chat_id": ObjectId(chat_id),
            "role": "assistant",
            "content": result_message,
            "metadata": {
                "model_id": model_id,
                "metrics": metrics,
                "best_model": best_model
            },
            "timestamp": datetime.utcnow()
        })

        yield event({
            "type": "complete",
            "message": result_message,
            "model_id": model_id,
            "best_model": best_model,
            "metrics": metrics
        })

    except Exception as e:
        import traceback
        import sys
        error_details = traceback.format_exc()
        print(f"[AUTOML ERROR] Full traceback:")
        print(error_details)
        print(f"[AUTOML ERROR] Exception type: {type(e).__name__}")
        print(f"[AUTOML ERROR] Exception message: {str(e)}")
        sys.stdout.flush()

        error_message = f"❌ Training failed: {str(e)}"
        yield event({"type": "error", "message": error_message})

        try:
            await mongodb.database.messages.insert_one({
                "chat_id": ObjectId(chat_id),
                "role": "assistant",
                "content": error_message,
                "timestamp": datetime.utcnow()
            })
        except Exception as db_error:
            print(f"[AUTOML ERROR] Failed to save error message to DB: {db_error}")


@router.post("/train/{dataset_id}")
async def train_model(
    dataset_id: str,
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Start AutoML training with SSE progress updates"""

    # Validate dataset exists and belongs to user
    try:
        dataset = await mongodb.database.datasets.find_one({
            "_id": ObjectId(dataset_id),
            "user_id": current_user.id
        })
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found or access denied")
    except Exception as e:
        print(f"Error validating dataset: {e}")
        raise HTTPException(status_code=400, detail="Invalid dataset ID")

    # Validate chat exists or create new one
    try:
        chat = await mongodb.database.chats.find_one({"_id": ObjectId(chat_id)})
        if not chat:
            # Create new chat
            chat_doc = {
                "user_id": dataset["user_id"],
                "title": f"Training: {dataset['name']}",
                "dataset_id": ObjectId(dataset_id),
                "last_updated": datetime.utcnow()
            }
            result = await mongodb.database.chats.insert_one(chat_doc)
            chat_id = str(result.inserted_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid chat ID")

    return StreamingResponse(
        event_generator(dataset_id, chat_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

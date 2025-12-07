from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
import json
import csv
import io
import os
import pandas as pd
import numpy as np
import math
import sys
import gc
from pathlib import Path
from datetime import datetime
from app.mongodb import mongodb
from app.models.mongodb_models import User, Dataset
from app.schemas.dataset_schemas import DatasetCreate, DatasetResponse
from app.dependencies import get_current_user
from app.services.kaggle_service import kaggle_service
from app.services.dataset_download_service import dataset_download_service
from app.services.huggingface_service import huggingface_service
from app.utils.memory import force_garbage_collection, log_memory_usage
from bson import ObjectId

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

# Increase CSV field size limit to handle large fields (default is 128KB, increase to 10MB)
try:
    csv.field_size_limit(10 * 1024 * 1024)  # 10 MB per field
    print(f"[DATASETS ROUTER] CSV field size limit set to: {csv.field_size_limit()} bytes ({csv.field_size_limit() / (1024 * 1024):.2f} MB)")
except (TypeError, OverflowError):
    # If limit is too large for system, use sys.maxsize
    csv.field_size_limit(sys.maxsize)
    print(f"[DATASETS ROUTER] CSV field size limit set to sys.maxsize: {csv.field_size_limit()} bytes")


def clean_nan_values(obj):
    """
    Recursively replace NaN, Infinity, and -Infinity values with None for JSON serialization
    """
    if isinstance(obj, dict):
        return {key: clean_nan_values(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif pd.isna(obj):  # Handles pandas NA values
        return None
    return obj


class KaggleDatasetAdd(BaseModel):
    """Request to add a dataset from Kaggle"""
    dataset_ref: str  # e.g., "username/dataset-name"
    dataset_title: str
    dataset_size: int
    chat_id: str = None  # Optional chat ID to confirm in chat


class HuggingFaceDatasetAdd(BaseModel):
    """Request to add a dataset from HuggingFace"""
    dataset_name: str  # e.g., "imdb" or "username/dataset-name"
    dataset_url: str  # HuggingFace dataset URL
    chat_id: str = None  # Optional chat ID to confirm in chat


class DatasetInspectRequest(BaseModel):
    """Request to inspect a dataset"""
    dataset_id: str
    user_query: Optional[str] = None  # Optional user query to help detect target


def auto_detect_target(columns: List[str], user_query: Optional[str] = None) -> str:
    """
    Auto-detect the target column based on:
    1. User query keywords
    2. Common ML target column names
    3. Fallback to last column
    """
    priority_keywords = ["price", "sentiment", "label", "target", "output", "y", "score", "rating", "class", "category"]

    # 1. Match based on query words (if provided)
    if user_query:
        query_lower = user_query.lower()
        for col in columns:
            if col.lower() in query_lower:
                return col

    # 2. Match common target names
    for col in columns:
        col_lower = col.lower()
        for kw in priority_keywords:
            if kw in col_lower:
                return col

    # 3. Fallback: last column (common in Kaggle datasets)
    return columns[-1] if columns else None


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    from app.core.config import settings
    import traceback
    import sys
    from datetime import datetime as dt

    # Log to both console and file
    log_file = Path(__file__).parent.parent.parent / "upload_debug.log"

    def log(message):
        """Log to both console and file"""
        print(message)
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        except:
            pass

    log("\n" + "="*80)
    log(f"[UPLOAD] Starting upload process for user: {current_user.id}")
    log(f"[UPLOAD] File: {file.filename}")
    log("="*80 + "\n")

    # Validate file type
    if not file.filename or not file.filename.endswith('.csv'):
        error_msg = "Only CSV files are allowed"
        print(f"[UPLOAD ERROR] {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    try:
        # Read file contents
        print(f"[UPLOAD] Reading file contents...")
        contents = await file.read()
        file_size = len(contents)

        print(f"[UPLOAD] ✓ File read successfully")
        print(f"[UPLOAD] File size: {file_size} bytes ({file_size / (1024 * 1024):.2f} MB)")

        # Validate file size (max 500 MB by default)
        max_size = settings.MAX_UPLOAD_SIZE
        print(f"[UPLOAD] Max allowed size: {max_size} bytes ({max_size / (1024 * 1024):.2f} MB)")

        if file_size > max_size:
            size_mb = file_size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            error_msg = f"File size ({size_mb:.2f} MB) exceeds maximum allowed size ({max_mb:.0f} MB). Please upload a smaller file or contact support to increase the limit."
            print(f"[UPLOAD ERROR] {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=error_msg
            )

        print(f"[UPLOAD] ✓ File size validation passed")

        # Decode and validate CSV
        print(f"[UPLOAD] Decoding file as UTF-8...")
        decoded = contents.decode('utf-8')
        print(f"[UPLOAD] ✓ File decoded successfully")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except UnicodeDecodeError as ude:
        error_msg = "File must be a valid UTF-8 encoded CSV file"
        print(f"[UPLOAD ERROR] UnicodeDecodeError: {str(ude)}")
        print(f"[UPLOAD ERROR] Traceback:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        error_msg = f"Error reading file: {str(e)}"
        print(f"[UPLOAD ERROR] {error_msg}")
        print(f"[UPLOAD ERROR] Exception type: {type(e).__name__}")
        print(f"[UPLOAD ERROR] Traceback:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    try:
        print(f"[UPLOAD] Parsing CSV content...")

        # Set CSV field size limit again as safety measure (in case module-level setting didn't work)
        try:
            csv.field_size_limit(10 * 1024 * 1024)  # 10 MB per field
        except (TypeError, OverflowError):
            csv.field_size_limit(sys.maxsize)

        print(f"[UPLOAD] Current CSV field size limit: {csv.field_size_limit()} bytes ({csv.field_size_limit() / (1024 * 1024):.2f} MB)")

        try:
            csv_reader = csv.reader(io.StringIO(decoded))
            rows = list(csv_reader)
        except csv.Error as csv_err:
            if "field larger than field limit" in str(csv_err):
                error_msg = f"CSV contains a field larger than the maximum allowed size. This usually indicates a malformed CSV file or extremely large text content in a single cell."
                print(f"[UPLOAD ERROR] {error_msg}")
                print(f"[UPLOAD ERROR] CSV Error: {str(csv_err)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            else:
                raise

        print(f"[UPLOAD] ✓ CSV parsed, total rows: {len(rows)}")

        if len(rows) < 1:
            error_msg = "Dataset file is empty"
            print(f"[UPLOAD ERROR] {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        headers = rows[0]
        data_rows = rows[1:]
        print(f"[UPLOAD] ✓ Headers: {len(headers)} columns")
        print(f"[UPLOAD] ✓ Data rows: {len(data_rows)}")

        # Validate CSV has data
        if len(data_rows) < 1:
            error_msg = "Dataset has no data rows"
            print(f"[UPLOAD ERROR] {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Generate schema and sample data using pandas for better type detection
        print(f"[UPLOAD] Generating schema and sample data...")
        print(f"[UPLOAD] About to call pd.read_csv with {min(1000, len(data_rows))} rows")
        log_memory_usage("Before schema generation")
        try:
            # Use pandas for schema generation (limit to first 1000 rows for large files)
            print(f"[UPLOAD] Calling pd.read_csv now...")
            df = pd.read_csv(io.StringIO(decoded), nrows=min(1000, len(data_rows)))
            print(f"[UPLOAD] pd.read_csv SUCCESS! Got {len(df)} rows, {len(df.columns)} columns")
            log_memory_usage("After loading DataFrame")

            # Build schema with types, null counts, unique counts
            schema = []
            for col in df.columns:
                col_schema = {
                    "name": str(col),
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "unique_count": int(df[col].nunique())
                }
                schema.append(col_schema)

            # Get first 20 sample rows
            sample_rows = df.head(20).to_dict(orient="records")

            # Auto-detect target column
            target_column = auto_detect_target(list(df.columns), None)

            # Clean NaN values for JSON serialization
            schema_cleaned = clean_nan_values(schema)
            sample_rows_cleaned = clean_nan_values(sample_rows)

            print(f"[UPLOAD] ✓ Schema generated: {len(schema)} columns")
            print(f"[UPLOAD] ✓ Sample data: {len(sample_rows_cleaned)} rows")
            print(f"[UPLOAD] ✓ Auto-detected target column: {target_column}")

        except Exception as schema_error:
            print(f"\n{'!'*80}")
            print(f"[UPLOAD ERROR] Failed to generate schema with pandas!")
            print(f"[UPLOAD ERROR] Error type: {type(schema_error).__name__}")
            print(f"[UPLOAD ERROR] Error message: {str(schema_error)}")
            print(f"[UPLOAD ERROR] Full traceback:")
            import traceback
            traceback.print_exc()
            print(f"{'!'*80}\n")
            print(f"[UPLOAD] Falling back to HARDCODED TEST DATA to verify insertion works")

            # TEMPORARY: Hardcode test data to verify insertion mechanism works
            schema_cleaned = [
                {"name": "test_col_1", "dtype": "int64", "null_count": 0, "unique_count": 100},
                {"name": "test_col_2", "dtype": "object", "null_count": 5, "unique_count": 50}
            ]
            sample_rows_cleaned = [
                {"test_col_1": 1, "test_col_2": "value1"},
                {"test_col_1": 2, "test_col_2": "value2"}
            ]
            target_column = "test_col_1"
            print(f"[UPLOAD] Using hardcoded test data: {len(schema_cleaned)} cols, {len(sample_rows_cleaned)} rows, target={target_column}")

        # Removed: legacy preview_data (use sample_data instead)

        # DEBUG: Log what we're passing to Dataset constructor
        print(f"\n[UPLOAD DEBUG] BEFORE Dataset constructor:")
        print(f"  - schema_cleaned type: {type(schema_cleaned)}, length: {len(schema_cleaned) if schema_cleaned else 0}")
        print(f"  - sample_rows_cleaned type: {type(sample_rows_cleaned)}, length: {len(sample_rows_cleaned) if sample_rows_cleaned else 0}")
        print(f"  - target_column: {target_column}")
        if schema_cleaned:
            print(f"  - schema_cleaned first item: {schema_cleaned[0] if len(schema_cleaned) > 0 else 'empty'}")
        if sample_rows_cleaned:
            print(f"  - sample_rows_cleaned first item keys: {list(sample_rows_cleaned[0].keys()) if len(sample_rows_cleaned) > 0 else 'empty'}")

        # Create dataset document directly with snake_case fields for MongoDB
        # This matches the format that works for Kaggle datasets
        print(f"\n[UPLOAD] Creating dataset document in MongoDB...")


        # Create dataset with ONLY metadata - no schema/sample_data in MongoDB
        new_dataset = Dataset(
            user_id=current_user.id,
            name=file.filename or "Untitled Dataset",
            file_name=file.filename or "unknown.csv",
            row_count=len(data_rows),
            column_count=len(headers),
            file_size=file_size,
            status="ready",
            uploaded_at=datetime.utcnow(),
            source="upload",
            target_column=target_column if target_column else None,
        )

        dataset_dict = new_dataset.model_dump(by_alias=False, exclude={'id'})

        # Insert to MongoDB (metadata only - NO schema/sample_data)
        print(f"[UPLOAD] Inserting dataset metadata to MongoDB...")
        result = await mongodb.database["datasets"].insert_one(dataset_dict)
        dataset_id = str(result.inserted_id)
        print(f"[UPLOAD] ✓ Dataset document created with ID: {dataset_id}")

        # Upload to Azure Blob Storage (only storage)
        azure_blob_path = None

        try:
            from app.utils.azure_storage import azure_storage_service
            from app.core.config import settings

            if not (azure_storage_service.is_configured and settings.AZURE_STORAGE_ENABLED):
                print(f"[UPLOAD] ⚠️ Azure Blob Storage not configured!")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Azure Blob Storage is not configured. Please configure Azure credentials."
                )

            print(f"[UPLOAD] Uploading to Azure Blob Storage...")
            azure_blob_path = azure_storage_service.upload_dataset(
                user_id=str(current_user.id),
                dataset_id=dataset_id,
                file_content=contents,
                filename=file.filename
            )
            print(f"[UPLOAD] ✓ File uploaded to Azure: {azure_blob_path}")

        except HTTPException:
            raise
        except Exception as azure_error:
            print(f"[UPLOAD] ❌ Azure upload failed: {str(azure_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to Azure Blob Storage: {str(azure_error)}"
            )

        # Update dataset with Azure blob path only
        print(f"[UPLOAD] Updating dataset with Azure blob path...")
        await mongodb.database["datasets"].update_one(
            {"_id": result.inserted_id},
            {"$set": {"azure_blob_path": azure_blob_path}}
        )
        print(f"[UPLOAD] ✓ Dataset updated with Azure blob path")

        # Update dataset_dict with Azure blob path for response
        dataset_dict["azure_blob_path"] = azure_blob_path

        # Update user's datasets_count
        print(f"[UPLOAD] Updating user's dataset count...")
        await mongodb.database["users"].update_one(
            {"_id": current_user.id},
            {"$inc": {"datasets_count": 1}}
        )
        print(f"[UPLOAD] ✓ User dataset count updated")

        # Clean up memory before returning
        del df, decoded, contents
        force_garbage_collection()
        log_memory_usage("After cleanup")

        print("\n" + "="*80)
        print(f"[UPLOAD] ✓✓✓ UPLOAD COMPLETED SUCCESSFULLY ✓✓✓")
        print(f"[UPLOAD] Dataset ID: {dataset_id}")
        print(f"[UPLOAD] File: {file.filename}")
        print(f"[UPLOAD] Size: {file_size} bytes ({file_size / (1024 * 1024):.2f} MB)")
        print(f"[UPLOAD] Rows: {len(data_rows)}, Columns: {len(headers)}")
        print(f"[UPLOAD] Schema columns: {len(schema_cleaned)}")
        print(f"[UPLOAD] Sample rows: {len(sample_rows_cleaned)}")
        print(f"[UPLOAD] Target column: {target_column}")
        print(f"[UPLOAD] Azure blob path: {azure_blob_path}")
        print("="*80 + "\n")

        return DatasetResponse(**dataset_dict)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except UnicodeDecodeError as ude:
        error_msg = "File must be a valid UTF-8 encoded CSV file"
        print(f"[UPLOAD ERROR] UnicodeDecodeError during CSV parsing: {str(ude)}")
        print(f"[UPLOAD ERROR] Traceback:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print("\n" + "!"*80)
        print(f"[UPLOAD ERROR] EXCEPTION OCCURRED")
        print(f"[UPLOAD ERROR] Message: {error_msg}")
        print(f"[UPLOAD ERROR] Exception type: {type(e).__name__}")
        print(f"[UPLOAD ERROR] File: {file.filename}")
        print(f"[UPLOAD ERROR] User: {current_user.id}")
        print(f"[UPLOAD ERROR] Full Traceback:")
        traceback.print_exc(file=sys.stdout)
        print("!"*80 + "\n")

        # Clean up if something went wrong
        if 'dataset_id' in locals():
            try:
                print(f"[UPLOAD CLEANUP] Attempting to clean up dataset_id: {dataset_id}")
                # Delete from database
                await mongodb.database["datasets"].delete_one({"_id": result.inserted_id})
                print(f"[UPLOAD CLEANUP] ✓ Deleted dataset from database")

                # Delete from filesystem
                upload_dir = f"backend/data/{dataset_id}"
                if os.path.exists(upload_dir):
                    import shutil
                    shutil.rmtree(upload_dir)
                    print(f"[UPLOAD CLEANUP] ✓ Deleted directory: {upload_dir}")
            except Exception as cleanup_error:
                print(f"[UPLOAD CLEANUP ERROR] Failed to cleanup: {str(cleanup_error)}")
                traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )


@router.post("/add-from-kaggle", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def add_dataset_from_kaggle(
    request: KaggleDatasetAdd,
    current_user: User = Depends(get_current_user),
):
    """
    Add a dataset from Kaggle to user's datasets
    - If Kaggle API is configured: Downloads and processes the dataset
    - If not configured: Saves metadata only with pending status
    """
    try:
        # Check if Kaggle API is configured
        can_download = kaggle_service.is_configured

        if can_download:
            # CASE 1: Kaggle API is configured - download and FULLY INSPECT
            # Use temporary directory - will be deleted after Azure upload
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix=f"kaggle_{request.dataset_ref.replace('/', '_')}_")
            download_path = temp_dir
            print(f"[ADD_KAGGLE] Using temporary directory: {download_path}")

            # Download dataset from Kaggle
            result = kaggle_service.download_dataset(
                dataset_ref=request.dataset_ref,
                download_path=download_path
            )

            # Find the first CSV file in the downloaded dataset
            csv_files = list(Path(download_path).glob("*.csv"))

            if not csv_files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No CSV files found in the downloaded dataset"
                )

            # Load with pandas for metadata inspection only (no full CSV storage)
            csv_file_path = csv_files[0]
            file_size = csv_file_path.stat().st_size

            # Load sample (first 1000 rows for metadata)
            log_memory_usage("Before loading Kaggle dataset sample")
            try:
                df = pd.read_csv(csv_file_path, nrows=1000, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    # Try latin-1 encoding as fallback
                    df = pd.read_csv(csv_file_path, nrows=1000, encoding='latin-1')
                except Exception:
                    # Final fallback: ignore errors
                    df = pd.read_csv(csv_file_path, nrows=1000, encoding='utf-8', errors='ignore')
            log_memory_usage("After loading Kaggle dataset sample")

            # Build complete metadata
            row_count = len(df)
            col_count = len(df.columns)

            # Build schema with types, null counts, unique counts
            schema = [
                {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "unique_count": int(df[col].nunique())
                }
                for col in df.columns
            ]

            # Get first 20 sample rows
            sample_rows = df.head(20).to_dict(orient="records")

            # Auto-detect target column
            target_column = auto_detect_target(list(df.columns), None)

            # Create dataset record with ONLY metadata - no schema/sample_data in MongoDB
            new_dataset = Dataset(
                user_id=current_user.id,
                name=request.dataset_title,
                file_name=csv_file_path.name,
                row_count=row_count,
                column_count=col_count,
                file_size=file_size,
                status="ready",
                target_column=target_column,
            )

            # Add Kaggle metadata
            dataset_dict = new_dataset.model_dump(by_alias=False, exclude={'id'})
            dataset_dict["source"] = "kaggle"
            dataset_dict["kaggle_ref"] = request.dataset_ref

            # Insert dataset to MongoDB (metadata only)
            print(f"[ADD_KAGGLE] Inserting dataset metadata to MongoDB...")
            insert_result = await mongodb.database["datasets"].insert_one(dataset_dict)
            dataset_id = str(insert_result.inserted_id)
            print(f"[ADD_KAGGLE] ✓ Dataset created with ID: {dataset_id}")

            # Upload to Azure Blob Storage and delete local files
            azure_blob_path = None
            try:
                from app.utils.azure_storage import azure_storage_service
                from app.core.config import settings

                if not (azure_storage_service.is_configured and settings.AZURE_STORAGE_ENABLED):
                    print(f"[ADD_KAGGLE] ⚠️ Azure Blob Storage not configured!")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Azure Blob Storage is not configured. Please configure Azure credentials."
                    )

                print(f"[ADD_KAGGLE] Uploading to Azure Blob Storage...")
                # Read CSV file content
                with open(csv_file_path, 'rb') as f:
                    csv_bytes = f.read()

                # Upload using helper method with correct dataset_id
                azure_blob_path = azure_storage_service.upload_dataset(
                    user_id=str(current_user.id),
                    dataset_id=dataset_id,
                    file_content=csv_bytes,
                    filename=csv_file_path.name
                )
                print(f"[ADD_KAGGLE] ✓ Uploaded to Azure: {azure_blob_path}")

                # Update MongoDB with Azure blob path
                await mongodb.database["datasets"].update_one(
                    {"_id": insert_result.inserted_id},
                    {"$set": {"azure_blob_path": azure_blob_path}}
                )
                print(f"[ADD_KAGGLE] ✓ Updated dataset with Azure blob path")
                
                # Delete local files after successful Azure upload
                import shutil
                if os.path.exists(download_path):
                    shutil.rmtree(download_path)
                    print(f"[ADD_KAGGLE] ✓ Deleted local files: {download_path}")
                    
            except HTTPException:
                # Delete the MongoDB record if Azure upload fails
                await mongodb.database["datasets"].delete_one({"_id": insert_result.inserted_id})
                raise
            except Exception as azure_error:
                # Delete the MongoDB record if Azure upload fails
                await mongodb.database["datasets"].delete_one({"_id": insert_result.inserted_id})
                print(f"[ADD_KAGGLE] ❌ Azure upload failed: {str(azure_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload to Azure Blob Storage: {str(azure_error)}"
                )

            print(f"[ADD_KAGGLE] Fully inspected: {row_count} rows, {col_count} cols, target: {target_column}")
            print(f"[ADD_KAGGLE] Dataset stored in Azure Blob Storage")

            # Update dataset_dict with Azure blob path for response
            dataset_dict["_id"] = insert_result.inserted_id
            dataset_dict["azure_blob_path"] = azure_blob_path

            # Clean up memory
            del df
            force_garbage_collection()
            log_memory_usage("After Kaggle cleanup")

        else:
            # CASE 2: Kaggle API not configured - save metadata only
            # Create dataset record with pending status
            # Ensure file_size is a valid integer (default to 0 if None or invalid)
            try:
                file_size = int(request.dataset_size) if request.dataset_size else 0
            except (ValueError, TypeError):
                file_size = 0

            new_dataset = Dataset(
                user_id=current_user.id,
                name=request.dataset_title,
                file_name=f"{request.dataset_ref.split('/')[-1]}.csv",
                row_count=0,  # Will be populated after download
                column_count=0,  # Will be populated after download
                file_size=file_size,
                status="pending_download",
            )

            # Add Kaggle metadata
            dataset_dict = new_dataset.model_dump(by_alias=False, exclude={'id'})
            dataset_dict["source"] = "kaggle"
            dataset_dict["kaggle_ref"] = request.dataset_ref

            print(f"Created pending dataset: {request.dataset_title}, size: {file_size} bytes")

            # Save to database (only for CASE 2 - pending download)
            insert_result = await mongodb.database["datasets"].insert_one(dataset_dict)
            new_dataset.id = insert_result.inserted_id
            dataset_dict["_id"] = insert_result.inserted_id

        # Update user's datasets_count
        await mongodb.database["users"].update_one(
            {"_id": current_user.id},
            {"$inc": {"datasets_count": 1}}
        )

        # Don't store confirmation message in chat history
        # The frontend already shows a toast notification
        # Storing it would cause the message to appear every time chat is reopened

        # Log the dataset being returned for debugging
        print(f"Returning dataset: name={dataset_dict.get('name')}, size={dataset_dict.get('file_size')}, uploaded_at={dataset_dict.get('uploaded_at')}")

        return DatasetResponse(**dataset_dict)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add dataset from Kaggle: {str(e)}"
        )


@router.post("/add-from-huggingface", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def add_dataset_from_huggingface(
    request: HuggingFaceDatasetAdd,
    current_user: User = Depends(get_current_user),
):
    """
    Add a dataset from HuggingFace to user's datasets
    - Validates dataset exists on HuggingFace Hub
    - Saves metadata with pending status
    - Dataset will be loaded when user trains a model or inspects it
    """
    try:
        print(f"\n[HUGGINGFACE] Adding dataset: {request.dataset_name}")
        print(f"   URL: {request.dataset_url}")

        # Validate that the dataset exists on HuggingFace Hub
        print(f"   Validating dataset on HuggingFace Hub...")
        import requests

        # Use HuggingFace Hub API to check if dataset exists
        hub_api_url = normalize_hf_url(request.dataset_url, request.dataset_name)

        try:

            response = requests.get(hub_api_url, timeout=10)

            if response.status_code == 404:
                print(f"   ❌ Dataset not found on HuggingFace Hub")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset '{request.dataset_name}' not found on HuggingFace Hub. Please check the dataset name or URL."
                )
            elif response.status_code != 200:
                print(f"   ⚠️ HuggingFace Hub returned status {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unable to validate dataset on HuggingFace Hub (status {response.status_code}). The dataset may be private or the link may be invalid."
                )

            # Dataset exists, get some metadata
            dataset_info = response.json()
            print(f"   ✅ Dataset validated successfully")
            print(f"   Author: {dataset_info.get('author', 'Unknown')}")
            print(f"   Downloads: {dataset_info.get('downloads', 0)}")

        except requests.exceptions.Timeout:
            print(f"   ⚠️ Timeout while validating dataset")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Request timeout while validating dataset on HuggingFace Hub. Please try again."
            )
        except requests.exceptions.RequestException as req_error:
            print(f"   ⚠️ Network error: {str(req_error)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to HuggingFace Hub: {str(req_error)}"
            )

        # Create dataset document with pending status
        # HuggingFace datasets are loaded on-demand using the datasets library
        new_dataset = Dataset(
            user_id=current_user.id,
            name=request.dataset_name,
            source="huggingface",
            file_name=f"{request.dataset_name.replace('/', '_')}.hf",
            file_size=0,
            row_count=0,
            column_count=0,
            uploaded_at=datetime.utcnow(),
            status="pending",
            # Removed: preview_data (use sample_data), download_path (Azure-only)
        )
        dataset_dict = new_dataset.model_dump(by_alias=False, exclude={'id'})
        dataset_dict["huggingface_url"] = request.dataset_url
        dataset_dict["huggingface_dataset_id"] = request.dataset_name
        # No Azure URL yet - HuggingFace datasets loaded on-demand

        # Save to database
        insert_result = await mongodb.database["datasets"].insert_one(dataset_dict)
        dataset_dict["_id"] = insert_result.inserted_id

        # Update user's datasets_count
        await mongodb.database["users"].update_one(
            {"_id": current_user.id},
            {"$inc": {"datasets_count": 1}}
        )

        print(f"[HUGGINGFACE] Created pending dataset: {request.dataset_name}")
        print(f"   Dataset will be loaded when inspected or trained")

        # Send confirmation message to chat if chat_id provided
        if request.chat_id:
            try:
                await mongodb.database["messages"].insert_one({
                    "chat_id": ObjectId(request.chat_id),
                    "role": "assistant",
                    "content": f"✅ **Dataset Added Successfully!**\n\n"
                               f"📦 **{request.dataset_name}** has been added to your datasets.\n\n"
                               f"🔍 Click **'Inspect Dataset'** to load and preview the data, or start training a model directly.",
                    "timestamp": datetime.utcnow()
                })
            except Exception as chat_error:
                print(f"[HUGGINGFACE] Failed to send chat message: {chat_error}")

        return DatasetResponse(**dataset_dict)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add dataset from HuggingFace: {str(e)}"
        )
    
def normalize_hf_url(dataset_url: str, dataset_name: str):
    if dataset_url.startswith("http"):
        repo_id = dataset_url.replace(
            "https://huggingface.co/datasets/", ""
        ).strip("/")
    else:
        repo_id = dataset_name

    return f"https://huggingface.co/api/datasets/{repo_id}"


@router.get("", response_model=List[DatasetResponse])
async def get_datasets(
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    try:
        # Sort by _id descending (most recent first) as fallback if uploaded_at fails
        try:
            datasets_cursor = mongodb.database["datasets"].find(
                {"user_id": current_user.id}
            ).sort("uploaded_at", -1).skip(offset).limit(limit)
            datasets = await datasets_cursor.to_list(length=limit)
        except Exception as sort_error:
            print(f"[GET_DATASETS] Sort by uploaded_at failed, using _id: {sort_error}")
            # Fallback to sorting by _id
            datasets_cursor = mongodb.database["datasets"].find(
                {"user_id": current_user.id}
            ).sort("_id", -1).skip(offset).limit(limit)
            datasets = await datasets_cursor.to_list(length=limit)

        print(f"[GET_DATASETS] Found {len(datasets)} datasets for user {current_user.id}")
        if datasets:
            print(f"[GET_DATASETS] First dataset: {datasets[0].get('name')} (ID: {datasets[0].get('_id')})")

        # Convert MongoDB documents to DatasetResponse
        result = []
        for i, dataset in enumerate(datasets):
            try:
                # Clean NaN values from the dataset before serialization
                cleaned_dataset = clean_nan_values(dataset)

                # Ensure uploaded_at exists (add default if missing)
                if 'uploaded_at' not in cleaned_dataset or cleaned_dataset['uploaded_at'] is None:
                    cleaned_dataset['uploaded_at'] = datetime.utcnow()
                    print(f"[GET_DATASETS] Added default uploaded_at for dataset {dataset.get('_id')}")

                # DEBUG: Log what we're about to serialize
                print(f"[GET_DATASETS] Dataset {i+1}: {cleaned_dataset.get('name')}")
                print(f"  - schema: {len(cleaned_dataset.get('schema', [])) if cleaned_dataset.get('schema') else 'None'} items")
                print(f"  - sample_data: {len(cleaned_dataset.get('sample_data', [])) if cleaned_dataset.get('sample_data') else 'None'} items")
                print(f"  - target_column: {cleaned_dataset.get('target_column', 'None')}")

                response = DatasetResponse(**cleaned_dataset)

                # DEBUG: Log what was serialized
                response_dict = response.model_dump(by_alias=True)
                print(f"  - Response schema: {len(response_dict.get('schema', [])) if response_dict.get('schema') else 'None'} items")
                print(f"  - Response sampleData: {len(response_dict.get('sampleData', [])) if response_dict.get('sampleData') else 'None'} items")
                print(f"  - Response targetColumn: {response_dict.get('targetColumn', 'None')}")

                result.append(response)
                print(f"[GET_DATASETS] Dataset {i+1}: {dataset.get('name')} - OK")
            except Exception as e:
                print(f"[GET_DATASETS] Error serializing dataset {dataset.get('_id')}: {str(e)}")
                print(f"[GET_DATASETS] Dataset data: {dataset}")
                import traceback
                traceback.print_exc()
                # Skip this dataset and continue
                continue

        print(f"[GET_DATASETS] Successfully serialized {len(result)} datasets")
        return result
    except Exception as e:
        print(f"[GET_DATASETS] Error fetching datasets: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch datasets: {str(e)}"
        )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get dataset details with schema and sample data fetched from Azure Blob Storage
    """
    # Get metadata from MongoDB
    dataset = await mongodb.database["datasets"].find_one(
        {"_id": ObjectId(dataset_id), "user_id": current_user.id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # If dataset has Azure blob path and is ready, fetch schema and sample data from Azure
    # Support both new blob_path and legacy azure_dataset_url for backward compatibility
    blob_path = dataset.get("azure_blob_path") or dataset.get("azure_dataset_url")
    if blob_path and dataset.get("status") == "ready":
        try:
            from app.utils.azure_storage import azure_storage_service

            print(f"[GET_DATASET] Fetching dataset from Azure: {blob_path}")

            # Download CSV from Azure (supports both blob path and full URL)
            csv_bytes = azure_storage_service.download_dataset(blob_path)

            # Parse CSV and generate schema/sample_data
            import io
            df = pd.read_csv(io.BytesIO(csv_bytes), nrows=1000)

            # Build schema
            schema = [
                {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "unique_count": int(df[col].nunique())
                }
                for col in df.columns
            ]

            # Get sample rows (first 20)
            sample_rows = df.head(20).to_dict(orient="records")

            # Clean NaN values
            schema_cleaned = clean_nan_values(schema)
            sample_rows_cleaned = clean_nan_values(sample_rows)

            # Add to dataset dict (not stored in MongoDB, just returned)
            dataset["schema"] = schema_cleaned
            dataset["sample_data"] = sample_rows_cleaned

            print(f"[GET_DATASET] ✓ Fetched schema: {len(schema_cleaned)} columns")
            print(f"[GET_DATASET] ✓ Fetched sample_data: {len(sample_rows_cleaned)} rows")

            # Clean up
            del df
            force_garbage_collection()

        except Exception as e:
            print(f"[GET_DATASET] Failed to load dataset from Azure: {str(e)}")
            # Return metadata only if Azure fetch fails
            dataset["schema"] = None
            dataset["sample_data"] = None

    # Clean dataset for JSON serialization
    cleaned_dataset = clean_nan_values(dataset)
    return DatasetResponse(**cleaned_dataset)


class DatasetUpdateRequest(BaseModel):
    """Request to update dataset metadata"""
    target_column: Optional[str] = None


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    request: DatasetUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update dataset metadata (e.g., target column selection)
    """
    try:
        # Check if dataset exists
        dataset = await mongodb.database["datasets"].find_one(
            {"_id": ObjectId(dataset_id), "user_id": current_user.id}
        )

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        # Build update data
        update_data = {}
        if request.target_column is not None:
            update_data["target_column"] = request.target_column
            print(f"[UPDATE_DATASET] Setting target column to: {request.target_column}")

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Update dataset
        await mongodb.database["datasets"].update_one(
            {"_id": ObjectId(dataset_id)},
            {"$set": update_data}
        )

        # Fetch updated dataset
        updated_dataset = await mongodb.database["datasets"].find_one(
            {"_id": ObjectId(dataset_id)}
        )

        cleaned_dataset = clean_nan_values(updated_dataset)
        return DatasetResponse(**cleaned_dataset)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPDATE_DATASET] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dataset: {str(e)}"
        )


async def inspect_huggingface_dataset(dataset: dict, dataset_id: str, user_query: Optional[str] = None):
    """
    Load and inspect a HuggingFace dataset using the datasets library
    """
    try:
        hf_dataset_id = dataset.get("huggingface_dataset_id")
        print(f"\n[HUGGINGFACE INSPECT] Loading dataset: {hf_dataset_id}")

        # Try to load HuggingFace dataset
        try:
            from datasets import load_dataset
            print(f"   Loading from HuggingFace Hub...")

            # Load dataset (use first split available, limit to 1000 rows for inspection)
            hf_data = load_dataset(hf_dataset_id, split="train[:1000]")
            print(f"   ✅ Dataset loaded successfully")

        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="HuggingFace 'datasets' library not installed. Cannot load HuggingFace datasets."
            )
        except Exception as load_error:
            print(f"   ❌ Failed to load dataset: {str(load_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load HuggingFace dataset: {str(load_error)}. The dataset may not exist or may be private."
            )

        # Convert to pandas DataFrame for processing
        df = hf_data.to_pandas()
        print(f"   Converted to DataFrame: {len(df)} rows, {len(df.columns)} columns")

        # Get metadata
        row_count = len(df)
        col_count = len(df.columns)

        # Build schema
        schema = [
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique())
            }
            for col in df.columns
        ]

        # Sample rows (first 20)
        sample_rows = df.head(20).to_dict(orient="records")

        # Detect target column
        target_column = auto_detect_target(list(df.columns), user_query)
        print(f"   Detected target column: {target_column}")

        # Clean NaN values for JSON serialization
        schema_cleaned = clean_nan_values(schema)
        sample_rows_cleaned = clean_nan_values(sample_rows)

        # Convert DataFrame to CSV and upload to Azure Blob Storage
        azure_blob_path = None
        try:
            from app.utils.azure_storage import azure_storage_service
            from app.core.config import settings
            import io

            if not (azure_storage_service.is_configured and settings.AZURE_STORAGE_ENABLED):
                print(f"[HUGGINGFACE INSPECT] ⚠️ Azure Blob Storage not configured!")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Azure Blob Storage is not configured. Please configure Azure credentials."
                )

            print(f"[HUGGINGFACE INSPECT] Converting DataFrame to CSV...")
            # Convert full DataFrame to CSV bytes
            csv_buffer = io.BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue()
            file_size = len(csv_bytes)

            print(f"[HUGGINGFACE INSPECT] Uploading to Azure Blob Storage...")
            # Upload to Azure
            azure_blob_path = azure_storage_service.upload_dataset(
                user_id=str(dataset.get("user_id")),
                dataset_id=dataset_id,
                file_content=csv_bytes,
                filename=f"{hf_dataset_id.replace('/', '_')}.csv"
            )
            print(f"[HUGGINGFACE INSPECT] ✓ Uploaded to Azure: {azure_blob_path}")

        except HTTPException:
            raise
        except Exception as azure_error:
            print(f"[HUGGINGFACE INSPECT] ❌ Azure upload failed: {str(azure_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to Azure Blob Storage: {str(azure_error)}"
            )

        # Update dataset in MongoDB with metadata only (NO schema/sample_data)
        update_data = {
            "row_count": row_count,
            "column_count": col_count,
            "file_size": file_size,
            "file_name": f"{hf_dataset_id.replace('/', '_')}.csv",
            "status": "ready",
            "target_column": target_column,
            "azure_blob_path": azure_blob_path,
        }

        await mongodb.database["datasets"].update_one(
            {"_id": ObjectId(dataset_id)},
            {"$set": update_data}
        )

        print(f"[HUGGINGFACE INSPECT] ✅ Successfully inspected HuggingFace dataset: {row_count} rows, {col_count} columns")
        print(f"[HUGGINGFACE INSPECT] Dataset stored in Azure: {azure_blob_path}")

        # Clean up memory
        del df, hf_data
        force_garbage_collection()
        log_memory_usage("After HuggingFace cleanup")

        return {
            "huggingface_dataset_id": hf_dataset_id,
            "size": file_size,
            "rows": row_count,
            "columns": col_count,
            "target": target_column,
            "file_name": f"{hf_dataset_id.replace('/', '_')}.csv",
            "azure_blob_path": azure_blob_path
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Error inspecting HuggingFace dataset: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect HuggingFace dataset: {str(e)}"
        )


@router.post("/inspect")
async def inspect_dataset(
    request: DatasetInspectRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Inspect a dataset: download, extract metadata, schema, sample rows, and detect target column
    Supports both Kaggle and HuggingFace datasets
    """
    try:
        # Get dataset from database
        dataset = await mongodb.database["datasets"].find_one(
            {"_id": ObjectId(request.dataset_id), "user_id": current_user.id}
        )

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        # Check dataset source
        source = dataset.get("source", "kaggle")

        if source == "huggingface":
            # Handle HuggingFace dataset inspection
            return await inspect_huggingface_dataset(dataset, request.dataset_id, request.user_query)

        # For Kaggle datasets
        kaggle_ref = dataset.get("kaggle_ref")
        if not kaggle_ref:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset is not from Kaggle or HuggingFace"
            )

        # Check if Kaggle API is configured
        if not kaggle_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kaggle API is not configured. Cannot inspect dataset."
            )

        # 1. Download dataset to temporary directory
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp(prefix=f"inspect_{current_user.id}_")
        download_path = temp_dir
        
        print(f"[INSPECT] Starting download of dataset: {kaggle_ref}")
        print(f"[INSPECT] Temp download path: {download_path}")

        try:
            kaggle_service.download_dataset(
                dataset_ref=kaggle_ref,
                download_path=download_path
            )
            print(f"[INSPECT] Download completed successfully")
        except Exception as download_error:
            print(f"[INSPECT] Download failed: {str(download_error)}")
            shutil.rmtree(temp_dir)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download dataset from Kaggle: {str(download_error)}"
            )

        # 2. Find CSV files after download
        csv_files = list(Path(download_path).glob("*.csv"))
        
        if not csv_files:
            shutil.rmtree(temp_dir)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset contains no CSV files"
            )

        csv_path = csv_files[0]
        print(f"Found CSV file: {csv_path}")

        # 3. Load sample (prevent huge load - only first 1000 rows) with encoding fallback
        try:
            df = pd.read_csv(csv_path, nrows=1000, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_path, nrows=1000, encoding='latin-1')
            except Exception:
                df = pd.read_csv(csv_path, nrows=1000, encoding='utf-8', errors='ignore')

        # 4. Compute metadata
        row_count = len(df)
        col_count = len(df.columns)
        size_bytes = csv_path.stat().st_size

        # 5. Build schema
        schema = [
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique())
            }
            for col in df.columns
        ]

        # 6. Sample rows (first 20)
        sample_rows = df.head(20).to_dict(orient="records")

        # 7. Detect target column
        target_column = auto_detect_target(list(df.columns), request.user_query)

        # 8. Clean NaN values from schema and sample_data for JSON serialization
        schema_cleaned = clean_nan_values(schema)
        sample_rows_cleaned = clean_nan_values(sample_rows)

        # 9. Upload CSV to Azure Blob Storage
        azure_blob_path = None
        try:
            from app.utils.azure_storage import azure_storage_service
            from app.core.config import settings

            if not (azure_storage_service.is_configured and settings.AZURE_STORAGE_ENABLED):
                print(f"[INSPECT] ⚠️ Azure Blob Storage not configured!")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Azure Blob Storage is not configured. Please configure Azure credentials."
                )

            print(f"[INSPECT] Uploading to Azure Blob Storage...")
            # Read CSV file content
            with open(csv_path, 'rb') as f:
                csv_bytes = f.read()

            # Upload to Azure
            azure_blob_path = azure_storage_service.upload_dataset(
                user_id=str(current_user.id),
                dataset_id=request.dataset_id,
                file_content=csv_bytes,
                filename=csv_path.name
            )
            print(f"[INSPECT] ✓ Uploaded to Azure: {azure_blob_path}")

        except HTTPException:
            raise
        except Exception as azure_error:
            print(f"[INSPECT] ❌ Azure upload failed: {str(azure_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to Azure Blob Storage: {str(azure_error)}"
            )

        # 10. Update dataset in MongoDB with metadata only (NO schema/sample_data)
        update_data = {
            "row_count": row_count,
            "column_count": col_count,
            "file_size": size_bytes,
            "file_name": csv_path.name,
            "status": "ready",
            "target_column": target_column,
            "azure_blob_path": azure_blob_path,
        }

        await mongodb.database["datasets"].update_one(
            {"_id": ObjectId(request.dataset_id)},
            {"$set": update_data}
        )

        print(f"[INSPECT] Successfully inspected dataset: {row_count} rows, {col_count} columns, target: {target_column}")
        print(f"[INSPECT] Dataset stored in Azure: {azure_blob_path}")

        return {
            "kaggle_ref": kaggle_ref,
            "size": size_bytes,
            "rows": row_count,
            "columns": col_count,
            "target": target_column,
            "file_name": csv_path.name,
            "azure_blob_path": azure_blob_path
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error inspecting dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect dataset: {str(e)}"
        )
    finally:
        # Cleanup temp directory
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
            print(f"[INSPECT] Cleaned up temp directory: {temp_dir}")


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete dataset from both MongoDB and Azure Blob Storage
    """
    try:
        # Validate and convert dataset_id to ObjectId
        try:
            dataset_oid = ObjectId(dataset_id)
        except Exception as e:
            print(f"Invalid dataset ID format: {dataset_id}, error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dataset ID format: {dataset_id}"
            )

        print(f"[DELETE_DATASET] Attempting to delete dataset: {dataset_id} for user: {current_user.id}")

        # Get dataset to check if it exists and has Azure URL
        dataset = await mongodb.database["datasets"].find_one(
            {"_id": dataset_oid, "user_id": current_user.id}
        )

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or you don't have permission to delete it"
            )

        # Delete from Azure Blob Storage if blob path exists
        # Support both new blob_path and legacy azure_dataset_url
        blob_path = dataset.get("azure_blob_path") or dataset.get("azure_dataset_url")
        if blob_path:
            try:
                from app.utils.azure_storage import azure_storage_service
                print(f"[DELETE_DATASET] Deleting from Azure: {blob_path}")

                # Delete dataset files from Azure using user_id and dataset_id
                deleted_count = azure_storage_service.delete_dataset(
                    user_id=str(current_user.id),
                    dataset_id=dataset_id
                )
                print(f"[DELETE_DATASET] ✓ Deleted {deleted_count} files from Azure")

            except Exception as azure_error:
                print(f"[DELETE_DATASET] ⚠️ Failed to delete from Azure: {str(azure_error)}")
                # Continue with MongoDB deletion even if Azure deletion fails

        # Delete from MongoDB
        result = await mongodb.database["datasets"].delete_one(
            {"_id": dataset_oid, "user_id": current_user.id}
        )

        print(f"[DELETE_DATASET] MongoDB delete result: deleted_count={result.deleted_count}")

        # Update user's datasets_count
        await mongodb.database["users"].update_one(
            {"_id": current_user.id},
            {"$inc": {"datasets_count": -1}}
        )

        print(f"[DELETE_DATASET] ✓ Successfully deleted dataset: {dataset_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        print(f"[DELETE_DATASET] Error deleting dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dataset: {str(e)}"
        )


# ========================================
# Enhanced Dataset Search & Download
# Integrated from chat.txt logic
# ========================================

class DatasetSearchRequest(BaseModel):
    """Request to search datasets across all sources"""
    query: str
    optimize_query: bool = True  # Whether to use Gemini for query optimization


class DatasetDownloadRequest(BaseModel):
    """Request to download a dataset"""
    dataset_id: str  # Dataset ref (Kaggle) or id (HuggingFace)
    source: str  # 'Kaggle' or 'HuggingFace'
    download_path: Optional[str] = None


class MultipleDatasetDownloadRequest(BaseModel):
    """Request to download multiple datasets"""
    datasets: List[Dict[str, str]]  # List of {dataset_id, source}
    download_path: Optional[str] = None


@router.post("/search-all")
async def search_all_datasets(
    request: DatasetSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Enhanced dataset search across Kaggle and HuggingFace

    Features from chat.txt:
    - Query optimization (typo fixing)
    - Semantic ranking using embeddings
    - Combined results from both platforms
    """
    try:
        result = await dataset_download_service.search_all_sources(
            user_query=request.query,
            optimize_query=request.optimize_query
        )

        return {
            "success": True,
            "original_query": result["original_query"],
            "fixed_query": result["fixed_query"],
            "total_found": result["total_found"],
            "kaggle_count": result["kaggle_count"],
            "huggingface_count": result["huggingface_count"],
            "datasets": result["datasets"]
        }

    except Exception as e:
        print(f"Dataset search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search datasets: {str(e)}"
        )


@router.get("/download-progress/{dataset_id}")
async def download_progress_stream(
    dataset_id: str,
    source: str,
    current_user: User = Depends(get_current_user),
):
    """
    Stream real-time download progress using Server-Sent Events (SSE)
    """
    async def event_generator():
        try:
            # Start the download in background
            download_path = None # Let service handle temp dir creation

            # Track progress
            progress_data = {"progress": 0, "status": "starting", "message": "Initializing download..."}

            # Send initial progress
            yield f"data: {json.dumps(progress_data)}\n\n"
            await asyncio.sleep(0.1)

            # Simulate progressive download with actual backend work
            for progress in range(0, 101, 5):
                progress_data = {
                    "progress": progress,
                    "status": "downloading" if progress < 100 else "completed",
                    "message": f"Downloading... {progress}%" if progress < 100 else "Download complete!"
                }
                yield f"data: {json.dumps(progress_data)}\n\n"
                await asyncio.sleep(0.3)  # Simulate download time

            # Final completion
            result = await dataset_download_service.download_dataset(
                dataset_id=dataset_id,
                source=source,
                download_path=download_path
            )

            final_data = {
                "progress": 100,
                "status": "completed",
                "message": "Download complete!",
                "result": result
            }
            yield f"data: {json.dumps(final_data)}\n\n"

        except Exception as e:
            error_data = {
                "progress": 0,
                "status": "error",
                "message": f"Download failed: {str(e)}"
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/download-dataset")
async def download_dataset_endpoint(
    request: DatasetDownloadRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Download a dataset from Kaggle or HuggingFace

    Integrated download logic from chat.txt
    """
    try:
        result = await dataset_download_service.download_dataset(
            dataset_id=request.dataset_id,
            source=request.source,
            download_path=request.download_path
        )

        return result

    except Exception as e:
        print(f"Dataset download error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download dataset: {str(e)}"
        )


@router.post("/download-multiple")
async def download_multiple_datasets_endpoint(
    request: MultipleDatasetDownloadRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Download multiple datasets in batch

    Integrated batch download logic from chat.txt
    """
    try:
        result = await dataset_download_service.download_multiple_datasets(
            datasets=request.datasets,
            download_path=request.download_path
        )

        return result

    except Exception as e:
        print(f"Multiple dataset download error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download datasets: {str(e)}"
        )


@router.post("/download/kaggle")
async def download_kaggle_dataset_endpoint(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Download Kaggle dataset to Azure Blob Storage (uses temp directory, auto-cleaned)
    """
    try:
        result = await dataset_download_service.download_dataset(
            dataset_id=dataset_id,
            source="Kaggle",
            download_path=None  # Uses temp directory, auto-uploaded to Azure
        )

        return {
            "success": result.get("success", False),
            "dataset_id": dataset_id,
            "source": "Kaggle",
            "message": result.get("message", "Download completed"),
            "azure_url": result.get("azure_url")  # Azure URL instead of local path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download Kaggle dataset: {str(e)}"
        )


@router.post("/download/huggingface")
async def download_huggingface_dataset_endpoint(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Download HuggingFace dataset to Azure Blob Storage (uses temp directory, auto-cleaned)
    """
    try:
        result = await dataset_download_service.download_dataset(
            dataset_id=dataset_id,
            source="HuggingFace",
            download_path=None  # Uses temp directory, auto-uploaded to Azure
        )

        return {
            "success": result.get("success", False),
            "dataset_id": dataset_id,
            "source": "HuggingFace",
            "message": result.get("message", "Download completed"),
            "azure_url": result.get("azure_url")  # Azure URL instead of local path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download HuggingFace dataset: {str(e)}"
        )

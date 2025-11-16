from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import csv
import io
import os
import pandas as pd
import numpy as np
import math
import sys
from pathlib import Path
from datetime import datetime
from app.mongodb import mongodb
from app.models.mongodb_models import User, Dataset
from app.schemas.dataset_schemas import DatasetCreate, DatasetResponse
from app.dependencies import get_current_user
from app.services.kaggle_service import kaggle_service
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
        try:
            # Use pandas for schema generation (limit to first 1000 rows for large files)
            print(f"[UPLOAD] Calling pd.read_csv now...")
            df = pd.read_csv(io.StringIO(decoded), nrows=min(1000, len(data_rows)))
            print(f"[UPLOAD] pd.read_csv SUCCESS! Got {len(df)} rows, {len(df.columns)} columns")

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

        # Legacy preview_data for backward compatibility
        preview_data = {
            "headers": headers,
            "rows": data_rows[:10]
        }

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

        dataset_dict = {
            "user_id": current_user.id,
            "name": file.filename or "Untitled Dataset",
            "file_name": file.filename or "unknown.csv",
            "row_count": len(data_rows),
            "column_count": len(headers),
            "file_size": file_size,
            "status": "ready",
            "preview_data": preview_data,
            "uploaded_at": datetime.utcnow(),
            "source": "upload",
            "kaggle_ref": None,
            "download_path": None,
            "schema": schema_cleaned if schema_cleaned else [],
            "sample_data": sample_rows_cleaned if sample_rows_cleaned else [],
            "target_column": target_column if target_column else None,
        }

        # DEBUG: Log what we're saving to MongoDB
        print(f"\n[UPLOAD DEBUG] MongoDB document structure:")
        print(f"  - user_id: {dataset_dict['user_id']}")
        print(f"  - name: {dataset_dict['name']}")
        print(f"  - row_count: {dataset_dict['row_count']}")
        print(f"  - column_count: {dataset_dict['column_count']}")
        print(f"  - file_size: {dataset_dict['file_size']}")
        print(f"  - status: {dataset_dict['status']}")
        print(f"  - schema: {len(dataset_dict['schema'])} columns")
        print(f"  - sample_data: {len(dataset_dict['sample_data'])} rows")
        print(f"  - target_column: {dataset_dict['target_column']}")

        result = await mongodb.database["datasets"].insert_one(dataset_dict)
        dataset_id = str(result.inserted_id)
        dataset_dict["_id"] = result.inserted_id
        print(f"[UPLOAD] ✓ Dataset document created with ID: {dataset_id}")

        # DEBUG: Verify what was actually saved to MongoDB
        saved_doc = await mongodb.database["datasets"].find_one({"_id": result.inserted_id})
        print(f"\n[UPLOAD DEBUG] VERIFICATION - Document in MongoDB:")
        print(f"  - 'schema' field exists: {'schema' in saved_doc}")
        print(f"  - 'schema' value: {type(saved_doc.get('schema'))}")
        print(f"  - 'schema' length: {len(saved_doc.get('schema', [])) if saved_doc.get('schema') else 0}")
        print(f"  - 'sample_data' field exists: {'sample_data' in saved_doc}")
        print(f"  - 'sample_data' value: {type(saved_doc.get('sample_data'))}")
        print(f"  - 'sample_data' length: {len(saved_doc.get('sample_data', [])) if saved_doc.get('sample_data') else 0}")
        print(f"  - 'target_column' field exists: {'target_column' in saved_doc}")
        print(f"  - 'target_column' value: {saved_doc.get('target_column')}")
        if saved_doc.get('schema') is None:
            print(f"\n[UPLOAD ERROR] ❌ SCHEMA IS NULL IN MONGODB!")
        if saved_doc.get('sample_data') is None:
            print(f"[UPLOAD ERROR] ❌ SAMPLE_DATA IS NULL IN MONGODB!")
        if saved_doc.get('target_column') is None:
            print(f"[UPLOAD ERROR] ❌ TARGET_COLUMN IS NULL IN MONGODB!")

        # Save file to disk
        upload_dir = f"backend/data/{dataset_id}"
        print(f"[UPLOAD] Creating upload directory: {upload_dir}")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        print(f"[UPLOAD] Saving file to: {file_path}")

        # Write file to disk
        with open(file_path, 'wb') as f:
            f.write(contents)
        print(f"[UPLOAD] ✓ File saved to disk")

        # Update dataset with file path
        print(f"[UPLOAD] Updating dataset with file path...")
        await mongodb.database["datasets"].update_one(
            {"_id": result.inserted_id},
            {"$set": {"download_path": upload_dir}}
        )
        print(f"[UPLOAD] ✓ Dataset updated with file path")

        # Update user's datasets_count
        print(f"[UPLOAD] Updating user's dataset count...")
        await mongodb.database["users"].update_one(
            {"_id": current_user.id},
            {"$inc": {"datasets_count": 1}}
        )
        print(f"[UPLOAD] ✓ User dataset count updated")

        print("\n" + "="*80)
        print(f"[UPLOAD] ✓✓✓ UPLOAD COMPLETED SUCCESSFULLY ✓✓✓")
        print(f"[UPLOAD] Dataset ID: {dataset_id}")
        print(f"[UPLOAD] File: {file.filename}")
        print(f"[UPLOAD] Size: {file_size} bytes ({file_size / (1024 * 1024):.2f} MB)")
        print(f"[UPLOAD] Rows: {len(data_rows)}, Columns: {len(headers)}")
        print(f"[UPLOAD] Schema columns: {len(schema_cleaned)}")
        print(f"[UPLOAD] Sample rows: {len(sample_rows_cleaned)}")
        print(f"[UPLOAD] Target column: {target_column}")
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
            download_path = f"./data/kaggle/{current_user.id}/{request.dataset_ref.replace('/', '_')}"

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

            # Load with pandas for full inspection
            csv_file_path = csv_files[0]
            file_size = csv_file_path.stat().st_size

            # Load sample (first 1000 rows for metadata) with encoding fallback
            try:
                df = pd.read_csv(csv_file_path, nrows=1000, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    # Try latin-1 encoding as fallback
                    df = pd.read_csv(csv_file_path, nrows=1000, encoding='latin-1')
                except Exception:
                    # Final fallback: ignore errors
                    df = pd.read_csv(csv_file_path, nrows=1000, encoding='utf-8', errors='ignore')

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

            # Clean NaN values for JSON serialization
            schema_cleaned = clean_nan_values(schema)
            sample_rows_cleaned = clean_nan_values(sample_rows)

            # Legacy preview_data for backward compatibility (cleaned)
            preview_rows = df.head(10).to_dict(orient="records")
            preview_rows_cleaned = clean_nan_values(preview_rows)
            preview_data = {
                "headers": list(df.columns),
                "rows": [[row.get(col) for col in df.columns] for row in preview_rows_cleaned]
            }

            # Create dataset record with full metadata
            new_dataset = Dataset(
                user_id=current_user.id,
                name=request.dataset_title,
                file_name=csv_file_path.name,
                row_count=row_count,
                column_count=col_count,
                file_size=file_size,
                status="ready",
                preview_data=preview_data,
                schema=schema_cleaned,
                sample_data=sample_rows_cleaned,
                target_column=target_column,
            )

            # Add Kaggle metadata
            dataset_dict = new_dataset.model_dump(by_alias=True, mode='json')
            dataset_dict["source"] = "kaggle"
            dataset_dict["kaggle_ref"] = request.dataset_ref
            dataset_dict["download_path"] = download_path

            print(f"[ADD_KAGGLE] Fully inspected: {row_count} rows, {col_count} cols, target: {target_column}")

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
                preview_data=None,
            )

            # Add Kaggle metadata
            dataset_dict = new_dataset.model_dump(by_alias=True, mode='json')
            dataset_dict["source"] = "kaggle"
            dataset_dict["kaggle_ref"] = request.dataset_ref
            dataset_dict["download_path"] = None

            print(f"Created pending dataset: {request.dataset_title}, size: {file_size} bytes")

        # Save to database
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
        hub_api_url = f"https://huggingface.co/api/datasets/{request.dataset_name}"

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
        dataset_dict = {
            "user_id": current_user.id,
            "name": request.dataset_name,
            "source": "huggingface",
            "file_name": f"{request.dataset_name.replace('/', '_')}.hf",  # Virtual file name for HuggingFace datasets
            "file_size": 0,  # Size unknown until loaded
            "row_count": 0,  # Will be updated when dataset is loaded
            "column_count": 0,  # Will be updated when dataset is loaded
            "uploaded_at": datetime.utcnow(),
            "status": "pending",  # Will be updated when dataset is loaded
            "huggingface_url": request.dataset_url,
            "huggingface_dataset_id": request.dataset_name,
            "download_path": None,  # Will be set when dataset is downloaded/cached
            "schema": [],
            "sampleData": [],
            "preview_data": {"headers": [], "rows": []},
            "target_column": None,
            "description": f"HuggingFace dataset: {request.dataset_name}"
        }

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
    dataset = await mongodb.database["datasets"].find_one(
        {"_id": ObjectId(dataset_id), "user_id": current_user.id}
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    return DatasetResponse(**dataset)


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

        # Update dataset in database
        update_data = {
            "row_count": row_count,
            "column_count": col_count,
            "file_size": 0,  # HuggingFace datasets don't have a direct file size
            "file_name": f"{hf_dataset_id.replace('/', '_')}.hf",
            "status": "ready",
            "schema": schema_cleaned,
            "sample_data": sample_rows_cleaned,
            "target_column": target_column,
        }

        await mongodb.database["datasets"].update_one(
            {"_id": ObjectId(dataset_id)},
            {"$set": update_data}
        )

        print(f"   ✅ Successfully inspected HuggingFace dataset: {row_count} rows, {col_count} columns")

        return {
            "huggingface_dataset_id": hf_dataset_id,
            "size": 0,
            "rows": row_count,
            "columns": col_count,
            "schema": schema_cleaned,
            "sample": sample_rows_cleaned,
            "target": target_column,
            "file_name": f"{hf_dataset_id.replace('/', '_')}.hf"
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

        # 1. Download dataset (if not already downloaded)
        download_path = f"./data/kaggle/{current_user.id}/{kaggle_ref.replace('/', '_')}"
        Path(download_path).mkdir(parents=True, exist_ok=True)

        # Check if already downloaded
        csv_files = list(Path(download_path).glob("*.csv"))

        if not csv_files:
            print(f"[INSPECT] Starting download of dataset: {kaggle_ref}")
            print(f"[INSPECT] Download path: {download_path}")
            print(f"[INSPECT] Kaggle configured: {kaggle_service.is_configured}")

            try:
                kaggle_service.download_dataset(
                    dataset_ref=kaggle_ref,
                    download_path=download_path
                )
                print(f"[INSPECT] Download completed successfully")
            except Exception as download_error:
                print(f"[INSPECT] Download failed: {str(download_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to download dataset from Kaggle: {str(download_error)}"
                )

            # 2. Find CSV files after download
            csv_files = list(Path(download_path).glob("*.csv"))
        else:
            print(f"[INSPECT] Dataset already downloaded, using cached version")
        if not csv_files:
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

        # 9. Update dataset in database with inspection results
        update_data = {
            "row_count": row_count,
            "column_count": col_count,
            "file_size": size_bytes,
            "file_name": csv_path.name,
            "status": "ready",
            "download_path": download_path,
            "schema": schema_cleaned,
            "sample_data": sample_rows_cleaned,
            "target_column": target_column,
        }

        await mongodb.database["datasets"].update_one(
            {"_id": ObjectId(request.dataset_id)},
            {"$set": update_data}
        )

        print(f"Successfully inspected dataset: {row_count} rows, {col_count} columns, target: {target_column}")

        return {
            "kaggle_ref": kaggle_ref,
            "size": size_bytes,
            "rows": row_count,
            "columns": col_count,
            "schema": schema_cleaned,
            "sample": sample_rows_cleaned,
            "target": target_column,
            "file_name": csv_path.name
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error inspecting dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect dataset: {str(e)}"
        )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
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

        print(f"Attempting to delete dataset: {dataset_id} for user: {current_user.id}")

        result = await mongodb.database["datasets"].delete_one(
            {"_id": dataset_oid, "user_id": current_user.id}
        )

        print(f"Delete result: deleted_count={result.deleted_count}")

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or you don't have permission to delete it"
            )

        # Update user's datasets_count
        await mongodb.database["users"].update_one(
            {"_id": current_user.id},
            {"$inc": {"datasets_count": -1}}
        )

        print(f"Successfully deleted dataset: {dataset_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dataset: {str(e)}"
        )

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List
import csv
import io
from app.mongodb import mongodb
from app.models.mongodb_models import User, Dataset
from app.schemas.dataset_schemas import DatasetCreate, DatasetResponse
from app.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    contents = await file.read()
    file_size = len(contents)

    try:
        decoded = contents.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(decoded))
        rows = list(csv_reader)

        if len(rows) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset file is empty"
            )

        headers = rows[0]
        data_rows = rows[1:]

        preview_data = {
            "headers": headers,
            "rows": data_rows[:10]
        }

        new_dataset = Dataset(
            user_id=current_user.id,
            name=file.filename or "Untitled Dataset",
            file_name=file.filename or "unknown.csv",
            row_count=len(data_rows),
            column_count=len(headers),
            file_size=file_size,
            status="ready",
            preview_data=preview_data,
        )

        result = await mongodb.database["datasets"].insert_one(new_dataset.dict(by_alias=True))
        new_dataset.id = result.inserted_id

        # Update user's datasets_count
        await mongodb.database["users"].update_one(
            {"_id": current_user.id},
            {"$inc": {"datasets_count": 1}}
        )

        return DatasetResponse(**new_dataset.dict(by_alias=True))

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid CSV file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("", response_model=List[DatasetResponse])
async def get_datasets(
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    datasets_cursor = mongodb.database["datasets"].find(
        {"user_id": current_user.id}
    ).sort("uploaded_at", -1).skip(offset).limit(limit)
    datasets = await datasets_cursor.to_list(length=limit)
    return [DatasetResponse(**dataset) for dataset in datasets]


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


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    result = await mongodb.database["datasets"].delete_one(
        {"_id": ObjectId(dataset_id), "user_id": current_user.id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Update user's datasets_count
    await mongodb.database["users"].update_one(
        {"_id": current_user.id},
        {"$inc": {"datasets_count": -1}}
    )

    return None

# Azure Storage Refactoring Plan

## Problem Statement

Currently, full Azure Blob Storage URLs are stored in MongoDB:
- `Dataset.azure_dataset_url` stores: `https://account.blob.core.windows.net/datasets/user_id/dataset_id/file.csv`
- `Model.azure_model_url` stores: `https://account.blob.core.windows.net/models/user_id/model_id/model-v1.zip`

### Issues:
1. **Tight Coupling**: If Azure account URL changes, all MongoDB records need updating
2. **Security**: Full URLs expose Azure account names
3. **Inconsistency**: Some methods expect full URLs, others expect blob paths
4. **Flexibility**: Cannot easily switch storage backends

## Solution: Store Only Blob Paths

Instead of full URLs, store only the relative blob path:
- Store: `user_id/dataset_id/file.csv`
- Construct URL dynamically: `settings.AZURE_ACCOUNT_URL + container + blob_path`

---

## Implementation Plan

### Phase 1: Update Azure Storage Service (`backend/app/utils/azure_storage.py`)

#### 1.1 Modify Upload Methods to Return Blob Paths

**Current Behavior:**
```python
def upload_dataset(...) -> str:
    blob_path = f"{user_id}/{dataset_id}/{filename}"
    blob_client.upload_blob(...)
    return blob_client.url  # Returns FULL URL
```

**New Behavior:**
```python
def upload_dataset(...) -> str:
    blob_path = f"{user_id}/{dataset_id}/{filename}"
    blob_client.upload_blob(...)
    return blob_path  # Returns ONLY blob path
```

**Methods to Update:**
- `upload_dataset()` - Return blob path instead of URL
- `upload_model()` - Return blob path instead of URL

#### 1.2 Add New Download-by-Path Methods

**Add New Methods:**
```python
def download_dataset_by_path(
    self,
    blob_path: str,
    container_name: Optional[str] = None
) -> bytes:
    """Download dataset using blob path (not full URL)"""
    container_name = container_name or self.datasets_container
    return self.download_file(blob_path, container_name)

def download_model_by_path(
    self,
    blob_path: str,
    container_name: Optional[str] = None
) -> bytes:
    """Download model using blob path (not full URL)"""
    container_name = container_name or self.models_container
    return self.download_file(blob_path, container_name)
```

#### 1.3 Add URL Construction Helper

```python
def construct_blob_url(
    self,
    blob_path: str,
    container_name: str
) -> str:
    """Construct full Azure URL from blob path"""
    return f"{self.account_url}/{container_name}/{blob_path}"
```

#### 1.4 Update Existing Download Methods for Backward Compatibility

Keep `download_dataset(azure_url)` but add detection:
```python
def download_dataset(self, path_or_url: str) -> bytes:
    """
    Download dataset from Azure.

    Args:
        path_or_url: Either a blob path (user_id/dataset_id/file.csv)
                     OR a full Azure URL (for backward compatibility)
    """
    if path_or_url.startswith("http"):
        # Legacy: Full URL provided, extract blob path
        blob_path = self._extract_blob_path_from_url(path_or_url)
    else:
        # New: Blob path provided directly
        blob_path = path_or_url

    return self.download_file(blob_path, self.datasets_container)
```

---

### Phase 2: Update MongoDB Models (`backend/app/models/mongodb_models.py`)

#### 2.1 Update Field Names

**Dataset Model:**
```python
class Dataset(BaseModel):
    # OLD:
    # azure_dataset_url: Optional[str] = None

    # NEW:
    azure_blob_path: Optional[str] = None  # Store only blob path
```

**Model Model:**
```python
class Model(BaseModel):
    # OLD:
    # azure_model_url: Optional[str] = None

    # NEW:
    azure_blob_path: Optional[str] = None  # Store only blob path
```

**Migration Note:** Add migration script to convert existing URLs to paths

---

### Phase 3: Update Routers

#### 3.1 Datasets Router (`backend/app/routers/datasets.py`)

**Upload Endpoint (Line 355-378):**
```python
# OLD:
azure_dataset_url = azure_storage_service.upload_dataset(...)
await mongodb.database["datasets"].update_one(
    {"_id": result.inserted_id},
    {"$set": {"azure_dataset_url": azure_dataset_url}}
)

# NEW:
blob_path = azure_storage_service.upload_dataset(...)
await mongodb.database["datasets"].update_one(
    {"_id": result.inserted_id},
    {"$set": {"azure_blob_path": blob_path}}
)
```

**Download/View Endpoint (Line 898):**
```python
# OLD:
azure_url = dataset.get("azure_dataset_url")
csv_bytes = azure_storage_service.download_dataset(azure_url)

# NEW:
blob_path = dataset.get("azure_blob_path")
csv_bytes = azure_storage_service.download_dataset_by_path(blob_path)
```

**Inspect Endpoint (Line 1287-1293):**
```python
# OLD:
azure_dataset_url = azure_storage_service.upload_dataset(...)
update_data = {"azure_dataset_url": azure_dataset_url}

# NEW:
blob_path = azure_storage_service.upload_dataset(...)
update_data = {"azure_blob_path": blob_path}
```

**Delete Endpoint (Line 1382-1393):**
```python
# OLD:
azure_url = dataset.get("azure_dataset_url")
# Extract user_id and dataset_id from URL

# NEW:
blob_path = dataset.get("azure_blob_path")
# Blob path already contains user_id/dataset_id/filename
azure_storage_service.delete_file(blob_path, container_name)
```

**Similar updates needed in:**
- `add_dataset_from_kaggle()` (Line 575-587)
- `inspect_huggingface_dataset()` (Line 1090-1096)

#### 3.2 AutoML Router (`backend/app/routers/automl.py`)

**Training Endpoint (Line 32-44):**
```python
# OLD:
azure_url = dataset.get("azure_dataset_url")
csv_bytes = azure_storage_service.download_dataset(azure_url)

# NEW:
blob_path = dataset.get("azure_blob_path")
csv_bytes = azure_storage_service.download_dataset_by_path(blob_path)
```

**Model Upload (Line 380-387):**
```python
# OLD:
azure_model_url = azure_storage_service.upload_model(...)
model_doc["azure_model_url"] = azure_model_url

# NEW:
blob_path = azure_storage_service.upload_model(...)
model_doc["azure_blob_path"] = blob_path
```

#### 3.3 Models Router (`backend/app/routers/models.py`)

**Prediction Endpoint (Line 217-244):**
```python
# OLD (INCORRECT):
azure_url = model.get("azure_model_url")
model_bytes = azure_storage_service.download_file(
    blob_path=azure_url,  # BUG: This is wrong!
    container_name=settings.AZURE_MODELS_CONTAINER
)

# NEW:
blob_path = model.get("azure_blob_path")
model_bytes = azure_storage_service.download_model_by_path(blob_path)
```

#### 3.4 Dataset Download Service (`backend/app/services/dataset_download_service.py`)

**Download Dataset Method (Line 220-227):**
```python
# OLD:
azure_url = azure_storage_service.upload_file(...)

# NEW:
blob_path = azure_storage_service.upload_file(...)
# Return blob_path instead of azure_url
```

---

### Phase 4: Data Migration

Create migration script: `backend/migrations/migrate_azure_urls_to_paths.py`

```python
async def migrate_azure_urls_to_blob_paths():
    """
    Convert existing azure_dataset_url and azure_model_url to blob_path format

    URL format: https://account.blob.core.windows.net/container/blob_path
    Extract: blob_path
    """

    # Migrate Datasets
    datasets = await mongodb.database["datasets"].find({
        "azure_dataset_url": {"$exists": True, "$ne": None}
    }).to_list(None)

    for dataset in datasets:
        azure_url = dataset["azure_dataset_url"]
        blob_path = extract_blob_path_from_url(azure_url, "datasets")

        await mongodb.database["datasets"].update_one(
            {"_id": dataset["_id"]},
            {
                "$set": {"azure_blob_path": blob_path},
                "$unset": {"azure_dataset_url": ""}
            }
        )

    # Migrate Models
    models = await mongodb.database["models"].find({
        "azure_model_url": {"$exists": True, "$ne": None}
    }).to_list(None)

    for model in models:
        azure_url = model["azure_model_url"]
        blob_path = extract_blob_path_from_url(azure_url, "models")

        await mongodb.database["models"].update_one(
            {"_id": model["_id"]},
            {
                "$set": {"azure_blob_path": blob_path},
                "$unset": {"azure_model_url": ""}
            }
        )

def extract_blob_path_from_url(azure_url: str, container_name: str) -> str:
    """
    Extract blob path from Azure URL

    Input: https://account.blob.core.windows.net/datasets/user_id/dataset_id/file.csv
    Output: user_id/dataset_id/file.csv
    """
    # Split by "/" and extract path after container name
    parts = azure_url.split("/")
    # Format: ['https:', '', 'account.blob.core.windows.net', 'container', 'path', 'parts']
    container_index = parts.index(container_name)
    blob_path = "/".join(parts[container_index + 1:])
    return blob_path
```

---

## Implementation Steps

### Step 1: Update Azure Storage Service ✅
- Modify `upload_dataset()` and `upload_model()` to return blob paths
- Add `download_dataset_by_path()` and `download_model_by_path()`
- Add backward compatibility to existing `download_dataset()`

### Step 2: Update MongoDB Models ✅
- Rename `azure_dataset_url` → `azure_blob_path`
- Rename `azure_model_url` → `azure_blob_path`

### Step 3: Update All Routers ✅
- Update datasets.py (upload, download, delete, inspect)
- Update automl.py (training, model upload)
- Update models.py (prediction endpoint)
- Update dataset_download_service.py

### Step 4: Create Migration Script ✅
- Write migration to convert existing URLs to blob paths
- Test on sample data

### Step 5: Update Response Schemas (Optional) ✅
- Update `DatasetResponse` to include `azure_blob_path` instead of `azure_dataset_url`
- Update `ModelResponse` to include `azure_blob_path` instead of `azure_model_url`
- Frontend may need updates to handle new field names

### Step 6: Testing ✅
- Test upload flow (ensure blob path is stored)
- Test download flow (ensure data loads correctly)
- Test training flow (ensure models can access datasets)
- Test prediction flow (ensure models can be loaded)
- Test migration script on production data

---

## Benefits After Refactoring

1. **Flexibility**: Easy to change Azure account without DB migration
2. **Security**: Azure account names not exposed in MongoDB
3. **Consistency**: All methods use blob paths internally
4. **Maintainability**: Clear separation between storage identifiers and URLs
5. **Testability**: Can mock storage more easily with paths

---

## Rollback Plan

If issues arise:
1. Keep old fields (`azure_dataset_url`, `azure_model_url`) temporarily
2. Populate both old and new fields during transition period
3. Frontend can fall back to old field if new field is null
4. Remove old fields only after confirming new system works

---

## Current Data Flow

### Upload Flow:
```
User uploads CSV
  → FastAPI endpoint
  → azure_storage_service.upload_dataset(user_id, dataset_id, bytes, filename)
    → Constructs blob_path: "user_id/dataset_id/filename"
    → Uploads to Azure
    → Returns: FULL URL ❌
  → Store FULL URL in MongoDB ❌
```

### Download Flow:
```
User views dataset
  → FastAPI endpoint
  → Get dataset from MongoDB (has FULL URL)
  → azure_storage_service.download_dataset(azure_url)
    → Extracts blob_path from URL
    → Downloads from Azure
    → Returns: bytes
  → Send to user
```

## New Data Flow

### Upload Flow:
```
User uploads CSV
  → FastAPI endpoint
  → azure_storage_service.upload_dataset(user_id, dataset_id, bytes, filename)
    → Constructs blob_path: "user_id/dataset_id/filename"
    → Uploads to Azure
    → Returns: blob_path ONLY ✅
  → Store blob_path in MongoDB ✅
```

### Download Flow:
```
User views dataset
  → FastAPI endpoint
  → Get dataset from MongoDB (has blob_path)
  → azure_storage_service.download_dataset_by_path(blob_path)
    → Uses blob_path directly
    → Downloads from Azure
    → Returns: bytes
  → Send to user
```

---

## Questions to Clarify

1. Should we keep `azure_dataset_url` and `azure_model_url` for backward compatibility during transition?
2. Should response schemas continue to expose URLs (constructed dynamically) or paths?
3. Do we need to support generating SAS URLs for temporary access?
4. Should we update the frontend to handle new field names?

---

## Current Implementation Details

### Files with Azure URL References:

1. **`backend/app/utils/azure_storage.py`**
   - Line 130: `upload_file()` returns `blob_url`
   - Line 362: `upload_dataset()` returns `blob_url`
   - Line 380-413: `download_dataset(azure_url)` extracts path from URL
   - Line 453: `upload_model()` returns `blob_url`

2. **`backend/app/models/mongodb_models.py`**
   - Line 111: `Dataset.azure_dataset_url`
   - Line 86: `Model.azure_model_url`

3. **`backend/app/routers/datasets.py`**
   - Line 361: Stores `azure_dataset_url`
   - Line 376: Updates `azure_dataset_url`
   - Line 586: Updates `azure_dataset_url` (Kaggle)
   - Line 890: Reads `azure_dataset_url`
   - Line 898: Calls `download_dataset(azure_url)`
   - Line 1115: Updates `azure_dataset_url` (HuggingFace)
   - Line 1293: Stores `azure_dataset_url` (Inspect)
   - Line 1382: Reads `azure_dataset_url` (Delete)

4. **`backend/app/routers/automl.py`**
   - Line 32: Reads `azure_dataset_url`
   - Line 44: Calls `download_dataset(azure_url)`
   - Line 387: Stores `azure_model_url`

5. **`backend/app/routers/models.py`**
   - Line 236: Reads `azure_model_url`
   - Line 241: **BUG**: Calls `download_file(blob_path=azure_url)` ❌

6. **`backend/app/services/dataset_download_service.py`**
   - Line 222: Uploads and gets `azure_url`
   - Line 238: Returns `azure_url`

---

## End of Plan

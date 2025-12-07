# Smart ML Assistant - Storage Architecture

## 🏗️ Architecture Overview

This application uses a **cloud-native, Azure-only storage architecture**. All datasets and models are stored exclusively in Azure Blob Storage, with MongoDB storing only metadata.

## 📊 Storage Layers

### 1. Azure Blob Storage (PRIMARY - All Data & Models)

**Purpose:** Store ALL CSV datasets and trained model files

**Structure:**
```
Azure Blob Storage Account
├── Container: datasets/
│   └── {user_id}/
│       └── {dataset_id}/
│           └── {filename}.csv
│
└── Container: models/
    └── {user_id}/
        └── {model_id}/
            └── model-{version}.zip
```

**Example:**
```
datasets/6918066a34c75f3c88c6a62d/693459fa0ee77d37a5ffcdf5/sample_dataset.csv
models/6918066a34c75f3c88c6a62d/693457ae0ee77d37a5ffcde8/model-v1.zip
```

**Operations:**
- ✅ Upload: CSV files uploaded directly to Azure
- ✅ Download: CSV fetched from Azure on-demand for viewing/training
- ✅ Delete: Blobs removed from Azure when dataset/model deleted

### 2. MongoDB (METADATA ONLY)

**Purpose:** Store only metadata and references to Azure blobs

**Collections:**

#### `datasets` Collection
```json
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "name": "california_housing.csv",
  "file_name": "housing.csv",
  "row_count": 20640,
  "column_count": 10,
  "file_size": 1484213,
  "status": "ready",
  "azure_dataset_url": "https://storageaccount.blob.core.windows.net/datasets/.../file.csv",
  "source": "kaggle",
  "target_column": "median_house_value",
  "uploaded_at": ISODate("2025-12-06T16:00:00Z")
}
```

**Key Points:**
- ❌ NO CSV data stored in MongoDB
- ❌ NO schema stored in MongoDB
- ❌ NO sample_data stored in MongoDB
- ✅ ONLY metadata + Azure URL

#### `models` Collection
```json
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "name": "Housing Price Predictor",
  "base_model": "NeuralNetTorch",
  "accuracy": "0.85",
  "azure_model_url": "https://storageaccount.blob.core.windows.net/models/.../model-v1.zip",
  "dataset_id": ObjectId("..."),
  "created_at": ISODate("2025-12-06T16:30:00Z")
}
```

**Key Points:**
- ❌ NO model files (.zip) stored in MongoDB
- ✅ ONLY metadata + Azure URL

### 3. Local Filesystem (TEMPORARY ONLY)

**Purpose:** Temporary processing during upload/download/training

**Usage:**
```python
# Temporary directories created during processing
temp_dir = tempfile.mkdtemp(prefix="kaggle_california-housing-prices_")

# Used for:
# - Downloading Kaggle datasets before Azure upload
# - Processing CSV for schema generation
# - Training models before zipping and uploading

# ALWAYS cleaned up after operation:
shutil.rmtree(temp_dir)
```

**Key Points:**
- ✅ Used ONLY during active processing
- ✅ ALWAYS deleted after operation completes
- ✅ ALWAYS deleted even if errors occur
- ❌ NO permanent storage on filesystem
- ❌ NO `data/` directory exists

## 🔄 Data Flow Diagrams

### Dataset Upload Flow

```
User uploads CSV
     ↓
FastAPI receives file
     ↓
Create temp directory
     ↓
Read CSV & generate schema
     ↓
Upload to Azure Blob Storage
     ↓
Save metadata to MongoDB
(name, size, azure_url)
     ↓
Delete temp directory
     ↓
Return dataset info to frontend
```

### Dataset Viewing Flow

```
User opens dataset details
     ↓
Frontend calls GET /api/datasets/{id}
     ↓
Backend fetches metadata from MongoDB
     ↓
Backend downloads CSV from Azure
     ↓
Generate schema & sample data on-the-fly
     ↓
Return metadata + schema + sample_data
     ↓
Frontend displays all components
```

### Model Training Flow

```
User clicks "Train Model"
     ↓
Backend downloads CSV from Azure
     ↓
Create temp directory for model
     ↓
Train with AutoGluon
     ↓
Zip model files
     ↓
Upload model.zip to Azure
     ↓
Save metadata to MongoDB
(name, accuracy, azure_url)
     ↓
Delete temp model directory
     ↓
Return training results
```

### Dataset Deletion Flow

```
User deletes dataset
     ↓
Delete all blobs from Azure
(user_id/dataset_id/*)
     ↓
Delete metadata from MongoDB
     ↓
Update user's dataset count
     ↓
Return success
```

## 🔐 Azure Blob Storage Configuration

**Required Environment Variables:**
```bash
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_ACCOUNT_URL=https://yourstore.blob.core.windows.net/
AZURE_DATASETS_CONTAINER=datasets
AZURE_MODELS_CONTAINER=models
AZURE_STORAGE_ENABLED=true
```

**Authentication Method:**
- Azure AD (Service Principal)
- Client Secret Credential

**Containers:**
- `datasets` - All CSV files
- `models` - All trained model files

## 📝 Code Implementation

### Azure Storage Service

**Location:** `backend/app/utils/azure_storage.py`

**Key Methods:**
```python
# Upload dataset
azure_storage_service.upload_dataset(
    user_id=str(user_id),
    dataset_id=str(dataset_id),
    file_content=csv_bytes,
    filename="data.csv"
)
# Returns: Azure Blob URL

# Download dataset
csv_bytes = azure_storage_service.download_dataset(azure_url)
# Returns: File content as bytes

# Delete dataset
deleted_count = azure_storage_service.delete_dataset(
    user_id=str(user_id),
    dataset_id=str(dataset_id)
)
# Returns: Number of files deleted
```

### Dataset Router

**Location:** `backend/app/routers/datasets.py`

**Upload Endpoint:**
```python
@router.post("/upload")
async def upload_dataset(file: UploadFile):
    # 1. Read file content
    contents = await file.read()

    # 2. Parse CSV and generate schema (temp memory only)
    df = pd.read_csv(io.BytesIO(contents))
    schema = generate_schema(df)

    # 3. Upload to Azure
    azure_url = azure_storage_service.upload_dataset(...)

    # 4. Save metadata to MongoDB
    dataset = {
        "name": file.filename,
        "azure_dataset_url": azure_url,
        # ... other metadata
    }
    await mongodb.datasets.insert_one(dataset)

    return dataset
```

**GET Endpoint:**
```python
@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str):
    # 1. Get metadata from MongoDB
    dataset = await mongodb.datasets.find_one({"_id": dataset_id})

    # 2. Download CSV from Azure
    csv_bytes = azure_storage_service.download_dataset(
        dataset["azure_dataset_url"]
    )

    # 3. Generate schema & sample data on-the-fly
    df = pd.read_csv(io.BytesIO(csv_bytes))
    schema = generate_schema(df)
    sample_data = df.head(20).to_dict("records")

    # 4. Return metadata + generated data
    return {
        **dataset,
        "schema": schema,
        "sampleData": sample_data
    }
```

## ✅ Validation & Safety

### Startup Validation

The application validates Azure configuration on startup:

```python
@app.on_event("startup")
async def startup_db_client():
    if azure_storage_service.is_configured:
        logger.info("[AZURE] Azure Blob Storage is configured and ready")
    else:
        logger.warning("[AZURE] Azure Blob Storage is NOT configured!")
        logger.warning("[AZURE] Dataset and model operations will fail")
```

### Error Handling

- If Azure is not configured → Operations fail with clear error messages
- If temp directory cleanup fails → Logged but doesn't crash the app
- If Azure upload fails → Temp files are still cleaned up

### Temporary File Cleanup

All temporary directories are cleaned up in `finally` blocks:

```python
temp_dir = tempfile.mkdtemp(prefix="model_training_")
try:
    # Process data...
    # Upload to Azure...
finally:
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        logger.info(f"[CLEANUP] Deleted temp directory: {temp_dir}")
```

## 🚫 What We DON'T Do

❌ Store CSV data in MongoDB
❌ Store model files in MongoDB
❌ Store files permanently on local filesystem
❌ Create a `data/` directory
❌ Use local storage as a fallback
❌ Keep temp files after processing

## ✅ What We DO

✅ Store ALL data in Azure Blob Storage
✅ Store only metadata in MongoDB
✅ Use temp directories only during processing
✅ Clean up temp directories after every operation
✅ Validate Azure configuration on startup
✅ Generate schema/sample data on-demand from Azure

## 🔍 Debugging & Monitoring

**Check if files are being cleaned up:**
```bash
# On Windows
dir %TEMP% | findstr /i "kaggle model inspect"

# On Linux/Mac
ls /tmp | grep -E "kaggle|model|inspect"
```

**Expected Result:** Should be empty (no leftover directories)

**Check Azure storage:**
```bash
# Using Azure CLI
az storage blob list --account-name yourstore --container-name datasets
az storage blob list --account-name yourstore --container-name models
```

**Check MongoDB (should only have metadata):**
```javascript
// Connect to MongoDB
db.datasets.findOne()
// Should show metadata ONLY, no 'csv_content' or large 'data' fields
```

## 📦 Dependencies

**Backend:**
```
azure-storage-blob==12.19.0
azure-identity==1.15.0
```

**Environment:**
- Azure Blob Storage account
- Service Principal with Storage Blob Data Contributor role
- MongoDB database (for metadata)

## 🎯 Benefits of This Architecture

1. **Scalability:** Azure handles any file size
2. **Cost:** Pay only for what you store
3. **Reliability:** Azure's redundancy and backups
4. **Clean:** No local filesystem clutter
5. **Cloud-Native:** Works in containers, serverless, etc.
6. **Security:** Azure AD authentication, encrypted at rest

## 📚 Additional Resources

- [Azure Blob Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Azure Identity Documentation](https://docs.microsoft.com/en-us/python/api/azure-identity/)
- [Application Configuration](./backend/app/core/config.py)
- [Azure Storage Service](./backend/app/utils/azure_storage.py)

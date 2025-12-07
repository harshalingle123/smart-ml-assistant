# Azure-Only Storage Architecture - Cleanup Plan

## 📊 Current State Analysis

### ✅ What's Already Working (Azure-Only)

**Backend:**
- ✅ MongoDB: Stores ONLY metadata (name, size, status, azure_url)
- ✅ Azure Blob Storage: Stores ALL CSV files and trained models
- ✅ Temporary directories: Used for processing, immediately cleaned up
- ✅ No permanent local storage exists

**Storage Locations:**
```
Azure Blob Storage (PRIMARY):
  datasets/
    └── {user_id}/{dataset_id}/{filename}.csv
  models/
    └── {user_id}/{model_id}/model-{version}.zip

MongoDB (METADATA ONLY):
  - datasets collection: metadata + azure_dataset_url
  - models collection: metadata + azure_model_url
  - users, chats, messages

Filesystem (TEMPORARY ONLY):
  - /tmp/kaggle_* (auto-deleted after upload)
  - /tmp/model_* (auto-deleted after upload)
  - /tmp/inspect_* (auto-deleted after processing)
```

### ⚠️ Items to Clean Up

1. **Deprecated Code References**
   - `DOWNLOAD_PATH` in config.py (commented but present)
   - Old comments mentioning local storage
   - .gitignore entries for local data directories

2. **Frontend UI Confusion**
   - `downloadPath` state variable (shows Azure operation status, not local path)
   - Could be renamed to `azureUploadPath` for clarity

3. **Documentation**
   - Need to update comments to reflect Azure-only architecture
   - Remove references to "fallback" or "local storage"

## 📋 Implementation Plan

### Phase 1: Code Audit & Cleanup (Backend)

#### 1.1 Configuration Cleanup
**File:** `backend/app/core/config.py`

**Actions:**
- Remove `DOWNLOAD_PATH` comment entirely
- Ensure all Azure settings are properly documented
- Add validation that Azure is properly configured

**Changes:**
```python
# REMOVE:
# DOWNLOAD_PATH: str = "./data/downloads" # Deprecated - using Azure Blob Storage

# ADD clear documentation:
# Azure Blob Storage Configuration (REQUIRED)
# All datasets and models are stored in Azure Blob Storage
# No local filesystem storage is used
```

#### 1.2 Dataset Router Cleanup
**File:** `backend/app/routers/datasets.py`

**Audit Points:**
- ✅ Upload endpoint: Uses temp dir → Azure → cleanup (GOOD)
- ✅ GET endpoint: Fetches from Azure on-demand (GOOD)
- ✅ Delete endpoint: Removes from Azure + MongoDB (GOOD)
- ✅ Kaggle integration: Temp dir → Azure → cleanup (GOOD)

**Actions:**
- Add validation to ensure Azure is configured before allowing operations
- Improve error messages to clarify Azure requirements
- Add logging to confirm temp directory cleanup

#### 1.3 AutoML Router Cleanup
**File:** `backend/app/routers/automl.py`

**Audit Points:**
- ✅ Training: Downloads CSV from Azure (GOOD)
- ✅ Model storage: Temp dir → zip → Azure → cleanup (GOOD)

**Actions:**
- Ensure no model files linger in temp directories
- Add explicit cleanup in error paths
- Validate Azure upload before marking training complete

#### 1.4 Services Cleanup
**Files:**
- `backend/app/services/dataset_download_service.py`
- `backend/app/services/kaggle_service.py`

**Actions:**
- Ensure all downloads use temporary directories
- Verify all temp directories are cleaned up
- No permanent file storage anywhere

### Phase 2: Frontend Cleanup

#### 2.1 Terminology Updates
**File:** `frontend/client/src/components/DownloadableDatasetCard.tsx`

**Actions:**
- Rename `downloadPath` → `azureUploadStatus`
- Update UI messages to clarify Azure operations
- Remove any local file path displays

#### 2.2 API Layer Clarity
**File:** `frontend/client/src/lib/api.ts`

**Actions:**
- Ensure all dataset operations call Azure-aware endpoints
- Add comments explaining Azure architecture
- Remove any fallback logic

### Phase 3: Documentation & Validation

#### 3.1 Architecture Documentation
**Create:** `ARCHITECTURE.md`

**Content:**
- Document Azure-only architecture
- Explain data flow (upload → temp → Azure → cleanup)
- Clarify MongoDB role (metadata only)
- Show container structure

#### 3.2 .gitignore Cleanup
**File:** `.gitignore`

**Actions:**
- Update comments to reflect Azure-only approach
- Keep entries for safety (temp files, accidental CSVs)
- Add clear note: "No local storage - all data in Azure"

#### 3.3 Requirements Validation
**File:** `backend/requirements.txt`

**Actions:**
- Ensure Azure SDK dependencies are present
- Remove any local storage libraries (if any)
- Document minimum required packages

### Phase 4: Testing

#### 4.1 Integration Tests
**Create:** `test_azure_only_flow.py`

**Test Cases:**
1. Upload dataset → verify in Azure only (not filesystem)
2. View dataset → verify fetch from Azure
3. Train model → verify temp cleanup
4. Delete dataset → verify removed from Azure
5. Error handling → verify temp cleanup on failures

#### 4.2 Manual Testing Checklist
```
☐ Upload CSV file → check no local file created
☐ View dataset details → schema fetched from Azure
☐ Train model → /tmp contains no leftover files
☐ Delete dataset → Azure blob deleted
☐ Backend restart → no local data persists
☐ Kaggle download → temp dir cleaned up
☐ Error during upload → temp dir cleaned up
```

### Phase 5: Deployment Preparation

#### 5.1 Environment Validation
**Actions:**
- Ensure Azure credentials are configured
- Test Azure connectivity before startup
- Fail fast if Azure not available

#### 5.2 Migration Notes
**For existing deployments:**
- No data migration needed (already in Azure)
- Remove any old local data directories
- Verify Azure containers exist

## 🎯 Expected Outcomes

### After Cleanup:

**Architecture:**
```
User Upload → FastAPI Backend → Temp Processing → Azure Upload → Temp Cleanup
                                       ↓
                                   MongoDB
                                  (metadata)
```

**No Local Storage:**
- ❌ No `data/` directory
- ❌ No permanent CSV files on disk
- ❌ No model files on disk
- ✅ Only temporary processing directories (auto-cleaned)

**Azure-Only Storage:**
- ✅ All datasets in Azure Blob Storage (datasets container)
- ✅ All models in Azure Blob Storage (models container)
- ✅ MongoDB stores only metadata + Azure URLs
- ✅ Temp directories used only during processing

**Error Handling:**
- ✅ If Azure unavailable → clear error (no fallback)
- ✅ Temp directories cleaned up even on errors
- ✅ No orphaned files on filesystem

## 📝 Files to Modify

### Backend:
1. `backend/app/core/config.py` - Remove DOWNLOAD_PATH comment
2. `backend/app/routers/datasets.py` - Add Azure validation, improve logging
3. `backend/app/routers/automl.py` - Ensure temp cleanup in error paths
4. `backend/app/services/*` - Verify temp directory usage

### Frontend:
1. `frontend/client/src/components/DownloadableDatasetCard.tsx` - Rename downloadPath
2. `frontend/client/src/lib/api.ts` - Add Azure architecture comments

### Documentation:
1. `.gitignore` - Update comments
2. `README.md` - Document Azure requirement
3. `ARCHITECTURE.md` - New file explaining storage architecture

### Testing:
1. `test_azure_only_flow.py` - New comprehensive test
2. `test_temp_cleanup.py` - Verify no filesystem remnants

## 🚨 Critical Validation Points

Before considering this complete, validate:

1. ✅ Zero files in any `data/` directory
2. ✅ All dataset operations go through Azure
3. ✅ All model operations go through Azure
4. ✅ Temp directories are always cleaned up
5. ✅ MongoDB stores NO actual data (only metadata)
6. ✅ System fails gracefully if Azure unavailable
7. ✅ No commented code referencing local storage
8. ✅ Documentation is clear about Azure requirement

## 🔄 Implementation Order

1. **Audit** (1 hour) - Review all code, list all changes needed
2. **Backend Cleanup** (2 hours) - Remove deprecated code, add validation
3. **Frontend Cleanup** (1 hour) - Update terminology, clarify UI
4. **Documentation** (1 hour) - Update all docs and comments
5. **Testing** (2 hours) - Run full test suite, manual testing
6. **Validation** (1 hour) - Check all critical points above

**Total Estimated Time:** 8 hours

## ⚡ Quick Wins (Can do immediately)

1. Remove `DOWNLOAD_PATH` comment from config.py
2. Update .gitignore comment about local storage
3. Add Azure requirement validation on startup
4. Run test to confirm no local files exist after operations

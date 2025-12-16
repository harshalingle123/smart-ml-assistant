# AutoLabel-AI Integration Plan

## Executive Summary
Integrate the autolabel-ai project into smart-ml-assistant by:
1. Creating FastAPI backend services for AI labeling
2. Porting React components to match existing architecture
3. Adding database persistence with MongoDB
4. Securing Gemini API calls on backend
5. Integrating with existing authentication and subscription system

---

## Architecture Overview

### Current State
- **autolabel-ai**: Frontend-only, direct Gemini API calls, no persistence
- **smart-ml-assistant**: Full-stack with FastAPI, MongoDB, user management

### Target State
- **Unified Platform**: Single application with labeling as a new feature module
- **Secure API**: All Gemini calls through FastAPI backend
- **Data Persistence**: MongoDB storage for labeling datasets and results
- **Multi-tenant**: User-based access control with subscription limits

---

## Phase 1: Backend Implementation

### 1.1 Database Models (`backend/app/models/mongodb_models.py`)

```python
class LabelingTask(str, Enum):
    GENERAL = "general_analysis"
    OBJECT_DETECTION = "object_detection"
    SEGMENTATION = "segmentation"
    CAPTIONING = "image_captioning"
    SENTIMENT = "sentiment_analysis"
    TRANSCRIPTION = "transcription"
    ENTITY_EXTRACTION = "entity_extraction"
    SUMMARIZATION = "summarization"

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    PDF = "pdf"
    UNKNOWN = "unknown"

class LabelingFileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class LabelData(BaseModel):
    """Structured labeling result from Gemini"""
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    objects: Optional[List[Dict[str, Any]]] = None  # {label, confidence, box_2d}
    topics: Optional[List[str]] = None
    events: Optional[List[Dict[str, str]]] = None  # {timestamp, description}
    entities: Optional[List[Dict[str, str]]] = None  # {name, type}
    safety_flags: Optional[List[str]] = None

class LabelingFile(Document):
    """Individual file within a labeling dataset"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    dataset_id: PyObjectId
    user_id: PyObjectId

    # File metadata
    filename: str
    original_name: str
    media_type: MediaType
    file_size: int  # bytes
    azure_blob_url: str  # Azure storage location

    # Processing
    status: LabelingFileStatus = LabelingFileStatus.PENDING
    result: Optional[LabelData] = None
    error_message: Optional[str] = None

    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    class Settings:
        name = "labeling_files"

class LabelingDataset(Document):
    """Collection of files for labeling"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId

    # Dataset info
    name: str
    task: LabelingTask
    target_labels: Optional[List[str]] = None  # Constrained label vocabulary

    # Statistics
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0

    # Status
    status: str = "active"  # active, completed, archived

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "labeling_datasets"
```

### 1.2 Labeling Service (`backend/app/services/labeling_service.py`)

**Key Functions:**
- `generate_labels(file_data, media_type, task, target_labels)` - Analyze file with Gemini
- `get_label_suggestions(files, task)` - AI-suggested labels from filenames
- `refine_analysis(file_id, verified_labels)` - Re-analyze after user edits
- `export_dataset(dataset_id, format)` - Export as JSON/CSV/ZIP for fine-tuning
- `process_file_batch(dataset_id, files)` - Batch process uploaded files

**Gemini Integration:**
- Use existing Gemini service or create specialized labeling prompts
- Move API key to backend config (secure)
- Add rate limiting and error handling
- Support multimodal inputs (images, video, audio, PDFs)
- JSON schema validation for structured outputs

### 1.3 API Router (`backend/app/routers/labeling.py`)

```python
# Dataset Management
POST   /api/labeling/datasets              # Create new labeling dataset
GET    /api/labeling/datasets              # List user's datasets
GET    /api/labeling/datasets/{id}         # Get dataset details
PATCH  /api/labeling/datasets/{id}         # Update dataset name/settings
DELETE /api/labeling/datasets/{id}         # Delete dataset

# File Upload & Processing
POST   /api/labeling/datasets/{id}/files   # Upload files to dataset
GET    /api/labeling/datasets/{id}/files   # List files in dataset
GET    /api/labeling/files/{file_id}       # Get file details and results
DELETE /api/labeling/files/{file_id}       # Delete individual file

# Labeling Operations
POST   /api/labeling/analyze               # Trigger analysis for pending files
POST   /api/labeling/refine                # Refine labels after user edits
POST   /api/labeling/suggestions           # Get AI label suggestions

# Export
GET    /api/labeling/datasets/{id}/export  # Export dataset (JSON/CSV/ZIP)
```

**Request/Response Schemas** (`backend/app/schemas/labeling_schemas.py`):
- `CreateDatasetRequest`: name, task, target_labels
- `UploadFilesRequest`: Multipart file upload
- `RefineLabelsRequest`: file_id, verified_labels
- `DatasetResponse`: Full dataset with files
- `LabelingFileResponse`: File with results

### 1.4 Azure Storage Integration

- **Container**: Create `labeling-files` container in Azure Blob Storage
- **Upload Pattern**: `{user_id}/{dataset_id}/{file_id}/{filename}`
- **File Types**: Support images, videos, audio, PDFs, text files
- **Cleanup**: Delete blobs when dataset/file is deleted

### 1.5 Subscription Integration

**Usage Limits** (Add to Plan model):
```python
class Plan:
    # ... existing fields ...
    labeling_files_per_month: int  # Max files to label per month
    labeling_concurrent_files: int  # Max concurrent processing
    labeling_file_size_mb: int     # Max file size
```

**Middleware Checks** (`backend/app/middleware/subscription_middleware.py`):
- `check_labeling_limit()` - Check monthly file limit
- `check_labeling_file_size()` - Validate file size
- Track usage in `UsageRecord.labeling_files_used`

**Plan Limits Example:**
- Free: 50 files/month, 10MB max size
- Pro: 500 files/month, 50MB max size
- Advanced: Unlimited, 100MB max size

---

## Phase 2: Frontend Implementation

### 2.1 New Pages

**`frontend/client/src/pages/Labeling.tsx`**
- List all labeling datasets (grid view)
- Create new dataset button
- Filter by task type
- Search datasets
- Stats: total datasets, files labeled, completion rate

**`frontend/client/src/pages/LabelingDatasetDetail.tsx`**
- Dataset header (name, task, stats)
- File grid with status indicators
- Upload new files button
- Filter by label
- Batch operations (analyze all, export)
- File detail panel (click to view results)

### 2.2 Components to Port/Create

**From autolabel-ai (adapt to our stack):**
- `FileUpload.tsx` → `LabelingFileUpload.tsx`
- `DatasetConfigModal.tsx` → `CreateLabelingDatasetModal.tsx`
- `ResultViewer.tsx` → `LabelingResultViewer.tsx`
- `DeployModal.tsx` → `LabelingExportModal.tsx`
- `StatsBar.tsx` → `LabelingStatsCard.tsx`

**New components:**
- `LabelingDatasetCard.tsx` - Dataset grid item
- `LabelingFileCard.tsx` - File thumbnail with status
- `LabelingSidebar.tsx` - Filter controls
- `LabelEditor.tsx` - Edit/verify labels
- `BatchProcessingProgress.tsx` - Progress indicator

### 2.3 API Client (`frontend/client/src/lib/api.ts`)

Add new API functions:
```typescript
// Datasets
export const createLabelingDataset = (data: CreateDatasetRequest) => ...
export const getLabelingDatasets = () => ...
export const getLabelingDataset = (id: string) => ...
export const updateLabelingDataset = (id: string, data: any) => ...
export const deleteLabelingDataset = (id: string) => ...

// Files
export const uploadLabelingFiles = (datasetId: string, files: File[]) => ...
export const getLabelingFiles = (datasetId: string) => ...
export const getLabelingFile = (fileId: string) => ...
export const deleteLabelingFile = (fileId: string) => ...

// Operations
export const analyzeLabelingFiles = (fileIds: string[]) => ...
export const refineLabels = (fileId: string, labels: any) => ...
export const getLabelSuggestions = (datasetId: string) => ...
export const exportLabelingDataset = (datasetId: string, format: string) => ...
```

### 2.4 Types (`frontend/client/src/types/labeling.ts`)

```typescript
export enum LabelingTask {
  GENERAL = "general_analysis",
  OBJECT_DETECTION = "object_detection",
  SEGMENTATION = "segmentation",
  CAPTIONING = "image_captioning",
  SENTIMENT = "sentiment_analysis",
  TRANSCRIPTION = "transcription",
  ENTITY_EXTRACTION = "entity_extraction",
  SUMMARIZATION = "summarization"
}

export enum MediaType {
  IMAGE = "image",
  VIDEO = "video",
  AUDIO = "audio",
  TEXT = "text",
  PDF = "pdf",
  UNKNOWN = "unknown"
}

export interface LabelData {
  summary?: string
  sentiment?: string
  objects?: Array<{
    label: string
    confidence: number
    box_2d?: number[]
  }>
  topics?: string[]
  entities?: Array<{ name: string; type: string }>
  safety_flags?: string[]
}

export interface LabelingFile {
  id: string
  dataset_id: string
  filename: string
  media_type: MediaType
  status: "pending" | "processing" | "completed" | "failed"
  result?: LabelData
  error_message?: string
  uploaded_at: string
  azure_blob_url: string
}

export interface LabelingDataset {
  id: string
  name: string
  task: LabelingTask
  target_labels?: string[]
  total_files: number
  completed_files: number
  failed_files: number
  status: string
  created_at: string
}
```

### 2.5 Routing Integration (`frontend/client/src/App.tsx`)

Add routes:
```tsx
<Route path="/labeling" component={Labeling} />
<Route path="/labeling/:id" component={LabelingDatasetDetail} />
```

### 2.6 Navigation Integration (`frontend/client/src/components/AppSidebar.tsx`)

Add sidebar item:
```tsx
{
  title: "Labeling",
  url: "/labeling",
  icon: Tag,
  badge: labelingCount
}
```

---

## Phase 3: Integration Tasks

### 3.1 Configuration Updates

**Backend `.env`:**
```env
# Gemini API for labeling (reuse existing)
GOOGLE_GEMINI_API_KEY=existing_key
GEMINI_MODEL=gemini-2.5-flash

# Azure Storage (add container)
AZURE_LABELING_CONTAINER=labeling-files
```

**Frontend - No changes needed** (uses same API URL detection)

### 3.2 Database Migrations

Create migration script: `backend/app/scripts/add_labeling_collections.py`
- Create indexes on labeling_datasets and labeling_files
- Add labeling fields to existing plans
- Initialize usage tracking for existing users

### 3.3 Subscription Plan Updates

Update existing plans in database:
```python
# Free plan
labeling_files_per_month: 50
labeling_file_size_mb: 10

# Pro plan
labeling_files_per_month: 500
labeling_file_size_mb: 50

# Advanced plan
labeling_files_per_month: 10000  # Effectively unlimited
labeling_file_size_mb: 100
```

### 3.4 Usage Dashboard Integration

Update `frontend/client/src/components/UsageDashboard.tsx`:
- Add "Labeling Files" progress bar
- Show files labeled this month vs. limit
- Add labeling storage usage

---

## Phase 4: Testing Strategy

### 4.1 Backend Tests

**Unit Tests** (`backend/tests/test_labeling.py`):
- Test labeling service functions
- Mock Gemini API responses
- Test file upload validation
- Test export format generation

**Integration Tests**:
- End-to-end dataset creation → file upload → analysis → export
- Subscription limit enforcement
- Error handling (API failures, invalid files)

### 4.2 Frontend Tests

**Component Tests**:
- File upload functionality
- Dataset creation modal
- Result viewer rendering
- Label editing

**E2E Tests**:
- Create dataset workflow
- Upload and analyze files
- Export dataset
- Filter and search

### 4.3 Manual Testing Checklist

- [ ] Upload images and verify object detection results
- [ ] Upload videos and verify event detection
- [ ] Upload audio and verify transcription
- [ ] Upload PDFs and verify text extraction
- [ ] Upload text files and verify NER
- [ ] Test label suggestions feature
- [ ] Test manual label editing and refinement
- [ ] Test export in all formats (JSON, CSV, ZIP)
- [ ] Verify subscription limits work
- [ ] Test concurrent file processing
- [ ] Test file size limits
- [ ] Verify Azure storage cleanup on delete

---

## Implementation Breakdown

### Backend Tasks (Estimated)

1. **Database Models** (30 min)
   - Add LabelingDataset, LabelingFile models
   - Add enums for task types and media types

2. **Labeling Service** (2 hours)
   - Port geminiService.ts logic to Python
   - Implement generateLabels, getLabelSuggestions, refineAnalysis
   - Add Azure blob upload/download
   - Add error handling and retries

3. **API Router** (1.5 hours)
   - Implement all CRUD endpoints
   - Add request/response schemas
   - Add file upload handling with multipart

4. **Subscription Integration** (1 hour)
   - Update Plan model with labeling limits
   - Add middleware checks
   - Update UsageRecord tracking

5. **Export Functionality** (1 hour)
   - Generate JSON export
   - Generate CSV export
   - Generate ZIP with JSONL for fine-tuning

6. **Testing** (1 hour)
   - Write unit tests
   - Test with real Gemini API

**Total Backend: ~7 hours**

### Frontend Tasks (Estimated)

1. **Type Definitions** (15 min)
   - Create labeling.ts types
   - Add to api.ts types

2. **API Client** (30 min)
   - Add all labeling API functions
   - Add file upload with FormData

3. **Labeling List Page** (1.5 hours)
   - Dataset grid layout
   - Create dataset modal
   - Search and filter
   - Stats cards

4. **Dataset Detail Page** (2 hours)
   - File grid with previews
   - Upload files component
   - File detail panel
   - Batch operations

5. **Result Viewer Component** (1.5 hours)
   - Media preview (images, video, audio, PDF, text)
   - Display all label types
   - Edit labels functionality
   - Export buttons

6. **Supporting Components** (1.5 hours)
   - LabelingDatasetCard
   - LabelingFileCard
   - CreateLabelingDatasetModal
   - LabelingExportModal
   - Progress indicators

7. **Navigation Integration** (15 min)
   - Add routes
   - Add sidebar menu item
   - Update usage dashboard

8. **Styling & Polish** (1 hour)
   - Match existing design system
   - Responsive layouts
   - Loading states
   - Error states

**Total Frontend: ~8.5 hours**

### Integration & Testing (Estimated)

1. **Database Migration** (30 min)
2. **Plan Updates** (30 min)
3. **End-to-End Testing** (2 hours)
4. **Bug Fixes & Polish** (2 hours)

**Total Integration: ~5 hours**

---

## Total Estimated Time: ~20-21 hours

---

## Dependencies to Add

### Backend
```txt
# Already have google-generativeai in requirements
# May need to add:
Pillow>=10.0.0  # For image processing/resizing
python-magic>=0.4.27  # For MIME type detection
```

### Frontend
```json
{
  "dependencies": {
    "@google/genai": "^1.33.0",  // Add for type definitions
    "jszip": "^3.10.1"  // For ZIP export (may already have)
  }
}
```

---

## Security Considerations

1. **API Key Protection**
   - ✅ Move Gemini API key to backend
   - ✅ Never expose in frontend code
   - ✅ Use environment variables

2. **File Upload Security**
   - ✅ Validate file types on backend
   - ✅ Scan for malicious content
   - ✅ Enforce file size limits
   - ✅ Use secure Azure blob URLs

3. **Access Control**
   - ✅ Users can only access their own datasets
   - ✅ JWT authentication required
   - ✅ Subscription limits enforced

4. **Rate Limiting**
   - ✅ Limit concurrent Gemini API calls
   - ✅ Implement retry logic with backoff
   - ✅ Track usage per user

---

## Migration Path for Existing autolabel-ai Code

### Files to Port:

1. **Services** (convert TS → Python):
   - `services/geminiService.ts` → `backend/app/services/labeling_service.py`

2. **Components** (adapt to our Radix UI stack):
   - `components/FileUpload.tsx` → Keep similar, use our form components
   - `components/DatasetConfigModal.tsx` → Use Radix Dialog + our form patterns
   - `components/ResultViewer.tsx` → Adapt to our card/panel components
   - `components/DeployModal.tsx` → Simplify to export modal

3. **Types**:
   - `types.ts` → `frontend/client/src/types/labeling.ts` + `backend/app/models/mongodb_models.py`

4. **Styling**:
   - Already using TailwindCSS → Keep consistent with our design tokens
   - Replace custom classes with our theme variables

---

## Post-Integration Enhancements (Future)

1. **Advanced Features**:
   - Real-time collaborative labeling
   - Version control for label changes
   - Active learning suggestions
   - Custom model fine-tuning from labeled data
   - Label quality scoring

2. **Performance Optimizations**:
   - Thumbnail generation for previews
   - Progressive image loading
   - WebSocket for real-time progress updates
   - Background job queue for large batches

3. **Integration with Existing Features**:
   - Use labeled data to train AutoML models
   - Chat with AI about labeling results
   - Deploy labeled datasets as APIs

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Gemini API rate limits | Implement queue system, retry logic, exponential backoff |
| Large file uploads | Stream uploads, validate before processing, compress images |
| Storage costs | Set retention policies, allow dataset archiving |
| Processing timeouts | Use background jobs for large batches, SSE for progress |
| Subscription abuse | Strict limit enforcement, monitoring, rate limiting |

---

## Success Criteria

- [ ] Users can create labeling datasets
- [ ] Users can upload files (images, video, audio, text, PDF)
- [ ] Files are automatically analyzed by Gemini
- [ ] Results display correctly with all label types
- [ ] Users can edit and refine labels
- [ ] Export works in all formats
- [ ] Subscription limits are enforced
- [ ] All data persists to MongoDB
- [ ] Files stored securely in Azure
- [ ] API key never exposed to frontend
- [ ] UI matches existing design system
- [ ] No regressions in existing features

---

## Implementation Order

### Phase 1: Foundation (Backend Core)
1. Database models
2. Labeling service (Gemini integration)
3. Basic API router (CRUD)
4. File upload to Azure

### Phase 2: Frontend Core
1. Type definitions
2. API client functions
3. Labeling list page (basic)
4. Dataset detail page (basic)

### Phase 3: Features
1. Result viewer with all label types
2. Label editing and refinement
3. Export functionality
4. File upload improvements

### Phase 4: Integration
1. Subscription limits
2. Usage tracking
3. Navigation integration
4. Polish and testing

This phased approach allows for incremental testing and reduces integration risk.

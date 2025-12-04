# 🚀 Training Implementation Flow & Architecture Guide

**Smart ML Assistant - Complete Training Pipeline Documentation**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Flow](#component-flow)
4. [Detailed Training Flow](#detailed-training-flow)
5. [Code Implementation](#code-implementation)
6. [Integration Points](#integration-points)
7. [Data Flow](#data-flow)
8. [API Endpoints](#api-endpoints)

---

## 🎯 Overview

The Smart ML Assistant implements a **complete end-to-end ML training pipeline** that integrates:
- Multi-source dataset discovery (Kaggle + HuggingFace)
- AI-powered model recommendations
- AutoML training with real-time progress tracking
- Deployment-ready models

### Key Features:
- ✅ Automatic dataset inspection with schema detection
- ✅ Auto-detection of target columns
- ✅ Real AutoML training using AutoGluon
- ✅ Server-Sent Events (SSE) for live progress updates
- ✅ Fallback to simulation mode if AutoGluon unavailable
- ✅ Production-safe (works with ephemeral filesystems)

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Chat.tsx   │  │ DatasetCard  │  │  useTraining │             │
│  │              │  │              │  │     Hook     │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
          │ User Query       │ Click Train      │ SSE Connection
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────────────┐
│                      BACKEND API LAYER                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  messages.py     │  │  datasets.py     │  │   automl.py     │  │
│  │  /api/messages   │  │  /api/datasets   │  │  /api/automl    │  │
│  │    /chat         │  │    /inspect      │  │    /train       │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬────────┘  │
└───────────┼────────────────────┼─────────────────────┼────────────┘
            │                    │                     │
            │                    │                     │
┌───────────▼────────────────────▼─────────────────────▼────────────┐
│                       SERVICE LAYER                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │ ml_orchestrator  │  │ dataset_download │  │  gemini_service │  │
│  │   .py            │  │   _service.py    │  │      .py        │  │
│  │                  │  │                  │  │                 │  │
│  │ - recommend()    │  │ - search()       │  │ - analyze()     │  │
│  │ - make_decision()│  │ - download()     │  │ - optimize()    │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬────────┘  │
└───────────┼────────────────────┼─────────────────────┼────────────┘
            │                    │                     │
            │                    │                     │
┌───────────▼────────────────────▼─────────────────────▼────────────┐
│                      EXTERNAL SERVICES                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Kaggle     │  │ HuggingFace  │  │    Gemini    │             │
│  │     API      │  │     Hub      │  │     API      │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
            │                    │                     │
            └────────────────────┼─────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────────┐
│                         DATA STORAGE                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      MongoDB                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │   │
│  │  │   datasets   │  │    models    │  │   messages   │       │   │
│  │  │  collection  │  │  collection  │  │  collection  │       │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  File System / Storage                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │   │
│  │  │  CSV Files   │  │ Trained      │  │  AutoGluon   │       │   │
│  │  │  (datasets)  │  │  Models      │  │   Cache      │       │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Component Flow

### 1. Dataset Discovery Flow

```
┌─────────────┐
│ User Query  │ "Find sentiment analysis datasets"
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ messages.py: /api/messages/chat             │
│                                              │
│ 1. Analyze query with Gemini                │
│ 2. Detect: needs_kaggle_search = True       │
│ 3. Extract search terms                     │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ dataset_download_service.search_all_sources()│
│                                              │
│ 1. Optimize query (fix typos)               │
│ 2. Search Kaggle API (parallel)             │
│ 3. Search HuggingFace API (parallel)        │
│ 4. Rank by semantic relevance               │
│ 5. Return top 5 combined                    │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ Response to User                             │
│                                              │
│ - Top 5 datasets with metadata               │
│ - Relevance scores                           │
│ - Download counts                            │
│ - Source breakdown (Kaggle/HF)              │
│ - Downloadable dataset cards                 │
└──────────────────────────────────────────────┘
```

### 2. Dataset Inspection Flow

```
┌─────────────────┐
│ User clicks     │ "Inspect Dataset" or "Add to Collection"
│ dataset card    │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ datasets.py: /api/datasets/add-from-kaggle  │
│                                              │
│ 1. Check if Kaggle API configured            │
│ 2. Download dataset to local storage         │
│ 3. Find CSV files in download                │
└──────┬───────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ Dataset Processing (pandas)                  │
│                                              │
│ 1. Load CSV (first 1000 rows for metadata)  │
│ 2. Generate schema:                          │
│    - Column names                            │
│    - Data types (int, float, object)        │
│    - Null counts                             │
│    - Unique counts                           │
│ 3. Extract sample data (20 rows)            │
│ 4. Auto-detect target column:               │
│    - Match keywords (price, label, etc.)    │
│    - Check user query                        │
│    - Fallback to last column                │
└──────┬───────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ Save to MongoDB: datasets collection         │
│                                              │
│ {                                            │
│   user_id, name, file_name,                  │
│   row_count, column_count, file_size,        │
│   schema: [...],                             │
│   sample_data: [...],                        │
│   target_column: "detected_column",          │
│   csv_content: "..." (production mode),      │
│   status: "ready"                            │
│ }                                            │
└──────┬───────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ Frontend: Dataset Card Updated               │
│                                              │
│ ✓ Shows schema preview                       │
│ ✓ Shows target column                        │
│ ✓ "Train Model" button enabled               │
└──────────────────────────────────────────────┘
```

### 3. Training Flow (Current Implementation)

```
┌─────────────────┐
│ User initiates  │ Click "Train Model" button
│ training        │ URL: /?chat=XXX&dataset=YYY&train=true
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│ Frontend: Chat.tsx (useEffect)                           │
│                                                           │
│ 1. Parse URL params:                                     │
│    - chat_id                                             │
│    - dataset_id                                          │
│    - train=true flag                                     │
│ 2. Call: handleStartTraining(dataset_id, chat_id)       │
└────────┬─────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│ Frontend: useTraining Hook                               │
│                                                           │
│ const startTraining = (datasetId, chatId, onProgress) => │
│                                                           │
│ 1. Establish SSE connection:                             │
│    EventSource(`/api/automl/train/${datasetId}?          │
│                 chat_id=${chatId}`)                      │
│                                                           │
│ 2. Listen for events:                                    │
│    - onmessage: Parse JSON data                          │
│    - Handle event types: status, progress, error,        │
│      complete                                            │
└────────┬─────────────────────────────────────────────────┘
         │
         │ HTTP GET (SSE Stream)
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│ Backend: automl.py                                        │
│ POST /api/automl/train/{dataset_id}                      │
│                                                           │
│ 1. Validate dataset exists                               │
│ 2. Validate chat exists                                  │
│ 3. Return StreamingResponse(event_generator())           │
└────────┬─────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│ async def event_generator(dataset_id, chat_id):          │
│                                                           │
│ PHASE 1: Load Dataset                                    │
│ ├─ Check dataset metadata in MongoDB                     │
│ ├─ Verify target_column is set                           │
│ ├─ Priority 1: Load from csv_content (MongoDB)           │
│ │  └─ Production-safe, works on ephemeral FS             │
│ ├─ Priority 2: Load from file_path (Development)         │
│ │  └─ Read CSV from disk                                 │
│ └─ Send SSE: "📊 Dataset loaded: X rows, Y columns"      │
│                                                           │
│ PHASE 2: Initialize AutoML                               │
│ ├─ Try: from autogluon.tabular import TabularPredictor  │
│ ├─ If success: use_autogluon = True                      │
│ └─ If ImportError: use_autogluon = False (simulation)    │
│                                                           │
│ PHASE 3: Data Preparation                                │
│ ├─ Verify target column exists in DataFrame              │
│ ├─ Get first 5 rows as sample                            │
│ ├─ Clean NaN values for JSON serialization               │
│ └─ Save sample to chat as message                        │
│                                                           │
│ PHASE 4A: Real AutoML Training (if available)            │
│ ├─ Detect task type:                                     │
│ │  └─ Classification: if dtype=object or nunique < 20   │
│ │  └─ Regression: otherwise                              │
│ ├─ Create TabularPredictor:                              │
│ │  └─ label=target_column                                │
│ │  └─ path=backend/models/{dataset_id}                   │
│ │  └─ problem_type='multiclass' or 'regression'          │
│ │  └─ eval_metric='accuracy' or 'r2'                     │
│ ├─ Train in executor (non-blocking):                     │
│ │  └─ predictor.fit(train_data=df, time_limit=60,       │
│ │                    presets='medium_quality')           │
│ ├─ Get leaderboard and best model                        │
│ └─ Calculate metrics:                                    │
│    └─ Classification: accuracy, f1, precision, recall    │
│    └─ Regression: r2_score, MAE, RMSE                    │
│                                                           │
│ PHASE 4B: Simulation Training (fallback)                 │
│ ├─ Simulate 5 model training steps:                      │
│ │  1. Random Forest (20% progress)                       │
│ │  2. XGBoost (40% progress)                             │
│ │  3. LightGBM (60% progress)                            │
│ │  4. Neural Network (80% progress)                      │
│ │  5. Ensemble (100% progress)                           │
│ ├─ Each step: send SSE + save message to chat           │
│ └─ Generate random metrics (75-95% accuracy)             │
│                                                           │
│ PHASE 5: Save Model to Database                          │
│ ├─ Create model document:                                │
│ │  {                                                      │
│ │    user_id, name, base_model,                          │
│ │    dataset_id, task_type,                              │
│ │    metrics: {accuracy, f1, etc.},                      │
│ │    model_path: "backend/models/...",                   │
│ │    uses_real_model: true/false,                        │
│ │    status: "ready"                                     │
│ │  }                                                      │
│ ├─ Insert into models collection                         │
│ └─ Get model_id                                          │
│                                                           │
│ PHASE 6: Complete & Notify                               │
│ ├─ Format result message with metrics                    │
│ ├─ Save final message to chat                            │
│ └─ Send SSE complete event:                              │
│    {                                                      │
│      type: "complete",                                   │
│      message: "Training Complete!",                      │
│      model_id, best_model, metrics                       │
│    }                                                      │
└────────┬─────────────────────────────────────────────────┘
         │
         │ SSE Events Stream
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│ Frontend: Event Handlers                                 │
│                                                           │
│ eventSource.onmessage = (event) => {                     │
│   const data = JSON.parse(event.data);                   │
│                                                           │
│   switch(data.type) {                                    │
│     case "status":                                       │
│       └─ addMessage(data.message)                        │
│     case "progress":                                     │
│       └─ updateProgressBar(data.progress)                │
│     case "error":                                        │
│       └─ showError(data.message)                         │
│     case "complete":                                     │
│       ├─ eventSource.close()                             │
│       ├─ addMessage(data.message)                        │
│       ├─ updateURL to remove ?train=true                 │
│       └─ showToast("Training Complete!")                 │
│   }                                                       │
│ }                                                         │
└──────────────────────────────────────────────────────────┘
```

---

## 💻 Code Implementation

### File Structure

```
backend/app/
├── routers/
│   ├── automl.py           ⭐ Main training endpoint
│   ├── messages.py         📨 Chat & query analysis
│   ├── datasets.py         📦 Dataset inspection
│   └── training_jobs.py    🔄 Background job tracking
│
├── services/
│   ├── ml_orchestrator.py  🤖 Model recommendations
│   ├── gemini_service.py   ✨ AI query analysis
│   ├── dataset_download_service.py  📥 Multi-source search
│   └── huggingface_service.py       🤗 HF integration
│
└── models/
    └── mongodb_models.py   🗄️ Database schemas

frontend/client/src/
├── pages/
│   └── Chat.tsx            💬 Main chat interface
│
├── hooks/
│   ├── useChat.ts          📡 Chat state management
│   └── useTraining.ts      🎯 Training SSE handler
│
└── components/
    ├── KaggleDatasetCard.tsx      📊 Kaggle dataset UI
    ├── HuggingFaceDatasetCard.tsx 🤗 HF dataset UI
    └── DownloadableDatasetCard.tsx 📦 Unified dataset card
```

### Key Code Sections

#### 1. Training Endpoint (`backend/app/routers/automl.py`)

```python
# Line 407-451: Main training endpoint
@router.post("/train/{dataset_id}")
async def train_model(
    dataset_id: str,
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Start AutoML training with SSE progress updates"""

    # Validate dataset and chat
    # Return StreamingResponse with event_generator()

    return StreamingResponse(
        event_generator(dataset_id, chat_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

#### 2. Event Generator (`backend/app/routers/automl.py`)

```python
# Line 17-404: SSE event stream generator
async def event_generator(dataset_id: str, chat_id: str):
    """
    Yields SSE events:
    - data: {"type": "status", "message": "Loading..."}
    - data: {"type": "progress", "message": "Training...", "progress": 50}
    - data: {"type": "complete", "model_id": "...", "metrics": {...}}
    """

    # Phase 1: Load dataset from MongoDB or filesystem
    # Phase 2: Initialize AutoGluon (or fallback to simulation)
    # Phase 3: Prepare data and show sample
    # Phase 4: Train model (real or simulated)
    # Phase 5: Save model to database
    # Phase 6: Send completion event
```

#### 3. Frontend Training Hook (`frontend/client/src/hooks/useTraining.ts`)

```typescript
export const useTraining = () => {
  const [isTraining, setIsTraining] = useState(false);

  const startTraining = (
    datasetId: string,
    chatId: string,
    onProgress: (data: any) => void
  ) => {
    setIsTraining(true);

    // Create SSE connection
    const eventSource = new EventSource(
      `${API_URL}/api/automl/train/${datasetId}?chat_id=${chatId}`
    );

    // Handle events
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onProgress(data);

      if (data.type === 'complete' || data.type === 'error') {
        eventSource.close();
        setIsTraining(false);
      }
    };

    return eventSource;
  };

  return { isTraining, startTraining };
};
```

#### 4. Chat Integration (`frontend/client/src/pages/Chat.tsx`)

```typescript
// Line 29-76: Initialize chat and handle training
useEffect(() => {
  const initializeChat = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const existingChatId = urlParams.get('chat');
    const datasetId = urlParams.get('dataset');
    const shouldTrain = urlParams.get('train') === 'true';

    if (shouldTrain && datasetId) {
      handleStartTraining(datasetId, existingChatId);
    }
  };

  initializeChat();
}, []);

// Line 79-101: Training handler
const handleStartTraining = (datasetId: string, currentChatId: string) => {
  startTraining(datasetId, currentChatId, (data) => {
    if (data.type === "status" || data.type === "progress") {
      addMessage({
        role: "assistant",
        content: data.message,
        timestamp: new Date()
      });
    } else if (data.type === "complete") {
      addMessage({
        role: "assistant",
        content: data.message,
        timestamp: new Date(),
        metadata: {
          model_id: data.model_id,
          metrics: data.metrics
        }
      });
    }
  });
};
```

---

## 🔗 Integration Points

### 1. Dataset Discovery → Training

```
messages.py (line 159-251)
├─ Detects: ML task keywords (classify, train, predict)
├─ Searches datasets via dataset_download_service
├─ Returns metadata with downloadable_datasets
└─ Frontend shows "Add to Collection" button
    │
    ▼
datasets.py (line 487-678)
├─ Downloads dataset from Kaggle/HuggingFace
├─ Inspects and generates schema
├─ Auto-detects target column
└─ Saves to MongoDB with status="ready"
    │
    ▼
Chat.tsx (line 270-285)
└─ Shows "Start Fine-tuning" button for ready datasets
    │
    ▼
automl.py (line 407)
└─ Starts training via SSE
```

### 2. Model Recommendation → Training

```
ml_orchestrator.py (line 28-102)
├─ recommend_models(task_description, dataset_id)
├─ Searches HuggingFace models
├─ Ranks by downloads/likes
└─ Returns top 3 with confidence scores
    │
    ▼
messages.py (line 255-336)
├─ Calls ml_orchestrator when ML task detected
├─ Formats recommendations for user
└─ Shows cost/time estimates
    │
    ▼
automl.py
└─ Uses recommended model for training
```

### 3. Training → Deployment

```
automl.py (line 354-373)
├─ Training completes successfully
├─ Saves to models collection:
│  {
│    model_id, base_model, metrics,
│    model_path, task_type, status="ready"
│  }
└─ Returns model_id to frontend
    │
    ▼
training_jobs.py (line 481-540)
└─ deploy_trained_model(job_id)
    ├─ Creates deployment record
    ├─ Generates API endpoint
    └─ Returns: /api/deployed/{id}/predict
```

---

## 📊 Data Flow

### MongoDB Collections

```
┌─────────────────────────────────────────────────────────────────┐
│ DATASETS Collection                                             │
├─────────────────────────────────────────────────────────────────┤
│ {                                                               │
│   _id: ObjectId,                                                │
│   user_id: ObjectId,                                            │
│   name: "House Prices Dataset",                                 │
│   source: "kaggle" | "huggingface" | "upload",                 │
│   kaggle_ref: "username/dataset-name",                          │
│   file_name: "housing.csv",                                     │
│   row_count: 20640,                                             │
│   column_count: 10,                                             │
│   file_size: 1234567,                                           │
│   status: "ready" | "pending" | "error",                       │
│   schema: [                                                     │
│     {name: "longitude", dtype: "float64", null_count: 0},       │
│     {name: "latitude", dtype: "float64", null_count: 0},        │
│     {name: "price", dtype: "float64", null_count: 0}            │
│   ],                                                            │
│   sample_data: [{longitude: -122.23, latitude: 37.88, ...}],   │
│   target_column: "price",                                       │
│   csv_content: "longitude,latitude,price\n..." (production),    │
│   download_path: "./data/kaggle/..." (development),             │
│   uploaded_at: ISODate                                          │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Used by
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ MODELS Collection                                               │
├─────────────────────────────────────────────────────────────────┤
│ {                                                               │
│   _id: ObjectId,                                                │
│   user_id: ObjectId,                                            │
│   name: "House Prices - WeightedEnsemble",                      │
│   base_model: "WeightedEnsemble_L2",                            │
│   dataset_id: ObjectId (references datasets),                   │
│   task_type: "regression",                                      │
│   status: "ready",                                              │
│   metrics: {                                                    │
│     r2_score: 0.8234,                                           │
│     mae: 45234.56,                                              │
│     rmse: 62345.78                                              │
│   },                                                            │
│   model_path: "backend/models/65f3a.../",                       │
│   uses_real_model: true,                                        │
│   created_at: ISODate                                           │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Referenced in
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ MESSAGES Collection                                             │
├─────────────────────────────────────────────────────────────────┤
│ {                                                               │
│   _id: ObjectId,                                                │
│   chat_id: ObjectId,                                            │
│   role: "assistant",                                            │
│   content: "Training Complete! Accuracy: 82.34%",               │
│   query_type: "ml_agent",                                       │
│   metadata: {                                                   │
│     model_id: ObjectId,                                         │
│     metrics: {...},                                             │
│     best_model: "WeightedEnsemble_L2"                           │
│   },                                                            │
│   timestamp: ISODate                                            │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🌐 API Endpoints

### Training Endpoints

```
POST /api/automl/train/{dataset_id}
├─ Query Params: chat_id (required)
├─ Auth: Bearer token required
├─ Response: text/event-stream (SSE)
└─ Events:
   ├─ {type: "status", message: "Loading dataset..."}
   ├─ {type: "progress", message: "Training 1/5", progress: 20}
   └─ {type: "complete", model_id: "...", metrics: {...}}

GET /api/datasets/{dataset_id}
├─ Returns: Dataset details with schema and sample data
└─ Used to verify target column before training

POST /api/datasets/inspect
├─ Body: {dataset_id, user_query}
├─ Downloads dataset if not present
├─ Generates schema and detects target column
└─ Updates dataset status to "ready"

POST /api/ml/models/recommend
├─ Body: {task_type, dataset_id, constraints}
├─ Returns: Top 3 model recommendations with scores
└─ Used before training for model selection
```

### Dataset Discovery Endpoints

```
POST /api/messages/chat
├─ Body: {chat_id, content, role: "user"}
├─ Analyzes query with Gemini
├─ Searches datasets if needed
└─ Returns: AI response with dataset suggestions

POST /api/messages/agent
├─ Same as /chat but uses advanced agent mode
├─ Direct API search for datasets
└─ Better for explicit dataset requests

POST /api/datasets/search-all
├─ Body: {query, optimize_query: true}
├─ Searches Kaggle + HuggingFace
├─ Ranks by semantic relevance
└─ Returns: {datasets: [...], total_found, kaggle_count, hf_count}
```

---

## 🎯 Training Scenarios

### Scenario 1: Real AutoML Training

```
Prerequisites:
✓ AutoGluon installed (pip install autogluon)
✓ Dataset with target column selected
✓ Sufficient disk space for model cache

Flow:
1. User clicks "Train Model"
2. Backend loads dataset from MongoDB
3. Creates TabularPredictor with AutoGluon
4. Trains for 60 seconds (quick mode)
5. Evaluates models and selects best one
6. Saves model to: backend/models/{dataset_id}/
7. Returns real metrics (accuracy, f1, etc.)

Result:
✓ Deployable model saved to disk
✓ Real predictions available via API
✓ Leaderboard with all models tried
```

### Scenario 2: Simulation Mode Training

```
Prerequisites:
✗ AutoGluon not installed
✓ Dataset with target column selected

Flow:
1. User clicks "Train Model"
2. Backend detects AutoGluon unavailable
3. Simulates 5 training steps (2 seconds each)
4. Generates realistic random metrics
5. No model saved to disk
6. Returns simulated metrics

Result:
✓ Demo-ready for UI/UX testing
✓ Fast completion (10 seconds)
✗ No real model for predictions
```

### Scenario 3: Production Training (Ephemeral FS)

```
Prerequisites:
✓ Production environment (Render, Heroku, etc.)
✓ CSV content stored in MongoDB
✓ AutoGluon installed

Flow:
1. Backend loads csv_content from MongoDB
2. Creates DataFrame from in-memory string
3. Trains model (model_path on ephemeral disk)
4. Saves model metadata to MongoDB
5. Model files lost on container restart

Note: For persistent models in production:
- Use S3/GCS to store model files
- Or use model-as-a-service (HuggingFace Inference API)
```

---

## 🔍 Debugging & Monitoring

### Log Points

```python
# automl.py - Key log points
print(f"[AUTOML] Loading dataset: {dataset_id}")          # Line 26
print(f"[AUTOML] Dataset loaded: {len(df)} rows")         # Line 102
print(f"[AUTOML] AutoML loaded successfully")             # Line 129
print(f"[AUTOML] Using simulation mode")                  # Line 132
print(f"[AUTOML] Training complete: {best_model}")        # Line 233
```

### SSE Event Tracking

```javascript
// Frontend - Track all events
eventSource.onmessage = (event) => {
  console.log('[SSE]', event.data);

  const data = JSON.parse(event.data);
  console.log('[SSE Type]', data.type);
  console.log('[SSE Message]', data.message);
};
```

### MongoDB Queries

```javascript
// Check dataset status
db.datasets.findOne({_id: ObjectId("...")})

// Check trained models
db.models.find({user_id: ObjectId("...")}).sort({created_at: -1})

// Check training messages
db.messages.find({
  chat_id: ObjectId("..."),
  content: {$regex: "Training"}
}).sort({timestamp: -1})
```

---

## 📈 Performance Considerations

### Training Time

| Dataset Size | Model Type | Training Time | Cost (GPU) |
|-------------|-----------|---------------|-----------|
| < 1K rows | AutoML Quick | 1-2 min | $0.01 |
| 1K-10K rows | AutoML Medium | 5-10 min | $0.08 |
| 10K-100K rows | AutoML Full | 30-60 min | $0.50 |
| > 100K rows | Distributed | 2-4 hours | $4.00 |

### Optimization Tips

1. **Dataset Loading**
   - Use `nrows=1000` for inspection
   - Store csv_content in MongoDB for production
   - Use encoding fallback (utf-8 → latin-1 → ignore)

2. **Training**
   - Set `time_limit=60` for quick demos
   - Use `presets='medium_quality'` for balance
   - Run in executor to avoid blocking event loop

3. **Memory Management**
   - Delete DataFrames after use
   - Call `gc.collect()` after training
   - Monitor with `log_memory_usage()`

---

## ✅ Testing Checklist

### Pre-Training Tests
- [ ] Dataset exists in MongoDB
- [ ] Dataset status is "ready"
- [ ] Target column is set
- [ ] CSV content or download_path is available
- [ ] User has permission to access dataset

### During Training Tests
- [ ] SSE connection established
- [ ] Progress events received every 1-2 seconds
- [ ] Messages saved to chat collection
- [ ] Memory usage stays under limit
- [ ] No event loop blocking (health check responds)

### Post-Training Tests
- [ ] Model saved to models collection
- [ ] model_id returned to frontend
- [ ] Metrics are realistic (not NaN or Infinity)
- [ ] Chat shows completion message
- [ ] SSE connection closed properly

---

## 🚀 Next Steps

### Immediate Improvements
1. Add model deployment API
2. Implement model predictions endpoint
3. Add training job queue for multiple users
4. Store models in S3/GCS for production

### Future Enhancements
1. Support for image/audio datasets
2. Distributed training for large datasets
3. Hyperparameter tuning with Optuna
4. Model comparison dashboard
5. A/B testing for deployed models

---

## 📞 Support & Resources

- **GitHub:** https://github.com/harshalingle123/smart-ml-assistant
- **AutoGluon Docs:** https://auto.gluon.ai/stable/tutorials/
- **SSE Guide:** https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events

---

**Document Version:** 1.0
**Last Updated:** December 2024
**Status:** Production-Ready ✅


# QUICK REFERENCE: dataset.py → Backend Implementation

## Function Mapping

| dataset.py Function | Backend Implementation | Status |
|---------------------|------------------------|--------|
| `extract_spec()` | `gemini_service.extract_spec()` | ✅ EXACT |
| `search_apis()` - Kaggle | `kaggle_service.search_datasets(sort_by='votes')` | ✅ EXACT |
| `search_apis()` - HuggingFace | `huggingface_service.search_datasets(sort="downloads", direction=-1)` | ✅ EXACT |
| `rank_candidates()` | `gemini_service.rank_candidates()` | ✅ EXACT |
| `download_kaggle_dataset()` | `dataset_download_service.download_kaggle_dataset()` | ✅ EXACT |
| `download_huggingface_dataset()` | `dataset_download_service.download_huggingface_dataset()` | ✅ EXACT |

---

## API Endpoints Usage

### 1. Chat with Dataset Search
```bash
POST /api/messages/chat
{
  "chat_id": "...",
  "content": "find dataset for diabetes analysis"
}
```

**Backend Flow:**
```
User Query → extract_spec() → search_all_sources() → rank_candidates() → Top 5 Results
```

---

### 2. Direct Dataset Search
```bash
POST /api/datasets/search-all
{
  "query": "diabetes analysis",
  "optimize_query": true
}
```

**Backend Flow:**
```
Query → extract_spec() → Kaggle (votes, 15) + HuggingFace (downloads, -1, 15) → rank_candidates()
```

---

### 3. Download Kaggle Dataset
```bash
POST /api/datasets/download/kaggle
{
  "dataset_id": "username/dataset-name",
  "download_path": "./downloads"  # optional
}
```

---

### 4. Download HuggingFace Dataset
```bash
POST /api/datasets/download/huggingface
{
  "dataset_id": "username/dataset-name",
  "download_path": "./downloads"  # optional
}
```

---

## Key Parameters (EXACT from dataset.py)

### Query Optimization
- **Model:** `gemini-2.5-flash`
- **Prompt:** Fixes typos (dibetes → diabetes)
- **Output:** `{fixed_query, keywords}`

### Kaggle Search
- **sort_by:** `'votes'`
- **limit:** `15` (top 15 results)
- **Output:** `{id, title, description, source='Kaggle', url, downloads}`

### HuggingFace Search
- **sort:** `'downloads'`
- **direction:** `-1` (descending)
- **limit:** `15`
- **Output:** `{id, title, description, source='HuggingFace', url, downloads}`

### Semantic Ranking
- **Model:** `models/text-embedding-004`
- **Query Task:** `retrieval_query`
- **Document Task:** `retrieval_document`
- **Similarity:** Cosine similarity
- **Output:** Candidates with `score` field, sorted descending

---

## Modified Files

1. `backend/app/services/gemini_service.py`
   - Added: `extract_spec()` (line 341)
   - Added: `rank_candidates()` (line 391)

2. `backend/app/services/kaggle_service.py`
   - Updated: `search_datasets()` (line 25)

3. `backend/app/services/huggingface_service.py`
   - Updated: `search_datasets()` (line 175)

4. `backend/app/services/dataset_download_service.py`
   - Updated: `search_all_sources()` (line 22)

---

## Example Output

### Input Query
```
"dibetes analussi"
```

### Step 1: extract_spec()
```json
{
  "fixed_query": "diabetes analysis",
  "keywords": ["diabetes", "analysis"]
}
```

### Step 2: search_apis()
```
Kaggle: 15 results (sorted by votes)
HuggingFace: 15 results (sorted by downloads, descending)
Total: 30 candidates
```

### Step 3: rank_candidates()
```json
[
  {
    "id": "...",
    "title": "Diabetes Dataset",
    "description": "...",
    "source": "Kaggle",
    "url": "https://www.kaggle.com/...",
    "downloads": 50000,
    "score": 0.92
  },
  ...
]
```

### Final Output: Top 5
```json
{
  "total_found": 30,
  "datasets": [top 5 ranked by score],
  "kaggle_count": 15,
  "huggingface_count": 15
}
```

---

## Testing Commands

### Test Query Optimization
```bash
curl -X POST http://localhost:8000/api/datasets/search-all \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "dibetes analussi", "optimize_query": true}'
```

**Expected:** Fixed query = "diabetes analysis"

### Test Kaggle Sort
Check logs for: `sort_by='votes'` and limit of 15 results

### Test HuggingFace Sort
Check logs for: `sort="downloads"`, `direction=-1`, and limit of 15 results

### Test Ranking
Check logs for: "Ranking candidates using embeddings..." and scores between 0-1

---

## Troubleshooting

### Issue: Gemini API Error
**Solution:** Falls back to original query (no typo fixing)

### Issue: No Ranking
**Solution:** Returns unranked results (sorted by download count)

### Issue: Empty Results
**Solution:** Check if Kaggle/HuggingFace APIs are configured

---

## Next Steps

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Test query: Use curl or Postman
3. Check logs: Verify "✓ Fixed query", "✓ Found X from Kaggle", "✓ Datasets ranked"
4. Verify output: Top 5 results should be ranked by relevance score

---

## Comparison: Before vs After

| Feature | Before | After (EXACT) |
|---------|--------|---------------|
| Query Fix Model | Various | `gemini-2.5-flash` |
| Kaggle Sort | `hottest` | `votes` ✅ |
| Kaggle Limit | 20 | 15 ✅ |
| HF Direction | Not specified | `-1` ✅ |
| Ranking Model | `text-embedding-004` | `text-embedding-004` ✅ |
| Query Task Type | `retrieval_query` | `retrieval_query` ✅ |
| Doc Task Type | `retrieval_document` | `retrieval_document` ✅ |

**Result:** 100% match with dataset.py implementation ✅

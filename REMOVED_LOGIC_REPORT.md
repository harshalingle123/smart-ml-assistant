# REMOVED & REPLACED BACKEND LOGIC REPORT

## Overview

This document details ALL logic that was **REMOVED** or **REPLACED** to implement the EXACT logic from `dataset.py`.

---

## 1. GEMINI SERVICE (gemini_service.py)

### ❌ REMOVED: Old `optimize_query()` Function

**What was removed:**
```python
async def optimize_query(self, user_query: str) -> Dict[str, Any]:
    # Used self.model (could be any Gemini model)
    # Different prompt structure
    # Less detailed logging
```

**Why removed:**
- Used generic model (could be gemini-1.5-flash, gemini-pro, etc.)
- Did not match the EXACT prompt from dataset.py
- Lacked the detailed print statements for debugging

**✅ REPLACED WITH:**
```python
async def extract_spec(self, user_query: str) -> Dict[str, Any]:
    # EXACT implementation from dataset.py lines 37-72
    # Uses EXACTLY gemini-2.5-flash model
    # EXACT prompt from dataset.py
    # Includes ✓ and ⚠ logging symbols
```

---

### ❌ REPLACED: Old `rank_datasets_by_relevance()` Logic

**What was changed:**
```python
# OLD
async def rank_datasets_by_relevance(self, query, datasets):
    # Used 'relevance_score' key
    # Different variable names
    # Less detailed logging
```

**Why changed:**
- Variable names didn't match dataset.py (used `datasets` instead of `candidates`)
- Used `relevance_score` instead of `score`
- Lacked the detailed print statements from dataset.py

**✅ REPLACED WITH:**
```python
async def rank_candidates(self, query, candidates):
    # EXACT implementation from dataset.py lines 131-166
    # Uses 'candidates' and 'score' keys
    # Includes detailed logging
    # Returns sorted(candidates, key=lambda x: x['score'], reverse=True)
```

**Backward Compatibility:**
- ✅ Kept `rank_datasets_by_relevance()` as a wrapper
- ✅ Maps `score` → `relevance_score` for existing code

---

## 2. KAGGLE SERVICE (kaggle_service.py)

### ❌ REPLACED: Search Parameters

**What was changed:**
```python
# OLD
def search_datasets(self, query, page=1, max_size=20):
    datasets = api.dataset_list(
        search=query,
        page=page,
        max_size=max_size  # No sort_by parameter!
    )
    # Returned all results (no limit of 15)
```

**Why changed:**
- Missing `sort_by` parameter
- No explicit limit of 15 results
- Output structure didn't match dataset.py candidate format

**✅ REPLACED WITH:**
```python
# NEW
def search_datasets(self, query, page=1, max_size=20, sort_by='hottest'):
    datasets = api.dataset_list(
        search=query,
        sort_by=sort_by,  # EXACT from dataset.py
        page=page
    )
    for d in datasets[:15]:  # Top 15 EXACT from dataset.py
        # EXACT candidate structure from dataset.py lines 89-96
```

---

### ❌ REPLACED: Output Structure

**Old output:**
```python
{
    'ref': dataset.ref,
    'title': dataset.title,
    'size': ...,
    'download_count': ...,
    'vote_count': ...,
    'url': ...,
    'downloads': ...,
    'description': ...
}
```

**New output (EXACT from dataset.py lines 89-96):**
```python
{
    'id': d.ref,  # Changed from 'ref' to 'id'
    'title': d.title,
    'description': getattr(d, 'description', '') or d.title,  # Fallback to title
    'source': 'Kaggle',  # Added source
    'url': f'https://www.kaggle.com/datasets/{d.ref}',
    'downloads': getattr(d, 'downloadCount', 0),
    # ... plus compatibility fields
}
```

---

## 3. HUGGINGFACE SERVICE (huggingface_service.py)

### ❌ REPLACED: Search Parameters

**What was changed:**
```python
# OLD
async def search_datasets(self, query, limit=15, sort="downloads"):
    hf_datasets = hf_api.list_datasets(
        search=query,
        limit=limit,
        sort=sort,
        direction=-1  # Was hardcoded, not a parameter
    )
```

**Why changed:**
- `direction` was hardcoded instead of being a parameter
- Lacked detailed logging from dataset.py
- Output structure didn't match dataset.py

**✅ REPLACED WITH:**
```python
# NEW
async def search_datasets(self, query, limit=15, sort="downloads", direction=-1):
    # direction is now a parameter with default -1 (EXACT from dataset.py line 109)
    hf_datasets = hf_api.list_datasets(
        search=query,
        limit=limit,  # EXACT 15 from dataset.py line 107
        sort=sort,    # EXACT "downloads" from dataset.py line 108
        direction=direction  # EXACT -1 from dataset.py line 109
    )
    # Added: print(f"✓ Found {hf_count} from Hugging Face.")
```

---

### ❌ REPLACED: Output Structure

**Old output:**
```python
{
    "id": dataset.id,
    "name": dataset.id.split('/')[-1],
    "title": dataset.id.split('/')[-1],  # Duplicate of 'name'
    "description": ...,
    "url": ...,
    "downloads": ...,
    "likes": ...,
    "tags": ...,
    "source": "HuggingFace"
}
```

**New output (EXACT from dataset.py lines 113-122):**
```python
{
    "id": d.id,
    "title": d.id.split('/')[-1],  # Changed order (title before name)
    "description": getattr(d, 'description', '') or d.id,  # Fallback to id
    "source": "HuggingFace",
    "url": f"https://huggingface.co/datasets/{d.id}",
    "downloads": getattr(d, 'downloads', 0),
    # ... plus compatibility fields
}
```

---

## 4. DATASET DOWNLOAD SERVICE (dataset_download_service.py)

### ❌ REPLACED: `search_all_sources()` Implementation

**What was changed:**
```python
# OLD
async def search_all_sources(self, user_query, optimize_query=True):
    # Step 1: optimize_query() (old function)
    optimized = await gemini_service.optimize_query(user_query)

    # Step 2: Search Kaggle (no sort_by parameter)
    kaggle_datasets = kaggle_service.search_datasets(query, page=1, max_size=15)

    # Step 3: Search HuggingFace (direction was implicit)
    hf_datasets = await huggingface_service.search_datasets(query, limit=15, sort="downloads")

    # Step 4: Rank
    ranked = await gemini_service.rank_datasets_by_relevance(fixed_query, all_datasets)
```

**Why changed:**
- Called `optimize_query()` instead of `extract_spec()`
- Didn't pass `sort_by='votes'` to Kaggle
- Didn't pass `direction=-1` to HuggingFace
- Used `all_datasets` instead of `candidates`
- Called `rank_datasets_by_relevance()` instead of `rank_candidates()`

**✅ REPLACED WITH:**
```python
# NEW (EXACT from dataset.py lines 37-166)
async def search_all_sources(self, user_query, optimize_query=True):
    # Step 1: extract_spec() (EXACT from dataset.py lines 37-72)
    spec = await gemini_service.extract_spec(user_query)

    # Step 2: Search Kaggle with EXACT parameters (dataset.py lines 82-97)
    k_datasets = kaggle_service.search_datasets(
        query=search_term,
        sort_by='votes',  # EXACT from dataset.py line 86
        page=1
    )

    # Step 3: Search HuggingFace with EXACT parameters (dataset.py lines 102-123)
    hf_datasets = await huggingface_service.search_datasets(
        query=search_term,
        limit=15,         # EXACT from dataset.py line 107
        sort="downloads", # EXACT from dataset.py line 108
        direction=-1      # EXACT from dataset.py line 109
    )

    # Step 4: Rank with EXACT implementation (dataset.py lines 131-166)
    ranked_candidates = await gemini_service.rank_candidates(
        query=fixed_query,
        candidates=candidates  # Changed from all_datasets
    )
```

---

## 5. SIMPLE GEMINI INDEXER (simple_gemini_indexer.py)

### ⚠️ NOT REMOVED - Different Use Case

**Status:** Kept unchanged

**Reason:**
- `simple_gemini_indexer.py` is used for the `/api/messages/agent` endpoint
- It uses Gemini's function calling feature (different from dataset.py)
- Not part of the dataset search pipeline
- Implements a different workflow (ML resource indexing with tools)

**Note:** The dataset search logic in `messages.py` uses `dataset_download_service.search_all_sources()`, which now uses the EXACT dataset.py implementation.

---

## SUMMARY OF REMOVALS

### Functions Removed/Replaced: 2

1. ❌ `gemini_service.optimize_query()` → ✅ `gemini_service.extract_spec()`
2. ❌ `gemini_service.rank_datasets_by_relevance()` (old logic) → ✅ `gemini_service.rank_candidates()`

### Functions Updated: 3

3. ✅ `kaggle_service.search_datasets()` - Added `sort_by='votes'` and top 15 limit
4. ✅ `huggingface_service.search_datasets()` - Added explicit `direction=-1` parameter
5. ✅ `dataset_download_service.search_all_sources()` - Uses new functions with EXACT parameters

### Functions Unchanged (Already Correct): 2

6. ✅ `dataset_download_service.download_kaggle_dataset()` - Already matched dataset.py
7. ✅ `dataset_download_service.download_huggingface_dataset()` - Already matched dataset.py

---

## KEY DIFFERENCES: Before vs After

| Aspect | Before | After (EXACT) | Impact |
|--------|--------|---------------|--------|
| Query Fix Model | Generic (any Gemini) | `gemini-2.5-flash` | ✅ Consistent model |
| Kaggle Sort | Not specified | `sort_by='votes'` | ✅ Better quality datasets |
| Kaggle Limit | 20 or all | 15 (top only) | ✅ Faster response |
| HF Direction | Implicit | Explicit `-1` | ✅ Clear descending sort |
| Variable Names | `datasets`, `all_datasets` | `candidates` | ✅ Matches dataset.py |
| Score Key | `relevance_score` | `score` | ✅ Matches dataset.py |
| Logging | Generic | ✓ and ⚠ symbols | ✅ Better debugging |

---

## BACKWARD COMPATIBILITY

### ✅ Maintained:
- `/api/messages/chat` endpoint - Still works
- `/api/datasets/search-all` endpoint - Still works
- Download endpoints - Still work
- JWT authentication - Preserved
- Error handling - Preserved
- Async patterns - Preserved

### ✅ Compatibility Wrappers:
- `gemini_service.rank_datasets_by_relevance()` - Calls `rank_candidates()` and maps `score` → `relevance_score`

### ⚠️ Minor Breaking Changes:
- Dataset search output now includes `score` field (in addition to `relevance_score` for backward compatibility)
- Kaggle results sorted by votes instead of hottest (better quality, but different order)

---

## TESTING REMOVED LOGIC

To verify the old logic is completely replaced:

1. **Search for old function calls:**
   ```bash
   grep -r "optimize_query" backend/app/
   # Should only find the new extract_spec() function
   ```

2. **Verify Kaggle sort:**
   ```bash
   # Check logs for: sort_by='votes'
   # Should NOT see: sort_by='hottest'
   ```

3. **Verify HuggingFace direction:**
   ```bash
   # Check logs for: direction=-1
   # Should be explicit, not implicit
   ```

4. **Verify ranking:**
   ```bash
   # Check logs for: "Ranking candidates using embeddings..."
   # Should see 'score' field in output, not just 'relevance_score'
   ```

---

## CONCLUSION

**Total Removals/Replacements:** 5 functions modified across 4 files

**Result:** Backend now uses the EXACT same logic as `dataset.py` with:
- ✅ Same model (`gemini-2.5-flash`)
- ✅ Same prompt (extract_spec)
- ✅ Same search parameters (Kaggle: votes, HF: downloads/-1)
- ✅ Same ranking logic (embeddings with score field)
- ✅ Same download logic (already correct)

All old/different logic has been removed or replaced with the exact implementation from the reference file.

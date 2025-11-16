# Database Migration Scripts

## Schema Field Name Inconsistency Fix

### Problem
Datasets in MongoDB had inconsistent field names:
- Some used `schema` field (correct)
- Some used `column_schema` field (incorrect/legacy)
- This caused frontend rendering failures on dataset detail pages

### Solution
1. Updated Pydantic models to use `schema` consistently
2. Updated all dataset creation endpoints
3. Created migration script to fix existing data

## Scripts

### 1. verify_schema_fields.py
**Purpose:** Check current state of schema fields in database

**Usage:**
```bash
cd backend
python -m app.scripts.verify_schema_fields
```

**Output:**
- Lists all datasets and their schema field status
- Shows counts of correct/incorrect/both/neither
- Indicates if migration is needed

### 2. migrate_column_schema.py
**Purpose:** Migrate `column_schema` → `schema` in all datasets

**Usage:**
```bash
cd backend
python -m app.scripts.migrate_column_schema
```

**What it does:**
- Finds all datasets with `column_schema` field
- Renames `column_schema` → `schema` (if schema doesn't exist)
- Removes `column_schema` (if both fields exist, keeps schema)
- Reports progress for each dataset

**Safety:**
- Non-destructive: Only renames/removes the legacy field
- Preserves all data
- Can be run multiple times safely

## Workflow

1. **Check current state:**
   ```bash
   python -m app.scripts.verify_schema_fields
   ```

2. **Run migration if needed:**
   ```bash
   python -m app.scripts.migrate_column_schema
   ```

3. **Verify migration succeeded:**
   ```bash
   python -m app.scripts.verify_schema_fields
   ```

   Should show: "✅ All datasets use correct 'schema' field!"

## Expected Results

### Before Migration
```
Total datasets: 2

❌ Melbourne House Prices (ID: 6919c6d42973b52bab4a8cb2)
   Has 'column_schema' field: 21 items

✅ Cancer_Data.csv (ID: 6919c7692973b52bab4a8cb3)
   Has 'schema' field: 33 items

SUMMARY
✅ Correct ('schema' only):         1
❌ Incorrect ('column_schema' only): 1
```

### After Migration
```
Total datasets: 2

✅ Melbourne House Prices (ID: 6919c6d42973b52bab4a8cb2)
   Has 'schema' field: 21 items

✅ Cancer_Data.csv (ID: 6919c7692973b52bab4a8cb3)
   Has 'schema' field: 33 items

SUMMARY
✅ Correct ('schema' only):         2
❌ Incorrect ('column_schema' only): 0

✅ All datasets use correct 'schema' field!
```

## Files Modified

1. **backend/app/models/mongodb_models.py** (line 115)
   - Changed: `column_schema: Optional[List[Any]]` → `schema: Optional[List[Any]]`
   - Removed confusing alias/serialization_alias

2. **backend/app/routers/datasets.py**
   - Line 327: Upload endpoint uses `schema=...`
   - Line 691: HuggingFace endpoint uses `schema=...`
   - Line 553: Kaggle endpoint already correct

3. **backend/app/schemas/dataset_schemas.py**
   - Already correct (uses `schema`)

## Testing

After migration, test:

1. **View dataset list:**
   - Both datasets should appear

2. **View broken dataset detail page:**
   - Navigate to: `/datasets/6919c6d42973b52bab4a8cb2`
   - Should now show schema with 21 columns

3. **Upload new dataset:**
   - Upload a CSV file
   - Verify it uses `schema` field (not `column_schema`)

4. **Add Kaggle dataset:**
   - Add a dataset from Kaggle
   - Verify it uses `schema` field

## Notes

- All new datasets will automatically use `schema` field
- Migration is one-time operation
- Safe to run migration multiple times
- Frontend expects `schema` field (via camelCase: `schema`)

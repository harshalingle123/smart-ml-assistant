# Quick Fix Steps for "Failed to Fetch" Error

## The Problem
Clicking on Datasets tab shows "failed to fetch" error.

## The Fix (Already Applied)
✅ Added `VITE_API_URL=http://localhost:8000` to `frontend/client/.env`

## What You Need to Do NOW

### Step 1: Restart the Frontend Dev Server

**IMPORTANT**: The .env file changes only take effect after restarting the dev server.

1. Go to the terminal running the frontend
2. Press `Ctrl+C` to stop it
3. Run `npm run dev` again

```bash
cd frontend
# Press Ctrl+C
npm run dev
```

### Step 2: Test the Fix

1. Open browser to `http://localhost:5173`
2. Login (if not already logged in)
3. Click on "Datasets" tab
4. Should now show the datasets page (empty or with your datasets)

### Alternative: Automated Test

Run the E2E test to verify everything works:
```bash
python test_datasets_e2e.py
```

Expected output: `ALL TESTS PASSED!`

## That's It!

The backend is already running correctly. The issue was just the missing frontend environment variable.

After restarting the frontend dev server, the Datasets tab will work perfectly.

---

**Need help?** Check `FIX_DATASETS_TAB_GUIDE.md` for detailed troubleshooting.

# 🚀 Quick Start Guide - Kaggle & HuggingFace Integration

## ⚡ Get Started in 5 Minutes

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

**New dependency added:**
- `huggingface_hub>=0.20.0` (for HuggingFace dataset downloads)

### 2. Set Environment Variables

Edit `backend/.env` and add:

```env
# HuggingFace Token (NEW - REQUIRED)
HF_TOKEN=hf_your_token_here

# Kaggle Credentials (Already configured, but verify)
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

# Google Gemini API Key (Already configured, but verify)
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
```

**Where to get tokens:**

🔑 **HuggingFace Token:**
1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Give it a name (e.g., "smart-ml-assistant")
4. Set type to "Read"
5. Copy the token (starts with `hf_`)

🔑 **Kaggle API Key:**
1. Go to https://www.kaggle.com/settings/account
2. Scroll to "API" section
3. Click "Create New Token"
4. Download `kaggle.json`
5. Copy username and key to `.env`

🔑 **Google Gemini API Key:**
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### 3. Test the Integration

**Option A: Use the Test Script**
```bash
# Make sure backend server is running
cd backend
python -m uvicorn app.main:app --reload

# In another terminal, run the test
cd ..
python test_integration.py
```

**Option B: Manual API Test**
```python
import requests

# 1. Login
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"email": "your_email@example.com", "password": "your_password"}
)
token = response.json()["access_token"]

# 2. Test enhanced search
search = requests.post(
    "http://localhost:8000/api/datasets/search-all",
    headers={"Authorization": f"Bearer {token}"},
    json={"query": "sentiment analysis", "optimize_query": True}
)

print(search.json())
```

### 4. Use in Chat

**Start a conversation:**
```bash
POST /api/messages/chat
{
  "chat_id": "your_chat_id",
  "content": "Find me datasets for house price prediction",
  "role": "user"
}
```

**Expected Response:**
```
I found 20 datasets for your query "house price prediction":

Top 5 Recommendations:
1. House Prices Dataset (Kaggle)
   - Relevance: 98.45%
   - Downloads: 50,000
   ...

Source Breakdown:
- Kaggle: 13 datasets
- HuggingFace: 7 datasets

Would you like to download any of these?
```

---

## 🎯 What's New

### New API Endpoints

1. **Enhanced Search**
   ```
   POST /api/datasets/search-all
   ```
   - Searches both Kaggle & HuggingFace
   - Fixes typos automatically
   - Ranks by semantic relevance

2. **Download Dataset**
   ```
   POST /api/datasets/download-dataset
   ```
   - Download from Kaggle or HuggingFace
   - Automatic extraction/unpacking

3. **Batch Download**
   ```
   POST /api/datasets/download-multiple
   ```
   - Download multiple datasets at once

### Enhanced Chat Features

- ✅ Automatic typo correction ("dibetes" → "diabetes")
- ✅ Semantic ranking with relevance scores
- ✅ Combined Kaggle + HuggingFace results
- ✅ Source breakdown in responses

---

## 🧪 Quick Tests

### Test 1: Query Optimization
```python
# Query with typos
query = "dibetes predction santiment"

# System automatically fixes to:
# "diabetes prediction sentiment"
```

### Test 2: Multi-Source Search
```python
# Searches both platforms
# - Kaggle: 12 datasets found
# - HuggingFace: 8 datasets found
# - Total: 20 datasets, ranked by relevance
```

### Test 3: Semantic Ranking
```python
# Query: "house prices"
# Top result: "House Prices Dataset" - 98.45% relevance
# 2nd result: "Real Estate Prices" - 94.32% relevance
# 3rd result: "Housing Market Data" - 91.28% relevance
```

---

## 📂 Project Structure

```
smart-ml-assistant/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py (✅ Added HF_TOKEN)
│   │   ├── services/
│   │   │   ├── huggingface_service.py (✅ Enhanced)
│   │   │   ├── gemini_service.py (✅ Enhanced)
│   │   │   ├── kaggle_service.py (existing)
│   │   │   └── dataset_download_service.py (✅ NEW)
│   │   └── routers/
│   │       ├── datasets.py (✅ Enhanced)
│   │       └── messages.py (✅ Enhanced)
│   └── requirements.txt (✅ Updated)
├── INTEGRATION_GUIDE.md (✅ NEW - Full docs)
├── INTEGRATION_SUMMARY.md (✅ NEW - Summary)
├── QUICKSTART.md (✅ NEW - This file)
└── test_integration.py (✅ NEW - Test suite)
```

---

## 🔍 Verify Installation

Run this to verify all components are working:

```python
# verify_setup.py
import os
from app.core.config import settings
from app.services.kaggle_service import kaggle_service
from app.services.huggingface_service import huggingface_service
from app.services.gemini_service import gemini_service

print("🔍 Checking Configuration...")

# Check HuggingFace
if settings.HF_TOKEN:
    print("✅ HF_TOKEN configured")
else:
    print("❌ HF_TOKEN missing - Add to .env")

# Check Kaggle
if kaggle_service.is_configured:
    print("✅ Kaggle configured")
else:
    print("❌ Kaggle not configured - Add KAGGLE_USERNAME and KAGGLE_KEY")

# Check Gemini
if gemini_service.is_available():
    print("✅ Gemini configured")
else:
    print("❌ Gemini not configured - Add GOOGLE_GEMINI_API_KEY")

print("\n✨ Setup verification complete!")
```

---

## 🐛 Common Issues

### Issue: "Module not found: huggingface_hub"
```bash
pip install huggingface_hub>=0.20.0
```

### Issue: "HF_TOKEN not found"
```bash
# Add to backend/.env
HF_TOKEN=hf_your_token_here
```

### Issue: "Kaggle authentication failed"
```bash
# Verify in backend/.env
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key
```

---

## 📞 Support

- **Full Documentation:** See `INTEGRATION_GUIDE.md`
- **Summary:** See `INTEGRATION_SUMMARY.md`
- **Test Suite:** Run `test_integration.py`

---

## ✅ Checklist

Before deploying:

- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Set `HF_TOKEN` in `.env`
- [ ] Verify `KAGGLE_USERNAME` and `KAGGLE_KEY`
- [ ] Verify `GOOGLE_GEMINI_API_KEY`
- [ ] Run test script (`python test_integration.py`)
- [ ] Test in chat interface
- [ ] Verify downloads work
- [ ] Check logs for errors

---

## 🎉 You're Ready!

The integration is complete and ready to use. Start the server and test with:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Then try asking in chat: **"Find me datasets for sentiment analysis"**

Enjoy your enhanced dataset search with AI-powered typo correction and semantic ranking! 🚀

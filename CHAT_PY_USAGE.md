# How to Use chat.py

## Overview
`chat.py` is a standalone Python script that demonstrates the dataset search and download functionality using:
- **Google Gemini AI** - For query optimization and semantic ranking
- **Kaggle API** - For searching Kaggle datasets
- **HuggingFace API** - For searching HuggingFace datasets

## Prerequisites

### 1. Install Required Packages
```bash
pip install google-generativeai huggingface_hub kaggle scikit-learn numpy
```

### 2. Set Up API Credentials

#### Google Gemini API Key
1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set environment variable:
```bash
# Windows (Command Prompt)
set GOOGLE_API_KEY=your-gemini-api-key-here

# Windows (PowerShell)
$env:GOOGLE_API_KEY="your-gemini-api-key-here"

# Linux/Mac
export GOOGLE_API_KEY="your-gemini-api-key-here"
```

#### HuggingFace Token
1. Get your token from [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Set environment variable:
```bash
# Windows (Command Prompt)
set HF_TOKEN=your-huggingface-token-here

# Windows (PowerShell)
$env:HF_TOKEN="your-huggingface-token-here"

# Linux/Mac
export HF_TOKEN="your-huggingface-token-here"
```

#### Kaggle API Credentials
1. Go to [Kaggle Account Settings](https://www.kaggle.com/settings)
2. Click "Create New API Token" - this downloads `kaggle.json`
3. Place `kaggle.json` in one of these locations:
   - **Windows**: `C:\Users\YourUsername\.kaggle\kaggle.json`
   - **Linux/Mac**: `~/.kaggle/kaggle.json`
   - **Or**: Current directory where you run `chat.py`

The `kaggle.json` file should look like:
```json
{
  "username": "your-kaggle-username",
  "key": "your-kaggle-api-key"
}
```

## Running the Script

### Option 1: Interactive Mode (Full chat.py)
```bash
python chat.py
```

This will:
1. Prompt you for a dataset search query
2. Optimize your query using Gemini AI
3. Search both Kaggle and HuggingFace
4. Rank results by semantic relevance
5. Display top 5 recommendations with URLs
6. Allow you to download selected datasets

**Example:**
```
Enter your dataset requirement: diabetes prediction dataset

Analyzing query: 'diabetes prediction dataset'...
✓ Fixed query: 'diabetes prediction dataset'
✓ Keywords: ['diabetes', 'prediction', 'dataset']

Searching for: 'diabetes prediction dataset'...
✓ Found 5 from Kaggle.
✓ Found 5 from Hugging Face.

Ranking candidates using embeddings...

🏆 TOP 5 RECOMMENDED DATASETS
==============================================================

1. [Kaggle] Diabetes Dataset
   Relevance Score: 0.8945
   Downloads: 12,500
   URL: https://www.kaggle.com/datasets/joshuaswords/diabetes-dataset

2. [HuggingFace] diabetes-prediction
   Relevance Score: 0.8723
   Downloads: 8,500
   URL: https://huggingface.co/datasets/community/diabetes-prediction

...

📦 DOWNLOAD OPTIONS
Would you like to download any of these datasets?
Enter the numbers separated by commas (e.g., 1,3,5) or 'all' for all datasets
Enter 'n' or 'no' to skip downloading

Your selection: _
```

### Option 2: Test Mode (test_chat_simple.py)
```bash
python test_chat_simple.py
```

This runs automated tests without requiring API authentication:
- Tests URL format generation
- Verifies response structure
- Demonstrates frontend integration

## Troubleshooting

### Error: "Could not find kaggle.json"
**Solution**: Place `kaggle.json` in the correct location (see Kaggle API Credentials above)

### Error: "Please set GOOGLE_API_KEY environment variable"
**Solution**: Set the environment variable before running the script:
```bash
# Windows
set GOOGLE_API_KEY=your-api-key

# Linux/Mac
export GOOGLE_API_KEY=your-api-key
```

### Error: "Please set HF_TOKEN environment variable"
**Solution**: Set the HuggingFace token:
```bash
# Windows
set HF_TOKEN=your-token

# Linux/Mac
export HF_TOKEN=your-token
```

### Error: Unicode/Encoding Issues (Windows)
If you see encoding errors with emojis, use `test_chat_simple.py` instead, which doesn't use emojis.

## What This Demonstrates

This script implements the exact logic that powers the Smart ML Assistant's dataset search feature:

1. **Query Optimization** - Uses Gemini to fix typos and extract meaningful keywords
2. **Multi-Source Search** - Searches both Kaggle and HuggingFace simultaneously
3. **Semantic Ranking** - Uses AI embeddings to rank datasets by relevance
4. **URL Generation** - Creates direct links to dataset pages:
   - Kaggle: `https://www.kaggle.com/datasets/{ref}`
   - HuggingFace: `https://huggingface.co/datasets/{id}`
5. **Interactive Download** - Allows downloading selected datasets

## Integration with Main Application

The main Smart ML Assistant application uses this same logic in:
- **Backend**: `backend/app/services/dataset_download_service.py`
- **Frontend**: Dataset cards with download buttons
- **API**: `/api/messages/chat` and `/api/messages/agent` endpoints

The URLs generated here are the same URLs displayed in the frontend download buttons.

## Example Queries to Try

- "diabetes prediction dataset"
- "sentiment analysis twitter"
- "house price prediction"
- "image classification cifar"
- "customer churn prediction"
- "stock market prediction"
- "text classification nlp"

## Notes

- The script requires internet connection for API calls
- Downloading large datasets may take time
- Free tier API limits apply for Gemini API
- Kaggle and HuggingFace have their own rate limits

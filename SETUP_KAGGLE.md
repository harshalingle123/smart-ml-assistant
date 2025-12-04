# Kaggle API Setup Guide

## Step 1: Get Your Kaggle API Credentials

1. Go to [Kaggle Account Settings](https://www.kaggle.com/settings)
2. Scroll down to the "API" section
3. Click **"Create New API Token"**
4. This will download a file named `kaggle.json`

## Step 2: Place kaggle.json in the Correct Location

### Option A: Windows User Directory (Recommended)
```powershell
# Create the .kaggle directory if it doesn't exist
mkdir C:\Users\Harshal\.kaggle

# Copy kaggle.json to the directory
# Download kaggle.json from Kaggle, then move it:
move C:\Users\Harshal\Downloads\kaggle.json C:\Users\Harshal\.kaggle\kaggle.json
```

### Option B: Project Directory
```powershell
# Copy kaggle.json to the project root
copy C:\Users\Harshal\Downloads\kaggle.json E:\Startup\smart-ml-assistant\kaggle.json
```

### Option C: Set Environment Variables
Instead of using kaggle.json, you can set environment variables:

```powershell
# PowerShell
$env:KAGGLE_USERNAME="your-kaggle-username"
$env:KAGGLE_KEY="your-kaggle-key"

# Or Command Prompt
set KAGGLE_USERNAME=your-kaggle-username
set KAGGLE_KEY=your-kaggle-key
```

## Step 3: Verify Setup

Run this command to test:
```powershell
kaggle datasets list --search diabetes
```

If it works, you'll see a list of datasets!

## Step 4: Set Other Required API Keys

### Google Gemini API Key
```powershell
# Get your API key from: https://makersuite.google.com/app/apikey
$env:GOOGLE_API_KEY="your-gemini-api-key"
```

### HuggingFace Token
```powershell
# Get your token from: https://huggingface.co/settings/tokens
$env:HF_TOKEN="your-huggingface-token"
```

## Step 5: Run the Full Test

```powershell
python chat.py
```

## Quick Test (No APIs Required)

If you just want to test the URL logic without setting up APIs:
```powershell
python test_chat_simple.py
```

This will verify that:
- URLs are formatted correctly
- Backend generates proper responses
- Frontend can use the URLs

## Troubleshooting

### Error: "Could not find kaggle.json"
**Solution**: Make sure kaggle.json is in one of these locations:
- `C:\Users\Harshal\.kaggle\kaggle.json` (Windows)
- `E:\Startup\smart-ml-assistant\kaggle.json` (Project root)
- Or set KAGGLE_USERNAME and KAGGLE_KEY environment variables

### Error: "Unauthorized"
**Solution**: Regenerate your API token on Kaggle and replace the old kaggle.json

### Error: kaggle.json has wrong permissions
**Solution**: On Windows, this is usually not an issue. On Linux/Mac:
```bash
chmod 600 ~/.kaggle/kaggle.json
```

## What kaggle.json Looks Like

```json
{
  "username": "your-kaggle-username",
  "key": "1234567890abcdef1234567890abcdef"
}
```

Replace with your actual credentials from Kaggle.

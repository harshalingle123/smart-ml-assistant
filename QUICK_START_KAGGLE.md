# 🚀 Quick Start: Enable Kaggle Dataset Download

Follow these steps to enable the "Download & Inspect Dataset" feature:

## 📋 Steps (5 minutes)

### 1. Get Your Kaggle API Token

1. Go to: https://www.kaggle.com/settings
2. Scroll to **"API"** section
3. Click **"Create New Token"**
4. A file called `kaggle.json` will download

### 2. Open kaggle.json

Open the downloaded file. It looks like this:

```json
{
  "username": "johndoe",
  "key": "abc123def456ghi789jkl012mno345"
}
```

### 3. Add to Your .env File

**Option A: If you have `backend/.env` file**

Open `backend/.env` and add these lines at the end:

```env
KAGGLE_USERNAME=johndoe
KAGGLE_KEY=abc123def456ghi789jkl012mno345
```

**Option B: If you don't have .env file**

Copy `.env.example` to `.env`:

```bash
cd backend
copy .env.example .env
```

Then edit `.env` and update the Kaggle credentials.

### 4. Restart Backend

```bash
cd backend
# Stop the server (Ctrl+C if running)
python -m uvicorn app.main:app --reload
```

### 5. Test It! ✅

1. Go to Smart ML Assistant
2. Ask: "I need house price datasets"
3. Click "Add to My Datasets"
4. Go to "Datasets" tab
5. Click "View Details" on the dataset
6. Click "Download & Inspect Dataset"

**It should work now!** 🎉

## 🔍 What You'll See

After inspection completes, you'll see:

- ✅ **Full row/column counts** (e.g., 1,460 rows, 80 columns)
- ✅ **Complete schema** with data types
- ✅ **Sample data** (first 20 rows)
- ✅ **Auto-detected target column** (e.g., "SalePrice")

## ❓ Still Not Working?

### Error: "Kaggle API is not configured"

- Check your `.env` file has both `KAGGLE_USERNAME` and `KAGGLE_KEY`
- Make sure there are no extra spaces or quotes
- **Restart the backend** (important!)

### Error: "401 Unauthorized"

- Your API key might be expired
- Go back to Kaggle settings and generate a new token
- Update your `.env` file with new credentials

### Check Your Credentials

Print your environment variables to verify:

```bash
# In backend directory
python -c "import os; print('Username:', os.getenv('KAGGLE_USERNAME')); print('Key:', 'Set' if os.getenv('KAGGLE_KEY') else 'Not Set')"
```

Should output:
```
Username: johndoe
Key: Set
```

## 🔒 Security

**IMPORTANT:** Never commit your `.env` file or `kaggle.json` to Git!

Your `.gitignore` already includes:
```
.env
kaggle.json
```

## 💡 Pro Tips

- **Without Kaggle API:** You can still add datasets as "linked" and view them on Kaggle.com
- **With Kaggle API:** You get full inspection, schema, and sample data locally
- **Privacy:** Your API key stays on your server, never sent to frontend

Need help? Check `KAGGLE_API_SETUP.md` for detailed troubleshooting.

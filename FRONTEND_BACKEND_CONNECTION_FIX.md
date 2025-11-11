# 🔧 Fix: Frontend-Backend Connection Issue

## Error: "Failed to fetch"

This error occurs when the frontend cannot communicate with the backend API.

---

## 🎯 Root Causes Identified

### 1. Hardcoded Localhost URL ❌
The `auth.ts` file was hardcoded to `http://localhost:8000`, which works locally but fails in production.

### 2. Missing Environment Variable ❌
The frontend needs the `VITE_API_URL` environment variable set in Render to know where the backend is deployed.

### 3. CORS Not Configured ❌
The backend's CORS settings need to include your frontend URL.

---

## ✅ SOLUTION: Fix the Connection (3 Steps)

### Step 1: Add VITE_API_URL to Frontend Service in Render

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click on**: `smart-ml-frontend` service
3. **Click**: **Environment** (left sidebar)
4. **Add new environment variable**:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://smart-ml-backend.onrender.com`

   ⚠️ **Replace with your actual backend URL!**

   To find your backend URL:
   - Go to `smart-ml-backend` service
   - Copy the URL at the top (e.g., `https://smart-ml-backend-xxxx.onrender.com`)

5. **Click**: **Save Changes**
6. Frontend will **redeploy automatically** (takes 5-10 minutes)

---

### Step 2: Update CORS_ORIGINS in Backend Service

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click on**: `smart-ml-backend` service
3. **Click**: **Environment** (left sidebar)
4. **Find**: `CORS_ORIGINS` variable
5. **Click**: **Edit** (pencil icon)
6. **Set value to your frontend URL**:
   ```
   https://smart-ml-frontend.onrender.com
   ```

   ⚠️ **Replace with your actual frontend URL!**

   To find your frontend URL:
   - Go to `smart-ml-frontend` service
   - Copy the URL at the top (e.g., `https://smart-ml-frontend-xxxx.onrender.com`)

7. **Click**: **Save Changes**
8. Backend will **redeploy automatically** (takes 2-3 minutes)

---

### Step 3: Redeploy Frontend with Latest Code

The code fix has been pushed to GitHub. You need to redeploy the frontend:

1. **Go to**: `smart-ml-frontend` service in Render
2. **Click**: **Manual Deploy** dropdown (top right)
3. **Select**: **Clear build cache & deploy**
4. Wait for deployment to complete (5-10 minutes)

---

## 🧪 Test the Connection

After both services have redeployed:

### 1. Test Backend Health
Visit your backend URL with `/health`:
```
https://smart-ml-backend.onrender.com/health
```
Should return:
```json
{"status": "healthy"}
```

### 2. Test Frontend
Visit your frontend URL:
```
https://smart-ml-frontend.onrender.com
```

### 3. Test Login
1. Go to the Login page
2. Try to login or register
3. Should work without "Failed to fetch" error!

---

## 📋 Quick Reference: Environment Variables

### Backend Service Environment Variables

| Variable | Example Value |
|----------|---------------|
| `MONGO_URI` | `mongodb+srv://Harshal:Harshal%40123@cluster0...` |
| `SECRET_KEY` | `rRSooDw_EKXFTyH9QGx6LNTWUoHWdz2UeEu1IwBGnCs` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `ENVIRONMENT` | `production` |
| `CORS_ORIGINS` | `https://smart-ml-frontend.onrender.com` ⚠️ |

### Frontend Service Environment Variables

| Variable | Example Value |
|----------|---------------|
| `NODE_VERSION` | `20.11.0` |
| `VITE_API_URL` | `https://smart-ml-backend.onrender.com` ⚠️ |

⚠️ **Important**: Replace with your actual Render URLs!

---

## 🔍 How to Find Your Render URLs

### Backend URL:
1. Go to Render Dashboard
2. Click on `smart-ml-backend`
3. Copy the URL from the top of the page
4. Format: `https://smart-ml-backend-xxxxx.onrender.com`

### Frontend URL:
1. Go to Render Dashboard
2. Click on `smart-ml-frontend`
3. Copy the URL from the top of the page
4. Format: `https://smart-ml-frontend-xxxxx.onrender.com`

---

## 🐛 Troubleshooting

### Still Getting "Failed to fetch"?

**Check 1: Verify VITE_API_URL is set**
1. Go to `smart-ml-frontend` → Environment
2. Ensure `VITE_API_URL` exists with your backend URL
3. If missing, add it and wait for redeploy

**Check 2: Verify CORS_ORIGINS is set**
1. Go to `smart-ml-backend` → Environment
2. Ensure `CORS_ORIGINS` has your frontend URL
3. Should match exactly: `https://smart-ml-frontend.onrender.com`

**Check 3: Check Browser Console**
1. Open your frontend in browser
2. Press F12 to open Developer Tools
3. Go to Console tab
4. Look for error messages:
   - **CORS error**: Backend CORS_ORIGINS not set correctly
   - **404 Not Found**: Backend URL wrong in VITE_API_URL
   - **Network error**: Backend might be down

**Check 4: Test Backend Directly**
Visit: `https://smart-ml-backend.onrender.com/health`
- If it doesn't load → Backend deployment failed
- If it returns `{"status": "healthy"}` → Backend is working

**Check 5: Clear Build Cache**
Sometimes old builds are cached:
1. Go to `smart-ml-frontend` service
2. Click **Manual Deploy** → **Clear build cache & deploy**
3. Wait for fresh deployment

---

## 📝 What Was Fixed in the Code

### File: `frontend/client/src/lib/auth.ts`

**Before (❌ Wrong):**
```typescript
const BASE_URL = "http://localhost:8000";
```

**After (✅ Fixed):**
```typescript
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

Now it reads from environment variable, falling back to localhost for local development.

### File: `render.yaml`

**Added VITE_API_URL to frontend service:**
```yaml
envVars:
  - key: NODE_VERSION
    value: 20.11.0
  - key: VITE_API_URL
    sync: false  # Will prompt during deployment
```

---

## ⚡ Quick Fix Checklist

Use this checklist to ensure everything is configured:

### Backend Configuration
- [ ] `MONGO_URI` is set with encoded password (`%40` not `@`)
- [ ] `SECRET_KEY` is set
- [ ] `CORS_ORIGINS` is set to your frontend URL
- [ ] Backend health check works: `/health` returns `{"status": "healthy"}`
- [ ] Backend logs show "Application startup complete"

### Frontend Configuration
- [ ] `VITE_API_URL` is set to your backend URL
- [ ] Frontend has been redeployed with latest code
- [ ] Frontend loads without errors
- [ ] Browser console shows no CORS errors

### Testing
- [ ] Can access frontend URL
- [ ] Can access backend `/health` endpoint
- [ ] Login/Register works without "Failed to fetch"
- [ ] Can create chats
- [ ] Can upload datasets

---

## 🎯 Expected Configuration

After following this guide, your services should be configured like this:

### Backend Environment (`smart-ml-backend`)
```
MONGO_URI=mongodb+srv://Harshal:Harshal%40123@cluster0.hguakgq.mongodb.net/smartml?appName=Cluster0
SECRET_KEY=rRSooDw_EKXFTyH9QGx6LNTWUoHWdz2UeEu1IwBGnCs
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
CORS_ORIGINS=https://smart-ml-frontend.onrender.com  ← Your frontend URL
```

### Frontend Environment (`smart-ml-frontend`)
```
NODE_VERSION=20.11.0
VITE_API_URL=https://smart-ml-backend.onrender.com  ← Your backend URL
```

---

## 🚨 Common Mistakes to Avoid

1. ❌ **Using `http://` instead of `https://`** in URLs
   - Render uses HTTPS by default
   - Always use `https://` prefix

2. ❌ **Including trailing slash in URLs**
   - WRONG: `https://smart-ml-backend.onrender.com/`
   - RIGHT: `https://smart-ml-backend.onrender.com`

3. ❌ **Not redeploying after adding environment variables**
   - Environment changes trigger auto-redeploy
   - Wait for deployment to complete before testing

4. ❌ **Using wrong service URLs**
   - Each Render service has a unique URL
   - Copy-paste from Render dashboard, don't guess

5. ❌ **Forgetting to update CORS_ORIGINS**
   - Backend MUST allow frontend origin
   - Must match exactly (including protocol)

---

## 📞 Still Need Help?

If you're still experiencing issues:

1. **Check Render Logs**:
   - Backend → Logs tab
   - Frontend → Logs tab
   - Look for specific error messages

2. **Verify URLs**:
   - Ensure backend and frontend URLs are correct
   - Test each service independently

3. **Test Locally First**:
   - Clone the repo
   - Run backend locally
   - Point frontend to local backend
   - Verify it works

4. **Contact Support**:
   - Render Community: https://community.render.com
   - Check Render docs: https://render.com/docs

---

## ✅ Summary

The "Failed to fetch" error happens because:
1. Frontend didn't know where backend is deployed
2. Backend didn't allow frontend origin (CORS)

**Solution:**
1. Set `VITE_API_URL` in frontend environment
2. Set `CORS_ORIGINS` in backend environment
3. Redeploy both services with latest code

**Result:** Frontend ↔️ Backend connection works! 🎉

---

**Your Action Items:**
1. Add `VITE_API_URL` to frontend environment in Render
2. Update `CORS_ORIGINS` in backend environment in Render
3. Redeploy frontend with "Clear build cache & deploy"
4. Test login/register functionality

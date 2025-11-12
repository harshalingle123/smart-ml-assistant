# Fix CORS Error for Custom Domain (darshix.com)

## The Problem
After registering your custom domain, you're seeing these errors:
```
Access to fetch at 'https://smart-ml-backend.onrender.com/api/auth/login'
from origin 'https://darshix.com' has been blocked by CORS policy
```

This happens because your backend is configured to only accept requests from localhost, not from your production domain.

## The Solution - Update CORS_ORIGINS on Render

### Step 1: Go to Render Dashboard
1. Visit: https://dashboard.render.com
2. Find and click on: **smart-ml-backend**

### Step 2: Update Environment Variable
1. Click **Environment** in the left sidebar
2. Find the variable: `CORS_ORIGINS`
3. Click **Edit** (pencil icon)
4. Replace the current value with:
   ```
   https://darshix.com
   ```
5. Click **Save Changes**

### Step 3: Wait for Redeploy
- Render will automatically redeploy (2-3 minutes)
- Watch the **Logs** tab for: `Application startup complete`

### Step 4: Test Your Site
1. Visit: https://darshix.com
2. Try logging in or registering
3. CORS errors should be gone!

---

## Multiple Origins (Optional)

If you want to allow requests from multiple domains:

```
https://darshix.com,https://smart-ml-frontend.onrender.com,http://localhost:5173
```

**Note:** Separate domains with commas, NO SPACES

---

## What We Changed

### Before:
```
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### After:
```
CORS_ORIGINS=https://darshix.com
```

This tells your backend: "Accept requests from https://darshix.com"

---

## Still Having Issues?

### 1. Check if backend is running
- Visit: https://smart-ml-backend.onrender.com/health
- Should return: `{"status":"healthy"}`

### 2. Verify the environment variable
- Go to: smart-ml-backend → Environment
- Confirm CORS_ORIGINS shows: `https://darshix.com`
- Make sure there are NO spaces before or after the URL

### 3. Clear browser cache
```bash
# Chrome/Edge: Press Ctrl+Shift+Delete
# Select "Cached images and files"
# Click "Clear data"
```

### 4. Check browser console
- Press F12 in your browser
- Go to Console tab
- Look for any remaining CORS errors
- Take a screenshot if errors persist

---

## Quick Reference

**Value to Copy/Paste:**
```
https://darshix.com
```

**Where to Paste:**
1. Render Dashboard → smart-ml-backend
2. Environment → CORS_ORIGINS → Edit
3. Paste value → Save Changes
4. Wait 2-3 minutes

Done!

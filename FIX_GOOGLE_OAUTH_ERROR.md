# Fix Google OAuth Error: "Access blocked: Authorization Error"

## Error Details
```
Access blocked: Authorization Error
harshalingle517@gmail.com
no registered origin
Error 401: invalid_client
```

## Root Cause
Your Google OAuth Client ID (`204472130909-btqroif1ao4o8quc0tg9gsv6vecl38ca`) doesn't have `http://localhost:5175` registered as an authorized origin.

---

## SOLUTION 1: Register the Origin (Recommended)

### Step-by-Step Instructions:

#### 1. Open Google Cloud Console
Go to: https://console.cloud.google.com/

#### 2. Navigate to Credentials
1. Click on the menu (☰) → **APIs & Services** → **Credentials**
2. Or use direct link: https://console.cloud.google.com/apis/credentials

#### 3. Find Your OAuth Client
Look for the OAuth 2.0 Client ID with:
- Client ID: `204472130909-btqroif1ao4o8quc0tg9gsv6vecl38ca`
- Click on it (pencil icon or name)

#### 4. Add Authorized JavaScript Origins
Scroll to **"Authorized JavaScript origins"** section.

**Click "+ ADD URI"** and add each of these (one at a time):

```
http://localhost:5175
http://localhost:5174
http://localhost:5173
http://localhost:3000
http://localhost:8000
```

**IMPORTANT NOTES:**
- ❌ Don't include trailing slash: `http://localhost:5175/` (WRONG)
- ✅ Correct format: `http://localhost:5175` (CORRECT)
- ❌ Don't use https for localhost
- ✅ Use exact port numbers

#### 5. Add Authorized Redirect URIs
Scroll to **"Authorized redirect URIs"** section.

**Click "+ ADD URI"** and add each of these:

```
http://localhost:5175
http://localhost:5174
http://localhost:5173
http://localhost:8000/api/auth/google/callback
```

#### 6. Save Changes
1. Click **SAVE** button at the bottom
2. Wait for confirmation message
3. **WAIT 1-2 MINUTES** for changes to propagate

#### 7. Test Again
1. Close all browser windows
2. Open a new browser window (or use Incognito/Private mode)
3. Go to: `http://localhost:5175/login`
4. Click "Continue with Google"
5. It should work now!

---

## SOLUTION 2: Create New OAuth Client (If Solution 1 Fails)

If you can't edit the existing client or it doesn't work, create a new one:

### Step 1: Create New OAuth 2.0 Client ID

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click **"+ CREATE CREDENTIALS"**
3. Select **"OAuth client ID"**
4. Choose **"Web application"**

### Step 2: Configure New Client

**Name:** `DualQueryIntelligence Local`

**Authorized JavaScript origins:**
```
http://localhost:5175
http://localhost:5174
http://localhost:5173
http://localhost:3000
http://localhost:8000
```

**Authorized redirect URIs:**
```
http://localhost:5175
http://localhost:5174
http://localhost:5173
http://localhost:8000/api/auth/google/callback
```

### Step 3: Get New Credentials

After clicking **CREATE**, you'll see:
- **Client ID**: Copy this (looks like: `123456789-xxx...xxx.apps.googleusercontent.com`)
- **Client Secret**: Copy this (looks like: `GOCSPX-xxx...xxx`)

### Step 4: Update Backend Configuration

Open: `C:\Users\Harshal\Downloads\DualQueryIntelligence\backend\.env`

Replace with your new credentials:
```env
GOOGLE_CLIENT_ID=YOUR_NEW_CLIENT_ID_HERE.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_NEW_CLIENT_SECRET_HERE
```

### Step 5: Update Frontend Configuration

Open: `C:\Users\Harshal\Downloads\DualQueryIntelligence\frontend\client\.env`

Replace with your new client ID:
```env
VITE_GOOGLE_CLIENT_ID=YOUR_NEW_CLIENT_ID_HERE.apps.googleusercontent.com
```

### Step 6: Restart Servers

**Stop current servers** (Ctrl+C in both terminals), then:

**Backend:**
```bash
cd C:\Users\Harshal\Downloads\DualQueryIntelligence\backend
python run.py
```

**Frontend:**
```bash
cd C:\Users\Harshal\Downloads\DualQueryIntelligence\frontend
npm run dev
```

### Step 7: Test
Go to the login page and try Google Sign-In again.

---

## SOLUTION 3: Enable OAuth Consent Screen

Sometimes the issue is with the OAuth Consent Screen configuration:

### Step 1: Configure OAuth Consent Screen

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. If not configured:
   - Click **"CONFIGURE CONSENT SCREEN"**
   - Select **"External"**
   - Click **"CREATE"**

### Step 2: Fill Required Fields

**App information:**
- App name: `DualQueryIntelligence`
- User support email: Your email
- Developer contact: Your email

**App domain (Optional for testing):**
- Leave blank for now

**Scopes:**
- Use default scopes (email, profile, openid)

**Test users:**
- Click **"+ ADD USERS"**
- Add: `harshalingle517@gmail.com`
- Click **"SAVE"**

### Step 3: Publish (Optional)

For development, you can keep it in "Testing" mode with test users.

---

## SOLUTION 4: Check OAuth Client Type

Make sure your OAuth client is a **Web application**, not:
- ❌ Android
- ❌ iOS
- ❌ Chrome extension
- ✅ Web application (CORRECT)

If it's not a Web application:
1. Delete the existing client
2. Create a new one as "Web application"
3. Follow Solution 2 above

---

## SOLUTION 5: Clear Browser Cache

Sometimes the browser caches the OAuth error:

### Chrome/Edge:
1. Press `Ctrl + Shift + Delete`
2. Select "Cached images and files"
3. Click "Clear data"
4. Or use **Incognito/Private mode**

### Firefox:
1. Press `Ctrl + Shift + Delete`
2. Select "Cache"
3. Click "Clear Now"
4. Or use **Private Window**

---

## SOLUTION 6: Enable Required APIs

Make sure Google+ API is enabled:

1. Go to: https://console.cloud.google.com/apis/library
2. Search: **"Google+ API"**
3. Click on it
4. Click **"ENABLE"** (if not already enabled)

Also enable:
- **Google Identity Toolkit API** (optional but recommended)

---

## Verification Checklist

After applying any solution, verify these:

- [ ] Authorized JavaScript origins include `http://localhost:5175`
- [ ] No trailing slashes in origins
- [ ] Using `http://` not `https://` for localhost
- [ ] OAuth Consent Screen is configured
- [ ] Test user email is added (for testing mode)
- [ ] Client type is "Web application"
- [ ] Google+ API is enabled
- [ ] Waited 1-2 minutes after saving changes
- [ ] Cleared browser cache or using incognito
- [ ] Backend and frontend restarted with correct Client ID

---

## Testing Command (Optional)

To verify your configuration without the browser:

```bash
curl -X POST http://localhost:8000/api/auth/google \
  -H "Content-Type: application/json" \
  -d '{"token":"test-token"}'
```

Expected response (will fail but shows endpoint is working):
```json
{"detail":"Invalid Google token"}
```

---

## Common Mistakes to Avoid

1. **Trailing Slash**: `http://localhost:5175/` ❌
   - Correct: `http://localhost:5175` ✅

2. **HTTPS on Localhost**: `https://localhost:5175` ❌
   - Correct: `http://localhost:5175` ✅

3. **Wrong Port**: Using `5173` when app runs on `5175` ❌
   - Add ALL ports you might use ✅

4. **Spaces in URLs**: Extra spaces before/after URL ❌
   - Trim spaces ✅

5. **Not Waiting**: Testing immediately after save ❌
   - Wait 1-2 minutes ✅

---

## Screenshot Guide

Your Google Console should look like this:

```
╔══════════════════════════════════════════════════╗
║  OAuth 2.0 Client ID Details                    ║
╠══════════════════════════════════════════════════╣
║  Name: DualQueryIntelligence Web Client          ║
║  Client ID: 204472130909-btqroif1ao4o8quc0t...  ║
║  Client secret: GOCSPX-xxxxxx (click to show)   ║
║  Creation date: Jan 10, 2025                     ║
╠══════════════════════════════════════════════════╣
║  Authorized JavaScript origins                   ║
║  ┌────────────────────────────────────────────┐ ║
║  │ http://localhost:5175                      │ ║
║  │ http://localhost:5174                      │ ║
║  │ http://localhost:5173                      │ ║
║  │ http://localhost:3000                      │ ║
║  │ http://localhost:8000                      │ ║
║  └────────────────────────────────────────────┘ ║
║                                                  ║
║  Authorized redirect URIs                        ║
║  ┌────────────────────────────────────────────┐ ║
║  │ http://localhost:5175                      │ ║
║  │ http://localhost:5174                      │ ║
║  │ http://localhost:5173                      │ ║
║  │ http://localhost:8000/api/auth/google/...  │ ║
║  └────────────────────────────────────────────┘ ║
╠══════════════════════════════════════════════════╣
║             [SAVE]  [CANCEL]                     ║
╚══════════════════════════════════════════════════╝
```

---

## Still Not Working?

If none of these solutions work:

1. **Share the exact error** from browser console (F12)
2. **Check backend logs**: `backend/backend.log`
3. **Verify project**: Make sure you're editing the correct Google Cloud project
4. **Try different browser**: Test in Chrome, Firefox, Edge
5. **Contact me** with:
   - Screenshot of your OAuth client configuration
   - Browser console errors (F12 → Console tab)
   - Backend log errors

---

## Quick Fix Commands

If you need to restart everything quickly:

```bash
# Kill all running processes
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Start backend
cd C:\Users\Harshal\Downloads\DualQueryIntelligence\backend
python run.py

# Start frontend (in new terminal)
cd C:\Users\Harshal\Downloads\DualQueryIntelligence\frontend
npm run dev
```

---

## Success Indicators

When Google OAuth is working correctly, you should see:

1. ✅ Google popup opens smoothly
2. ✅ Account selection screen appears
3. ✅ After selecting account, popup closes
4. ✅ You're redirected to dashboard
5. ✅ Your Google name/email shows in sidebar
6. ✅ No errors in browser console

---

**Good luck! This should resolve your Google OAuth issue.**

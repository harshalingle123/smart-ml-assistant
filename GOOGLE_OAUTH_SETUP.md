# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for the DualQueryIntelligence application.

## Overview

Google OAuth allows users to sign in with their Google account. The implementation consists of:
- **Backend**: FastAPI endpoints that verify Google ID tokens
- **Frontend**: React components with Google Sign-In button

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "New Project"
3. Enter project name: `DualQueryIntelligence`
4. Click "Create"

## Step 2: Enable Google+ API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google+ API"
3. Click on it and click "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" user type
3. Click "Create"
4. Fill in the required fields:
   - **App name**: `DualQueryIntelligence`
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click "Save and Continue"
6. On the "Scopes" page, click "Save and Continue" (we'll use default scopes)
7. On the "Test users" page, you can add test emails or skip
8. Click "Save and Continue"

## Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Web application"
4. Configure:
   - **Name**: `DualQueryIntelligence Web Client`
   - **Authorized JavaScript origins**:
     - `http://localhost:5173`
     - `http://localhost:3000`
   - **Authorized redirect URIs**:
     - `http://localhost:8000/api/auth/google/callback`
     - `http://localhost:5173`
5. Click "Create"
6. **IMPORTANT**: Copy the Client ID and Client Secret

## Step 5: Configure Backend

1. Open `backend/.env` file
2. Replace the Google OAuth placeholder values:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

**Example:**
```env
GOOGLE_CLIENT_ID=123456789-abc123def456ghi789jkl012mno345pqr.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

3. Save the file
4. Restart the backend server

## Step 6: Configure Frontend

1. Create a `.env` file in the `frontend` directory (if it doesn't exist)
2. Add your Google Client ID:

```env
VITE_GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
```

**Example:**
```env
VITE_GOOGLE_CLIENT_ID=123456789-abc123def456ghi789jkl012mno345pqr.apps.googleusercontent.com
```

3. Save the file
4. Restart the frontend development server

## Step 7: Test Google Login

1. **Start both servers**:
   ```bash
   # Backend
   cd backend
   python run.py

   # Frontend (in a new terminal)
   cd frontend
   npm run dev
   ```

2. **Access the login page**: `http://localhost:5173/login`

3. **Click "Continue with Google"** button

4. **Select your Google account** in the popup

5. **Verify successful login**:
   - You should be redirected to the dashboard
   - Your name and email from Google should appear in the sidebar
   - A JWT token should be stored in localStorage

## API Endpoint

### POST /api/auth/google

Authenticates a user with a Google ID token.

**Request:**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE..."
}
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response (Error):**
```json
{
  "detail": "Invalid Google token"
}
```

## How It Works

### Frontend Flow:
1. User clicks "Continue with Google" button
2. Google OAuth popup opens
3. User selects their Google account
4. Frontend receives Google ID token
5. Frontend sends token to backend `/api/auth/google` endpoint
6. Frontend receives JWT access token
7. Token is stored in localStorage
8. User is redirected to dashboard

### Backend Flow:
1. Receives Google ID token from frontend
2. Verifies token with Google's servers
3. Extracts user information (email, name)
4. Checks if user exists in database
5. If user exists: Generate JWT and return
6. If new user: Create account, generate JWT, and return

## Security Notes

1. **Never commit `.env` files to Git**
   - Already added to `.gitignore`
   - Store secrets securely

2. **Use HTTPS in production**
   - Update redirect URIs in Google Console
   - Update GOOGLE_REDIRECT_URI in `.env`

3. **Verify email is from verified domain** (Optional)
   - Add domain validation in backend
   - Example: Only allow @yourcompany.com emails

4. **Token expiration**
   - Google ID tokens expire after 1 hour
   - JWT tokens expire based on `ACCESS_TOKEN_EXPIRE_MINUTES`

## Troubleshooting

### "Invalid Google token" error
- Check that GOOGLE_CLIENT_ID in backend `.env` matches the one in Google Console
- Ensure the token hasn't expired
- Verify that Google+ API is enabled

### "redirect_uri_mismatch" error
- Ensure redirect URIs in Google Console exactly match your application URLs
- Check for trailing slashes (should not have them)
- Verify you're using the correct protocol (http vs https)

### Google popup doesn't open
- Check browser popup blocker settings
- Verify VITE_GOOGLE_CLIENT_ID is set in frontend `.env`
- Check browser console for errors

### User not created in database
- Check MongoDB connection
- Verify backend logs for errors
- Test with manual registration first

## Production Deployment

When deploying to production:

1. **Update Google Console**:
   - Add production domain to Authorized JavaScript origins
   - Add production callback URL to Authorized redirect URIs

2. **Update Backend `.env`**:
   ```env
   GOOGLE_REDIRECT_URI=https://yourdomain.com/api/auth/google/callback
   CORS_ORIGINS=https://yourdomain.com
   ```

3. **Update Frontend `.env`**:
   ```env
   VITE_GOOGLE_CLIENT_ID=your-production-client-id
   VITE_API_URL=https://api.yourdomain.com
   ```

4. **Use environment-specific credentials**
   - Consider separate Google projects for dev/staging/prod
   - Use different Client IDs for each environment

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Websites](https://developers.google.com/identity/sign-in/web)
- [@react-oauth/google Documentation](https://www.npmjs.com/package/@react-oauth/google)

## Support

For issues or questions:
1. Check backend logs: `backend/backend.log`
2. Check frontend console for JavaScript errors
3. Verify all environment variables are set correctly
4. Test with the built-in email/password login first

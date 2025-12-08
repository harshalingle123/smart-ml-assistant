# Authentication Troubleshooting Guide

## Common Errors and Solutions

### 1. HTTP 429 - Too Many Requests (Rate Limiting)

**Error Message:** "Too many requests. Please try again in X seconds."

**Cause:** You've exceeded the rate limit for authentication endpoints.

**Rate Limits:**
- **Send OTP**: 3 attempts per 5 minutes (per IP and per email)
- **Register**: 3 attempts per hour (per IP)
- **Login**: 5 attempts per 5 minutes (per IP and per email)
- **Password Reset**: 3 attempts per hour (per IP)

**Solutions:**
1. **Wait**: The error tells you how long to wait (check `retry_after` field)
2. **Clear rate limit** (development only):
   ```python
   # In Python console
   from app.middleware.auth_rate_limiter import rate_limiter
   import asyncio

   # Clear IP rate limit
   asyncio.run(rate_limiter.reset_identifier("ip:127.0.0.1"))

   # Clear email rate limit
   asyncio.run(rate_limiter.reset_identifier("email:your@email.com"))
   ```

### 2. HTTP 422 - Unprocessable Entity (Validation Error)

**Cause:** Your request data failed validation.

**Common Reasons:**

#### A. Invalid OTP
- OTP must be exactly 6 digits
- OTP expires after 10 minutes
- Maximum 5 attempts per OTP

**Solution:** Request a new OTP

#### B. Password Too Short
- Minimum 6 characters required
- No special characters needed (simplified validation)

**Solution:** Use a password with at least 6 characters

#### C. Name Too Short
- Minimum 2 characters required
- Only letters, spaces, hyphens, and apostrophes allowed

**Solution:** Use a valid name

#### D. Invalid Email Format
**Solution:** Use a valid email address

### 3. HTTP 400 - Email Already Registered

**Cause:** Email is already in the database (case-insensitive check)

**Solutions:**

#### Option 1: Check Database
```bash
python check_email.py your@email.com
```

#### Option 2: Clean Up Email (Development Only)
```bash
python cleanup_email.py your@email.com
```

This will:
- Remove user records
- Remove OTP records
- Clean up expired OTPs

#### Option 3: Use Forgot Password
If you forgot your password, use the "Forgot Password" link on the login page.

### 4. OTP Not Received

**Cause:** Email sending failed or email is in spam folder

**Solutions:**
1. **Check Console Logs** (Development Mode):
   - Backend logs show the OTP in console
   - Look for: `Generated OTP for <email>: XXXXXX`

2. **Check Spam Folder**

3. **Verify SMTP Settings** (if using real email):
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SENDER_EMAIL=your-email@gmail.com
   ```

4. **Get App Password** for Gmail:
   - Go to https://myaccount.google.com/apppasswords
   - Generate new app password
   - Use that in `.env` file

### 5. Backend Not Responding

**Symptoms:**
- Connection timeout errors
- No response from API

**Solutions:**
1. **Check if backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Restart backend**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Check MongoDB connection**:
   - Make sure MongoDB is running
   - Verify `MONGODB_URL` in `.env`

## Development Tools

### 1. Check Email in Database
```bash
python check_email.py your@email.com
```

Output shows:
- User records
- OTP records
- Cleanup commands

### 2. Clean Up Email Records
```bash
python cleanup_email.py your@email.com
```

⚠️ **Warning:** This permanently deletes all data for the email.

### 3. View Backend Logs

The backend logs show:
- OTP codes (in development)
- Validation errors
- Rate limit warnings
- Registration attempts

Look for:
```
INFO: Generated OTP for <email>: XXXXXX
WARNING: Rate limit exceeded for <identifier>
ERROR: Registration error for <email>
```

## Testing Registration Flow

### Step 1: Send OTP
```bash
curl -X POST http://localhost:8000/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "purpose": "signup"}'
```

### Step 2: Check Console for OTP
Look in backend logs for:
```
INFO: Generated OTP for test@example.com: 123456
```

### Step 3: Complete Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "test123",
    "otp": "123456"
  }'
```

## Quick Fixes

### Reset Everything for Testing
```bash
# Clean up email
python cleanup_email.py test@example.com

# Clear Python cache
cd backend
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Restart backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Disable Rate Limiting (Development Only)

Edit `backend/app/middleware/auth_rate_limiter.py`:

```python
# Increase limits for testing
SEND_OTP = {"max_requests": 100, "window_seconds": 60}
REGISTER = {"max_requests": 100, "window_seconds": 60}
```

Then restart backend.

## Need Help?

1. Check backend logs for error messages
2. Use `check_email.py` to inspect database
3. Verify all environment variables in `.env`
4. Make sure MongoDB is running
5. Clear browser cache and try again

# Industry-Standard Authentication System

## Overview

This authentication system implements industry best practices including:
- ✅ Email OTP verification for signup
- ✅ Strong password validation
- ✅ Rate limiting and brute force protection
- ✅ Account lockout after failed attempts
- ✅ Google OAuth integration with proper data storage
- ✅ Password reset with OTP verification
- ✅ Comprehensive test coverage

## Features

### 1. **Email OTP Verification**
All new signups require email verification via OTP (One-Time Password):
- 6-digit OTP codes
- 10-minute expiration
- Maximum 5 verification attempts
- Rate limited to prevent abuse

### 2. **Strong Password Requirements**
Passwords must meet these criteria:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character
- No common passwords (password123, etc.)
- No sequential characters (abc, 123, etc.)
- No repeated characters (aaa, 111, etc.)

### 3. **Account Security**
- **Rate Limiting**: Protects against brute force attacks
  - Login: 5 attempts per 5 minutes
  - Registration: 3 attempts per hour
  - OTP requests: 3 per 5 minutes
  - Password reset: 3 per hour

- **Account Lockout**: After 5 failed login attempts
  - Account locked for 30 minutes
  - Can be unlocked via password reset

- **Account Status Tracking**:
  - `pending`: Email not verified
  - `active`: Normal account
  - `locked`: Too many failed attempts
  - `suspended`: Manually suspended by admin

### 4. **Google OAuth Integration**
- Properly stores OAuth provider info (`auth_provider`, `oauth_id`)
- Automatically verifies email for Google users
- Handles account linking (email signup → Google login)
- Creates users with verified status

## API Endpoints

### Registration Flow

#### 1. Send OTP for Signup
```http
POST /api/auth/send-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "purpose": "signup"
}
```

**Response:**
```json
{
  "message": "OTP sent successfully. Please check your email.",
  "email": "user@example.com",
  "expires_in": 600
}
```

#### 2. Complete Registration
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456",
  "password": "StrongPassword123!",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "name": "John Doe",
  "current_plan": "free",
  "email_verified": true,
  "auth_provider": "email",
  "account_status": "active",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401`: Invalid credentials
- `403`: Account locked/suspended or email not verified
- `429`: Rate limit exceeded

### Password Reset Flow

#### 1. Request Password Reset
```http
POST /api/auth/password-reset/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If an account exists with this email, a password reset code has been sent.",
  "email": "user@example.com"
}
```

#### 2. Complete Password Reset
```http
POST /api/auth/password-reset/complete
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewStrongPassword123!"
}
```

**Response:**
```json
{
  "message": "Password reset successfully. You can now login with your new password."
}
```

### Google OAuth

```http
POST /api/auth/google
Content-Type: application/json

{
  "token": "google-id-token-from-frontend"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Get Current User

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "name": "John Doe",
  "current_plan": "free",
  "email_verified": true,
  "auth_provider": "email",
  "account_status": "active",
  "created_at": "2025-01-15T10:30:00Z",
  "last_login_at": "2025-01-15T14:30:00Z"
}
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Required for OTP email verification
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
SENDER_NAME=Smart ML Assistant

# Frontend URL for email links
FRONTEND_URL=http://localhost:5173

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Gmail Setup

1. Enable 2-factor authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an "App Password"
4. Use the App Password as `SMTP_PASSWORD` (not your regular password)

### Alternative Email Providers

**SendGrid:**
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

**Mailgun:**
```bash
SMTP_SERVER=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=your-mailgun-username
SMTP_PASSWORD=your-mailgun-password
```

**AWS SES:**
```bash
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

## Database Schema

### User Model

```python
{
    "_id": ObjectId,
    "email": str,
    "name": str,
    "password": str,  # Hashed with bcrypt
    "current_plan": str,
    "email_verified": bool,
    "auth_provider": str,  # "email", "google", etc.
    "oauth_id": str,  # Google ID, GitHub ID, etc.
    "account_status": str,  # "pending", "active", "locked", "suspended"
    "failed_login_attempts": int,
    "last_login_attempt": datetime,
    "account_locked_until": datetime,
    "created_at": datetime,
    "updated_at": datetime,
    "last_login_at": datetime
}
```

### OTP Code Model

```python
{
    "_id": ObjectId,
    "email": str,
    "otp": str,
    "purpose": str,  # "signup", "password_reset", "email_change"
    "created_at": datetime,
    "expires_at": datetime,
    "verified": bool,
    "attempts": int
}
```

## Testing

Run the comprehensive test suite:

```bash
# Run all auth tests
pytest backend/tests/test_auth.py -v

# Run specific test class
pytest backend/tests/test_auth.py::TestPasswordValidation -v

# Run with coverage
pytest backend/tests/test_auth.py --cov=app.routers.auth --cov-report=html
```

### Test Coverage

The test suite covers:
- ✅ Password strength validation
- ✅ OTP generation and verification
- ✅ Complete registration flow
- ✅ Login with correct/incorrect credentials
- ✅ Account lockout after failed attempts
- ✅ Password reset flow
- ✅ Rate limiting
- ✅ Google OAuth for new and existing users

## Security Best Practices Implemented

1. **Password Security**
   - Bcrypt hashing with salt
   - Strong password requirements
   - Common password blacklist

2. **Email Verification**
   - Required for all email signups
   - OTP expires after 10 minutes
   - Limited verification attempts

3. **Brute Force Protection**
   - Rate limiting by IP and email
   - Account lockout after failed attempts
   - Exponential backoff

4. **Data Protection**
   - No password storage for OAuth users
   - Secure token generation
   - HTTPS required in production

5. **Privacy**
   - Generic error messages (no email enumeration)
   - Secure password reset flow
   - Minimal data collection

## Migration from Old System

If you have existing users without the new fields:

```python
# Run this migration script
from app.mongodb import mongodb
from datetime import datetime

async def migrate_users():
    users = await mongodb.database["users"].find({}).to_list(length=None)

    for user in users:
        update_fields = {}

        if "email_verified" not in user:
            update_fields["email_verified"] = True  # Assume old users are verified

        if "auth_provider" not in user:
            update_fields["auth_provider"] = "email"

        if "account_status" not in user:
            update_fields["account_status"] = "active"

        if "failed_login_attempts" not in user:
            update_fields["failed_login_attempts"] = 0

        if "created_at" not in user:
            update_fields["created_at"] = datetime.utcnow()

        if update_fields:
            await mongodb.database["users"].update_one(
                {"_id": user["_id"]},
                {"$set": update_fields}
            )
```

## Development Mode

When email credentials are not configured, the system operates in development mode:
- OTP codes are logged to console instead of being emailed
- All other security features remain active
- Useful for local testing without email setup

## Production Checklist

Before deploying to production:

- [ ] Configure proper SMTP credentials
- [ ] Set strong `SECRET_KEY` in environment
- [ ] Enable HTTPS/SSL
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Set up email monitoring
- [ ] Configure Google OAuth credentials (if using)
- [ ] Test rate limiting under load
- [ ] Set up logging and monitoring
- [ ] Run migration for existing users

## Support

For issues or questions:
- Check logs for detailed error messages
- Ensure environment variables are set correctly
- Verify SMTP credentials and connectivity
- Test with development mode first

## License

MIT License - See LICENSE file for details

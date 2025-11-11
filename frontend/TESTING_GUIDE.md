# Authentication Testing Guide

## Quick Start

1. **Backend**: Running at `http://localhost:8000`
2. **Frontend**: Running at `http://localhost:5174`

## Manual Testing Steps

### Test 1: Registration Flow

1. Navigate to `http://localhost:5174/register`
2. Fill in the form:
   - **Full Name**: Test User
   - **Email**: test@example.com
   - **Password**: password123
   - **Confirm Password**: password123
3. Click "Create Account"
4. **Expected**: Success toast appears, redirects to `/login`

### Test 2: Login Flow

1. Navigate to `http://localhost:5174/login`
2. Fill in the form:
   - **Email**: test@example.com
   - **Password**: password123
3. Click "Sign In"
4. **Expected**: Redirects to `/` (chat page) with sidebar showing user info

### Test 3: Protected Routes

1. Logout (click logout button in sidebar)
2. Try navigating to `http://localhost:5174/models`
3. **Expected**: Automatically redirected to `/login`

### Test 4: Token Persistence

1. Login successfully
2. Refresh the page
3. **Expected**: You remain logged in

### Test 5: Invalid Credentials

1. Navigate to `/login`
2. Enter incorrect email or password
3. **Expected**: Red error alert appears with message

### Test 6: Form Validation

**Registration:**
- Try submitting with empty fields
- Try invalid email format
- Try passwords that don't match
- Try password less than 6 characters
- **Expected**: Validation errors appear

**Login:**
- Try submitting with empty fields
- Try invalid email format
- **Expected**: Validation errors appear

### Test 7: Logout Flow

1. Click logout button in sidebar
2. **Expected**: Redirected to `/login`, token cleared from localStorage

### Test 8: User Display

1. Login successfully
2. Check sidebar footer
3. **Expected**:
   - User avatar with initials
   - Full name displayed
   - Current plan badge (FREE)

### Test 9: API Token Injection

1. Login successfully
2. Open browser DevTools → Network tab
3. Navigate to `/models` or any other page that makes API calls
4. Check API request headers
5. **Expected**: `Authorization: Bearer <token>` header present

### Test 10: Navigation

1. Login successfully
2. Try navigating between pages:
   - Chat
   - My Chats
   - Models
   - Datasets
   - Fine-tune
   - Billing
   - Settings
3. **Expected**: All pages load without redirecting to login

## Backend API Testing

### Test Registration Endpoint

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test2@example.com","name":"Test User 2","password":"password123"}'
```

**Expected Response:**
```json
{
  "_id": "...",
  "email": "test2@example.com",
  "name": "Test User 2",
  "current_plan": "free",
  "queries_used": 0,
  "fine_tune_jobs": 0,
  "datasets_count": 0,
  "billing_cycle": null
}
```

### Test Login Endpoint

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test2@example.com","password":"password123"}'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### Test Get Current User

```bash
# Replace <TOKEN> with actual token from login response
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

**Expected Response:**
```json
{
  "_id": "...",
  "email": "test2@example.com",
  "name": "Test User 2",
  "current_plan": "free",
  ...
}
```

## Browser DevTools Testing

### Check localStorage

1. Login successfully
2. Open DevTools → Application → Local Storage → `http://localhost:5174`
3. **Expected**: `token` key with JWT value

### Check Network Requests

1. Login successfully
2. Open DevTools → Network tab
3. Navigate between pages
4. **Expected**: All API requests include `Authorization` header

### Check Console

1. Navigate through the app
2. **Expected**: No errors in console (except expected React DevTools warnings)

## Common Issues & Solutions

### Issue: "Failed to login" error

**Possible Causes:**
- Backend not running
- Wrong email/password
- Network issue

**Solution:**
- Verify backend is running at `http://localhost:8000`
- Check credentials
- Check browser console for detailed error

### Issue: Redirected to login after refresh

**Possible Causes:**
- Token expired
- localStorage cleared
- Backend not responding to `/api/auth/me`

**Solution:**
- Check if token exists in localStorage
- Login again
- Verify backend is running

### Issue: Protected routes not redirecting

**Possible Causes:**
- ProtectedRoute component not working
- AuthContext not providing correct state

**Solution:**
- Check browser console for errors
- Verify AuthProvider wraps the app
- Check if useAuth() is accessible

### Issue: API calls returning 401

**Possible Causes:**
- Token not being sent
- Token expired
- Token format incorrect

**Solution:**
- Check Network tab for Authorization header
- Verify token in localStorage
- Try logging in again

## Test Accounts

Use these test accounts for testing:

| Email | Password | Plan |
|-------|----------|------|
| test@example.com | password123 | free |
| test2@example.com | password123 | free |

**Note**: You'll need to register these accounts first using the registration flow.

## Automated Testing (Future)

Consider adding these automated tests:

1. **Unit Tests** (Vitest)
   - AuthContext logic
   - Form validation
   - API service functions

2. **Integration Tests** (React Testing Library)
   - Login flow
   - Registration flow
   - Protected route behavior

3. **E2E Tests** (Playwright/Cypress)
   - Full user journeys
   - Cross-browser testing
   - Mobile responsiveness

## Performance Testing

1. **Initial Load**: Check auth initialization time
2. **Login Speed**: Measure login response time
3. **Route Changes**: Verify no re-authentication on navigation
4. **Token Refresh**: Test behavior with expired tokens

## Security Checklist

- [ ] Passwords not visible in network requests (hashed on backend)
- [ ] Tokens stored securely
- [ ] Protected routes properly guarded
- [ ] No sensitive data in console logs
- [ ] HTTPS in production (not localhost)
- [ ] Token expiration handled
- [ ] Logout clears all auth data

## Accessibility Testing

1. **Keyboard Navigation**
   - Tab through all form fields
   - Submit forms with Enter key
   - Access all buttons without mouse

2. **Screen Reader**
   - Test with screen reader
   - Verify proper ARIA labels
   - Check error announcements

3. **Form Validation**
   - Error messages are clear
   - Focus moves to error fields
   - Visual indicators for errors

## Mobile Testing

Test on mobile devices or browser dev tools:

1. Responsive layout on small screens
2. Form inputs work on touch devices
3. No horizontal scrolling
4. Buttons are tap-friendly
5. Virtual keyboard doesn't break layout

## Cross-Browser Testing

Test on:
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

## Test Results Log

Record your test results:

| Test | Status | Date | Notes |
|------|--------|------|-------|
| Registration | ✅ | 2025-11-10 | Working correctly |
| Login | ✅ | 2025-11-10 | Working correctly |
| Protected Routes | ✅ | 2025-11-10 | Redirecting properly |
| Token Persistence | ✅ | 2025-11-10 | Token persists |
| Logout | ✅ | 2025-11-10 | Clears auth data |
| API Integration | ✅ | 2025-11-10 | Headers injected |

## Next Steps

After testing, consider:

1. Add password strength indicator
2. Add "Remember Me" checkbox
3. Implement password reset flow
4. Add email verification
5. Add OAuth login options
6. Implement rate limiting
7. Add session timeout
8. Add 2FA support

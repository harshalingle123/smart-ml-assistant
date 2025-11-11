# Authentication System Documentation

## Overview

A complete, production-ready authentication system for the DualQueryIntelligence React frontend.

## Architecture

### 1. Auth Context (`src/contexts/AuthContext.tsx`)

Central state management for authentication:

- **State Management**: User data, token, loading state
- **Token Storage**: Automatic localStorage persistence
- **Auto-initialization**: Fetches user data on app load if token exists
- **Type-safe API**: Fully typed with TypeScript

**Key Functions:**
- `login(token)` - Saves token and fetches user data
- `logout()` - Clears token and user data
- `updateUser(user)` - Updates user state
- `isAuthenticated` - Boolean indicating auth status

### 2. API Services

#### Auth Service (`src/lib/auth.ts`)

Handles authentication API calls:

```typescript
login(credentials: { email, password }) → Promise<Token>
register(data: { email, name, password }) → Promise<User>
getCurrentUser(token) → Promise<User>
```

**Features:**
- Proper error handling with detailed messages
- Type-safe interfaces
- Backend endpoint: `http://localhost:8000/api/auth/*`

#### API Service (`src/lib/api.ts`)

Updated with automatic token injection:

```typescript
getAuthHeaders() → HeadersInit
```

All API calls now automatically include the JWT token from localStorage.

### 3. Protected Routes (`src/components/ProtectedRoute.tsx`)

Route guard component that:
- Shows loading spinner while checking auth
- Redirects to `/login` if not authenticated
- Renders children if authenticated

### 4. Authentication Pages

#### Login Page (`src/pages/Login.tsx`)

**Features:**
- Email + password fields
- Form validation with Zod
- Error messages with Alert component
- Loading states
- Link to registration
- Responsive design

**Flow:**
1. User submits credentials
2. Calls `/api/auth/login`
3. Receives JWT token
4. Saves token via AuthContext
5. Fetches user data
6. Redirects to dashboard

#### Register Page (`src/pages/Register.tsx`)

**Features:**
- Name + email + password + confirm password
- Password matching validation
- Form validation with Zod
- Success toast notification
- Error handling
- Link to login
- Responsive design

**Flow:**
1. User submits registration data
2. Calls `/api/auth/register`
3. Shows success message
4. Redirects to login

### 5. App Integration

#### Updated App.tsx

**Routing Structure:**
```
/ (root)
├── /login (public)
├── /register (public)
└── * (protected layout)
    ├── / (chat)
    ├── /chats
    ├── /models
    ├── /datasets
    ├── /fine-tune
    ├── /billing
    └── /settings
```

**Provider Hierarchy:**
1. QueryClientProvider
2. TooltipProvider
3. ThemeProvider
4. AuthProvider
5. Router

#### Updated AppSidebar

**Features:**
- Displays user name/email
- Shows current plan (free/pro/enterprise)
- Avatar with user initials
- Logout button
- Automatically pulls data from AuthContext

## API Endpoints

### Backend Requirements

The authentication system expects these endpoints:

**POST /api/auth/register**
```json
Request: { "email": "string", "name": "string", "password": "string" }
Response: { "_id": "string", "email": "string", "name": "string", "current_plan": "string" }
```

**POST /api/auth/login**
```json
Request: { "email": "string", "password": "string" }
Response: { "access_token": "string", "token_type": "bearer" }
```

**GET /api/auth/me**
```
Headers: Authorization: Bearer <token>
Response: { "_id": "string", "email": "string", "name": "string", "current_plan": "string", ... }
```

## User Flow

### Registration Flow

1. User visits `/register`
2. Fills out name, email, password
3. Submits form
4. Account created on backend
5. Success toast shown
6. Redirected to `/login`

### Login Flow

1. User visits `/login`
2. Enters email + password
3. Submits form
4. Backend validates credentials
5. JWT token returned
6. Token saved to localStorage
7. User data fetched from `/api/auth/me`
8. Redirected to `/` (chat page)

### Protected Route Access

1. User navigates to protected route
2. ProtectedRoute checks auth state
3. If loading: Show spinner
4. If not authenticated: Redirect to `/login`
5. If authenticated: Render page

### Logout Flow

1. User clicks logout button in sidebar
2. `logout()` called in AuthContext
3. Token removed from localStorage
4. User state cleared
5. Redirected to `/login`

### Token Persistence

1. App loads
2. AuthContext checks localStorage for token
3. If token exists:
   - Fetches user data from `/api/auth/me`
   - User stays logged in
4. If no token or fetch fails:
   - User redirected to login

## Type Definitions

### User Interface

```typescript
interface User {
  _id?: string;
  id?: string;
  email: string;
  name: string;
  username?: string;
  current_plan: string;
  queries_used?: number;
  fine_tune_jobs?: number;
  datasets_count?: number;
  billing_cycle?: string | null;
}
```

### Token Interface

```typescript
interface Token {
  access_token: string;
  token_type: string;
}
```

## Security Features

1. **Token Storage**: JWT stored in localStorage (consider httpOnly cookies for production)
2. **Automatic Token Injection**: All API calls include Authorization header
3. **Protected Routes**: Unauthorized users redirected to login
4. **Token Validation**: Invalid/expired tokens trigger logout
5. **Error Handling**: Failed auth attempts show user-friendly errors

## UI/UX Features

1. **Loading States**: Spinners during API calls
2. **Error Messages**: Clear, actionable error alerts
3. **Form Validation**: Real-time validation with Zod
4. **Success Feedback**: Toast notifications
5. **Responsive Design**: Mobile-friendly with Tailwind CSS
6. **Accessible**: Proper ARIA labels, keyboard navigation
7. **Theme Support**: Works with light/dark themes

## Testing Checklist

- [ ] Register new account
- [ ] Login with credentials
- [ ] Access protected routes when logged in
- [ ] Redirect to login when not authenticated
- [ ] Logout successfully
- [ ] Token persists after page refresh
- [ ] Invalid credentials show error
- [ ] Network errors handled gracefully
- [ ] Password validation works
- [ ] Email validation works

## Environment

**Frontend:** http://localhost:5174
**Backend:** http://localhost:8000

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Wouter** - Routing
- **Tailwind CSS** - Styling
- **Radix UI** - Component primitives
- **React Hook Form** - Form management
- **Zod** - Schema validation
- **TanStack Query** - Data fetching
- **Lucide React** - Icons

## Files Created/Modified

### Created:
- `src/contexts/AuthContext.tsx` - Auth state management
- `src/components/ProtectedRoute.tsx` - Route guard
- `frontend/AUTHENTICATION.md` - This documentation

### Modified:
- `src/lib/auth.ts` - Auth API calls
- `src/lib/api.ts` - Token injection
- `src/pages/Login.tsx` - Login UI
- `src/pages/Register.tsx` - Register UI
- `src/App.tsx` - Routing setup
- `src/components/AppSidebar.tsx` - User display
- `src/types/api.ts` - Type definitions

## Future Enhancements

1. **Password Reset**: Forgot password flow
2. **Email Verification**: Verify email after registration
3. **Remember Me**: Persistent sessions
4. **Session Timeout**: Auto-logout after inactivity
5. **OAuth**: Google/GitHub login
6. **2FA**: Two-factor authentication
7. **Profile Management**: Update user details
8. **httpOnly Cookies**: More secure token storage
9. **Refresh Tokens**: Token refresh mechanism
10. **Rate Limiting**: Prevent brute force attacks

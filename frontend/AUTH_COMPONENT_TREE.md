# Authentication System - Component Tree

## Visual Component Structure

```
App.tsx (Root)
│
├─ QueryClientProvider (TanStack Query)
│  └─ TooltipProvider (Radix UI)
│     └─ ThemeProvider (Dark/Light mode)
│        └─ AuthProvider ← AUTH CONTEXT (Token + User State)
│           │
│           ├─ Route: /login (PUBLIC)
│           │  └─ Login.tsx
│           │     ├─ Email input
│           │     ├─ Password input
│           │     ├─ Error alerts
│           │     └─ Link to /register
│           │
│           ├─ Route: /register (PUBLIC)
│           │  └─ Register.tsx
│           │     ├─ Name input
│           │     ├─ Email input
│           │     ├─ Password input
│           │     ├─ Confirm password input
│           │     ├─ Error alerts
│           │     └─ Link to /login
│           │
│           └─ Route: * (PROTECTED)
│              └─ ProtectedRoute.tsx
│                 │
│                 ├─ [if loading]
│                 │  └─ Loading Spinner
│                 │
│                 ├─ [if not authenticated]
│                 │  └─ Redirect to /login
│                 │
│                 └─ [if authenticated]
│                    └─ ProtectedLayout
│                       ├─ SidebarProvider
│                       │  ├─ AppSidebar
│                       │  │  ├─ Header (Logo + App Name)
│                       │  │  ├─ Navigation Links
│                       │  │  │  ├─ Chat Section
│                       │  │  │  │  ├─ New Chat
│                       │  │  │  │  └─ My Chats
│                       │  │  │  ├─ Resources Section
│                       │  │  │  │  ├─ My Models
│                       │  │  │  │  ├─ Datasets
│                       │  │  │  │  └─ Fine-tune Jobs
│                       │  │  │  └─ Account Section
│                       │  │  │     ├─ Billing
│                       │  │  │     └─ Settings
│                       │  │  └─ Footer
│                       │  │     ├─ User Avatar (initials)
│                       │  │     ├─ User Name/Email
│                       │  │     ├─ Plan Badge
│                       │  │     └─ Logout Button ← LOGOUT ACTION
│                       │  │
│                       │  └─ Main Content Area
│                       │     ├─ Header Bar
│                       │     │  ├─ Sidebar Toggle
│                       │     │  └─ Theme Toggle
│                       │     │
│                       │     └─ Page Routes (Protected)
│                       │        ├─ / → Chat.tsx
│                       │        ├─ /chats → Chats.tsx
│                       │        ├─ /models → Models.tsx
│                       │        ├─ /datasets → Datasets.tsx
│                       │        ├─ /fine-tune → FineTune.tsx
│                       │        ├─ /billing → Billing.tsx
│                       │        └─ /settings → Settings.tsx
│                       │
│                       └─ Toaster (Notifications)
```

## Auth State Flow

```
┌─────────────────────────────────────────────────────────┐
│                     AuthContext.tsx                     │
│                                                         │
│  State:                                                 │
│  ├─ user: User | null                                   │
│  ├─ token: string | null                                │
│  ├─ isLoading: boolean                                  │
│  └─ isAuthenticated: boolean                            │
│                                                         │
│  Functions:                                             │
│  ├─ login(token) → Save token, fetch user              │
│  ├─ logout() → Clear token & user                       │
│  └─ updateUser(user) → Update user state               │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │
                         │ useAuth() hook
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
  Login.tsx      ProtectedRoute.tsx   AppSidebar.tsx
  Register.tsx   (checks auth)        (shows user info)
```

## API Call Flow

```
Component makes API call
        │
        ▼
   api.ts functions
        │
        ▼
   getAuthHeaders()
        │
        ├─ Read token from localStorage
        ├─ Add Authorization header
        └─ Return headers
        │
        ▼
   fetch() with headers
        │
        ▼
   Backend API (http://localhost:8000)
        │
        ├─ Validates JWT token
        ├─ Processes request
        └─ Returns response
```

## Authentication Flow Diagrams

### Registration Flow

```
User visits /register
        │
        ▼
Register.tsx form
        │
        ▼
User fills form (name, email, password)
        │
        ▼
Form validation (Zod)
        │
        ▼
POST /api/auth/register
        │
        ▼
Backend creates user
        │
        ▼
Success response
        │
        ▼
Toast notification
        │
        ▼
Redirect to /login
```

### Login Flow

```
User visits /login
        │
        ▼
Login.tsx form
        │
        ▼
User enters email + password
        │
        ▼
Form validation (Zod)
        │
        ▼
POST /api/auth/login
        │
        ▼
Backend validates credentials
        │
        ▼
Returns JWT token
        │
        ▼
AuthContext.login(token)
        │
        ├─ Save to localStorage
        ├─ Fetch user from /api/auth/me
        └─ Update context state
        │
        ▼
Redirect to / (chat page)
```

### Protected Route Access

```
User navigates to protected route
        │
        ▼
ProtectedRoute component
        │
        ├─ Check isLoading
        │  └─ if true → Show spinner
        │
        ├─ Check isAuthenticated
        │  ├─ if false → Redirect to /login
        │  └─ if true → Render children
        │
        └─ Render page content
```

### Logout Flow

```
User clicks logout button
        │
        ▼
AppSidebar.handleLogout()
        │
        ▼
AuthContext.logout()
        │
        ├─ Remove token from localStorage
        ├─ Clear user state
        └─ Set token to null
        │
        ▼
Redirect to /login
```

### Token Persistence Flow

```
App loads (page refresh)
        │
        ▼
AuthProvider.useEffect()
        │
        ├─ Check localStorage for token
        │
        ├─ If token exists:
        │  ├─ Set token in state
        │  ├─ GET /api/auth/me
        │  ├─ Set user in state
        │  └─ Set isLoading = false
        │
        └─ If no token:
           └─ Set isLoading = false
        │
        ▼
User remains logged in / redirected to login
```

## Key Files & Responsibilities

```
src/
├─ contexts/
│  └─ AuthContext.tsx
│     - Manages auth state globally
│     - Provides useAuth() hook
│     - Handles token persistence
│
├─ components/
│  ├─ ProtectedRoute.tsx
│  │  - Guards protected routes
│  │  - Shows loading state
│  │  - Redirects if not authenticated
│  │
│  └─ AppSidebar.tsx
│     - Displays user info
│     - Shows logout button
│     - Consumes useAuth()
│
├─ pages/
│  ├─ Login.tsx
│  │  - Login form UI
│  │  - Calls login API
│  │  - Handles auth errors
│  │
│  └─ Register.tsx
│     - Registration form UI
│     - Calls register API
│     - Validates form data
│
├─ lib/
│  ├─ auth.ts
│  │  - login() function
│  │  - register() function
│  │  - getCurrentUser() function
│  │
│  └─ api.ts
│     - getAuthHeaders() function
│     - All API call functions
│     - Auto-includes JWT token
│
├─ types/
│  └─ api.ts
│     - User interface
│     - Token interface
│     - Request/Response types
│
└─ App.tsx
   - Route configuration
   - Provider setup
   - Layout structure
```

## Data Dependencies

```
localStorage
    │
    ├─ "token": string (JWT)
    │
    └─ Used by:
       ├─ AuthContext (init)
       ├─ getAuthHeaders() (API calls)
       └─ logout() (clear)

AuthContext State
    │
    ├─ user: User | null
    ├─ token: string | null
    └─ isAuthenticated: boolean
    │
    └─ Used by:
       ├─ ProtectedRoute (check auth)
       ├─ AppSidebar (display user)
       ├─ Login (redirect logic)
       └─ Any component via useAuth()

Backend Session
    │
    └─ JWT Token validated on each request
       ├─ Contains user ID
       ├─ Has expiration
       └─ Must be in Authorization header
```

## Security Boundaries

```
PUBLIC ROUTES (No Auth Required)
├─ /login
└─ /register

PROTECTED ROUTES (Auth Required)
├─ /
├─ /chats
├─ /models
├─ /datasets
├─ /fine-tune
├─ /billing
└─ /settings

AUTH CHECKS
├─ ProtectedRoute component
├─ AuthContext.isAuthenticated
└─ Token in localStorage
```

## Component Communication

```
Login/Register → AuthContext → ProtectedRoute → Pages
     │               │              │
     │               │              └─ Checks auth state
     │               │
     │               └─ Provides auth state to all children
     │
     └─ Updates auth state on login/logout

AppSidebar → AuthContext
     │            │
     │            └─ Reads user data
     │            └─ Calls logout()
     │
     └─ Displays user info and logout button

API Calls → getAuthHeaders() → localStorage
     │           │                  │
     │           │                  └─ Reads token
     │           │
     │           └─ Returns headers with token
     │
     └─ Includes Authorization header automatically
```

---

This visual tree shows how all authentication components work together to create a secure, user-friendly authentication system.

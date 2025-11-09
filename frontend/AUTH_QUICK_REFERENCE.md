# Authentication Quick Reference

## For Developers

### Import Auth Context

```typescript
import { useAuth } from "@/contexts/AuthContext";
```

### Use Auth in Component

```typescript
function MyComponent() {
  const { user, token, isAuthenticated, isLoading, login, logout } = useAuth();

  if (isLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return <div>Please login</div>;

  return (
    <div>
      <p>Welcome, {user?.name}!</p>
      <p>Email: {user?.email}</p>
      <p>Plan: {user?.current_plan}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Check Auth State

```typescript
const { isAuthenticated } = useAuth();

if (isAuthenticated) {
  // User is logged in
} else {
  // User is not logged in
}
```

### Get Current User

```typescript
const { user } = useAuth();

console.log(user?.name);
console.log(user?.email);
console.log(user?.current_plan);
```

### Logout User

```typescript
const { logout } = useAuth();

const handleLogout = () => {
  logout();
  // Optionally redirect
  navigate("/login");
};
```

### Protect a Component

```typescript
import { ProtectedRoute } from "@/components/ProtectedRoute";

function MyPage() {
  return (
    <ProtectedRoute>
      <div>This content is protected</div>
    </ProtectedRoute>
  );
}
```

### Make Authenticated API Calls

API calls automatically include the auth token:

```typescript
import { getModels } from "@/lib/api";

function MyComponent() {
  const fetchModels = async () => {
    try {
      const models = await getModels(); // Token auto-included
      console.log(models);
    } catch (error) {
      console.error("Failed to fetch models", error);
    }
  };

  return <button onClick={fetchModels}>Load Models</button>;
}
```

### Add New Protected API Endpoint

In `src/lib/api.ts`:

```typescript
export const getMyData = async () => {
  const response = await fetch(`${BASE_URL}/api/my-endpoint`, {
    headers: getAuthHeaders() // Auto-includes token
  });
  if (!response.ok) {
    throw new Error("Failed to fetch data");
  }
  return response.json();
};
```

### User Type Definition

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

### Auth Context Type

```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}
```

## For Testing

### Test User Credentials

```
Email: test@example.com
Password: password123
```

### Create Test Account

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"password123"}'
```

### Login via API

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### Test Protected Endpoint

```bash
# Replace <TOKEN> with actual JWT
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

### Check Token in Browser

```javascript
// Open browser console
localStorage.getItem("token")
```

### Clear Auth State

```javascript
// Open browser console
localStorage.removeItem("token")
location.reload()
```

## Common Patterns

### Conditional Rendering Based on Auth

```typescript
function Header() {
  const { isAuthenticated, user } = useAuth();

  return (
    <header>
      {isAuthenticated ? (
        <div>Welcome, {user?.name}</div>
      ) : (
        <Link href="/login">Login</Link>
      )}
    </header>
  );
}
```

### Show Loading During Auth Check

```typescript
function App() {
  const { isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return <Routes />;
}
```

### Redirect After Login

```typescript
import { useLocation } from "wouter";

function LoginPage() {
  const [, setLocation] = useLocation();
  const { login } = useAuth();

  const handleLogin = async (token: string) => {
    await login(token);
    setLocation("/dashboard");
  };
}
```

### Access User Data Safely

```typescript
function Profile() {
  const { user } = useAuth();

  // Safe access with optional chaining
  return (
    <div>
      <h1>{user?.name ?? "Anonymous"}</h1>
      <p>{user?.email ?? "No email"}</p>
    </div>
  );
}
```

## Troubleshooting

### User Not Logged In After Refresh

**Check:**
```javascript
localStorage.getItem("token") // Should return JWT
```

**Fix:**
- Ensure token is saved correctly
- Check AuthContext initialization
- Verify `/api/auth/me` endpoint works

### API Calls Return 401

**Check:**
```javascript
// In Network tab, check if Authorization header exists
Authorization: Bearer <token>
```

**Fix:**
- Verify `getAuthHeaders()` is called
- Check token exists in localStorage
- Ensure token hasn't expired

### Protected Route Not Redirecting

**Check:**
- Is `ProtectedRoute` wrapping the component?
- Is `AuthProvider` in the component tree?
- Check browser console for errors

### Logout Not Working

**Check:**
```javascript
localStorage.getItem("token") // Should be null after logout
```

**Fix:**
- Ensure `logout()` is being called
- Check if token is removed from localStorage
- Verify redirect happens after logout

## URLs

- **Frontend**: http://localhost:5174
- **Backend**: http://localhost:8000
- **Login**: http://localhost:5174/login
- **Register**: http://localhost:5174/register

## Key Files

- `src/contexts/AuthContext.tsx` - Auth state
- `src/lib/auth.ts` - Auth API calls
- `src/lib/api.ts` - Token injection
- `src/components/ProtectedRoute.tsx` - Route guard
- `src/pages/Login.tsx` - Login page
- `src/pages/Register.tsx` - Register page

## Environment Variables

Currently hardcoded, but consider:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Then update:

```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL;
```

## Best Practices

1. **Always use `useAuth()` hook** - Don't access localStorage directly
2. **Check `isAuthenticated`** - Before showing sensitive data
3. **Handle loading states** - Show spinners during auth checks
4. **Clear errors** - Reset form errors after successful submission
5. **Use TypeScript** - Leverage type safety for User objects
6. **Test auth flows** - Regularly test login/logout/protected routes

## Security Notes

- Tokens stored in localStorage (consider httpOnly cookies for production)
- Always use HTTPS in production
- Implement token refresh for long sessions
- Add rate limiting on backend
- Validate input on both client and server
- Log security events

## Next Features to Add

- [ ] Password reset flow
- [ ] Email verification
- [ ] Remember me option
- [ ] OAuth integration
- [ ] 2FA support
- [ ] Session timeout
- [ ] Password strength indicator
- [ ] Account deletion

---

**Quick Help**: For detailed docs, see `AUTHENTICATION.md`

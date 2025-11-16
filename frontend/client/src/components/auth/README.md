# Authentication Components

Production-ready React authentication components with dark theme, animations, and full accessibility support.

## Components

### LoginPage
Sign-in page with email/password authentication and Google OAuth option.

**Features:**
- Email and password inputs with validation
- Password visibility toggle
- Forgot password link
- Google OAuth button
- Loading states
- Responsive design (chat preview hidden on mobile)

**Usage:**
```tsx
import { LoginPage } from '@/components/auth';

function App() {
  return <LoginPage />;
}
```

### RegisterPage
Registration page with full name, email, and password fields.

**Features:**
- Full name, email, and password inputs
- Real-time password strength validation (minimum 8 characters)
- Password visibility toggle
- Google OAuth button
- Loading states
- Responsive design (chat preview hidden on mobile)

**Usage:**
```tsx
import { RegisterPage } from '@/components/auth';

function App() {
  return <RegisterPage />;
}
```

### Shared Components

#### AuthLayout
Two-column layout wrapper that handles responsive behavior and layout direction.

**Props:**
- `children: ReactNode` - Form content to render
- `reverse?: boolean` - Reverses layout (form left, chat right). Default: false
- `chatPreview: ReactNode` - Chat preview component to render

#### ChatPreview
Animated chat preview showcasing the AutoML assistant interface.

**Features:**
- Gradient background with blue glow
- Animated chat messages with typing indicators
- Training progress bar
- Code snippet display
- Processing steps with checkmarks
- Fully animated using Tailwind CSS

#### SocialButton
Reusable OAuth button component (currently supports Google).

**Props:**
- `provider: 'google'` - OAuth provider
- `onClick: () => void` - Click handler
- `disabled?: boolean` - Disabled state

## Design Specifications

### Color Scheme
- **Background:** `#000000` (black)
- **Primary:** `#4169ff` (blue)
- **Text:** White with opacity variations
- **Chat Preview Gradient:** `#1a1a2e` to `#16213e`

### Typography
- System font stack (Apple system, Segoe UI, Roboto, etc.)
- Headings: Bold, 36px (text-4xl)
- Body: 14px (text-sm) with white/60% opacity

### Spacing & Layout
- Form inputs: 14px vertical, 16px horizontal padding
- Border radius: 8px (rounded-lg)
- Focus ring: 2px blue with offset
- Button hover: -2px translateY

### Animations
- `fadeIn`: 0.6s ease-out
- `slideUp`: 0.5s ease-out with 10px transform
- `bounce`: Built-in Tailwind for typing indicators
- `spin`: Built-in Tailwind for loading spinners

## Accessibility

All components include:
- Proper semantic HTML (form, label, input elements)
- ARIA labels for icon-only buttons
- Keyboard navigation support
- Focus states with visible indicators
- Required field validation
- Descriptive alt text for images/icons

## Integration

### Current Implementation
Components log form data to console for development:
```typescript
console.log('Login attempt:', formData);
console.log('Google OAuth login initiated');
```

### Production Integration
Replace console.log statements with actual authentication logic:

```typescript
// LoginPage.tsx
const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  setIsLoading(true);

  try {
    const response = await authAPI.login(formData);
    // Handle successful login (store token, redirect, etc.)
  } catch (error) {
    // Handle error (show toast, display error message)
  } finally {
    setIsLoading(false);
  }
};

const handleGoogleLogin = () => {
  window.location.href = `${API_URL}/auth/google`;
};
```

## File Structure

```
auth/
├── AuthLayout.tsx       # Two-column layout wrapper
├── ChatPreview.tsx      # Animated chat preview
├── LoginPage.tsx        # Sign-in page
├── RegisterPage.tsx     # Sign-up page
├── SocialButton.tsx     # OAuth button component
├── index.ts            # Barrel exports
└── README.md           # This file
```

## Tailwind Configuration

Custom animations added to `tailwind.config.ts`:

```typescript
keyframes: {
  fadeIn: {
    from: { opacity: "0" },
    to: { opacity: "1" },
  },
  slideUp: {
    from: { opacity: "0", transform: "translateY(10px)" },
    to: { opacity: "1", transform: "translateY(0)" },
  },
},
animation: {
  fadeIn: "fadeIn 0.6s ease-out",
  slideUp: "slideUp 0.5s ease-out",
}
```

## Browser Support

- Modern browsers with ES6+ support
- CSS Grid and Flexbox support required
- Tailwind CSS v3.x compatible

## Performance Optimizations

- Components wrapped with `React.memo()` to prevent unnecessary re-renders
- Event handlers memoized with `useCallback()`
- Password visibility toggle optimized to only re-render affected input
- Chat preview animations use CSS transforms for GPU acceleration

## Responsive Behavior

- **Desktop (lg+):** Two-column layout with chat preview
- **Mobile (<lg):** Single column, chat preview hidden
- Form maintains consistent width (max-w-md) across breakpoints

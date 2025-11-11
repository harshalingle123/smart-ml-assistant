# Dual Query Intelligence - Frontend

A modern React-based frontend for the Dual Query Intelligence platform, featuring chat interfaces, dataset management, and model fine-tuning capabilities.

## Tech Stack

- **React 18** - Modern UI library with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and development server
- **TanStack Query** - Powerful data fetching and caching
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Accessible component primitives
- **Wouter** - Lightweight routing
- **Recharts** - Data visualization

## Prerequisites

- **Node.js** 18+ and npm
- **Backend API** running on `http://localhost:8000`

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Configuration (Optional)

Create a `.env` file in the frontend directory if you need to customize the API URL:

```env
VITE_API_URL=http://localhost:8000
```

If not specified, the app defaults to `http://localhost:8000`.

### 3. Start Development Server

```bash
npm run dev
```

The application will start on `http://localhost:5173` by default.

### 4. Build for Production

```bash
npm run build
```

Built files will be in `dist/public/`.

### 5. Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── client/
│   └── src/
│       ├── components/       # Reusable UI components
│       │   ├── ui/          # Base UI components (buttons, cards, etc.)
│       │   ├── AppSidebar.tsx
│       │   ├── ChatInput.tsx
│       │   ├── MessageBubble.tsx
│       │   └── ...
│       ├── pages/           # Route components
│       │   ├── Chat.tsx
│       │   ├── Chats.tsx
│       │   ├── Models.tsx
│       │   ├── Datasets.tsx
│       │   ├── FineTune.tsx
│       │   └── Billing.tsx
│       ├── lib/             # Utilities and configurations
│       │   ├── api.ts       # API client with endpoints
│       │   ├── queryClient.ts # React Query setup
│       │   └── utils.ts
│       ├── types/           # TypeScript type definitions
│       │   └── api.ts       # API response types
│       ├── hooks/           # Custom React hooks
│       ├── App.tsx          # Root component with routing
│       └── main.tsx         # Application entry point
├── package.json
├── vite.config.ts           # Vite configuration with API proxy
├── tailwind.config.ts       # Tailwind CSS configuration
└── tsconfig.json            # TypeScript configuration
```

## API Integration

The frontend communicates with the FastAPI backend through:

1. **Vite Proxy**: Development requests to `/api/*` are proxied to `http://localhost:8000`
2. **API Client** (`client/src/lib/api.ts`): Centralized API functions with JWT authentication
3. **React Query**: Automatic caching and data synchronization

### Authentication

JWT tokens are stored in `localStorage` and automatically included in API requests via the `Authorization: Bearer <token>` header.

### Available API Endpoints

- **Auth**: `/api/auth/login`, `/api/auth/register`, `/api/auth/me`
- **Chats**: `/api/chats`, `/api/chats/{id}`
- **Messages**: `/api/messages/{chatId}`
- **Models**: `/api/models`, `/api/models/{id}`
- **Datasets**: `/api/datasets`, `/api/datasets/upload`
- **Fine-tuning**: `/api/finetune/jobs`, `/api/finetune/start`
- **API Keys**: `/api/keys`

## Development

### Type Checking

TypeScript types are automatically checked during build. To manually check:

```bash
npm run check
```

### Code Style

- Use functional components with hooks
- Follow TypeScript best practices
- Maintain component modularity
- Use Tailwind for styling

### Adding New Components

1. Create component in `client/src/components/`
2. Import and use Radix UI primitives from `client/src/components/ui/`
3. Apply Tailwind classes for styling
4. Export and use in pages or other components

## Features

- **Chat Interface**: Real-time conversation with AI models
- **Dataset Management**: Upload, preview, and manage CSV datasets
- **Model Fine-tuning**: Create and monitor fine-tuning jobs
- **Model Management**: View and manage trained models
- **Billing Dashboard**: Track usage and manage subscriptions
- **Dark Mode**: System-aware theme switching
- **Responsive Design**: Mobile-friendly layouts

## Troubleshooting

### Port Already in Use

If port 5173 is occupied, Vite will automatically use the next available port.

### API Connection Issues

1. Ensure the backend is running on `http://localhost:8000`
2. Check CORS settings in the backend configuration
3. Verify the proxy configuration in `vite.config.ts`

### Build Errors

1. Clear node_modules and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Clear Vite cache:
   ```bash
   rm -rf node_modules/.vite
   ```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run check` | Run TypeScript type checking |

## Backend Integration

This frontend requires the FastAPI backend to be running. See the backend README for setup instructions.

**Backend Repository**: `../backend/`

Make sure the backend is started before running the frontend:

```bash
# In the backend directory
cd ../backend
python run.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT

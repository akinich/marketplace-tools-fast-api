# Farm Management System - Frontend

Modern React frontend for the Farm Management System with Material-UI.

## Version
**v1.0.0** - 2025-11-17

## Tech Stack

- **React 18** - UI framework
- **Material-UI (MUI) v5** - Component library
- **React Router v6** - Routing
- **Zustand** - State management
- **React Query** - Server state management
- **Axios** - HTTP client
- **Vite** - Build tool (fast!)
- **Notistack** - Toast notifications

## Features

### Authentication
- Login with email/password
- Password reset flow
- JWT token management with auto-refresh
- Protected routes

### Dashboard
- Farm-wide KPI summary
- Inventory metrics
- User activity stats
- Real-time data with React Query

### Admin Panel
- User management (create, update, delete)
- Role-based access control
- Module permissions management
- Activity logs with filtering

### Inventory Module
- Item master management
- Stock operations (add/use with FIFO)
- Purchase order management
- Low stock alerts
- Expiry alerts
- Transaction history

### Navigation
- Responsive sidebar navigation
- Collapsible module sub-menus
- Mobile-friendly drawer

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your backend URL:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

Output will be in the `dist/` folder.

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and services
│   │   ├── client.js     # Axios instance with interceptors
│   │   ├── auth.js       # Auth API calls
│   │   └── index.js      # All API exports
│   ├── components/       # Reusable components
│   │   └── DashboardLayout.jsx  # Main layout with sidebar
│   ├── pages/            # Page components
│   │   ├── LoginPage.jsx
│   │   ├── DashboardHome.jsx
│   │   ├── AdminPanel.jsx
│   │   └── InventoryModule.jsx
│   ├── store/            # Zustand stores
│   │   └── authStore.js  # Authentication state
│   ├── theme/            # MUI theme configuration
│   │   └── theme.js
│   ├── App.jsx           # Main app with routing
│   └── main.jsx          # Entry point
├── public/               # Static assets
├── index.html            # HTML template
├── vite.config.js        # Vite configuration
└── package.json          # Dependencies
```

## Key Components

### Authentication Flow

1. User enters credentials on login page
2. Frontend calls `/api/v1/auth/login`
3. Backend returns access token + refresh token + user info
4. Tokens stored in localStorage
5. `authStore` updates global state
6. User redirected to dashboard

### API Client Features

- **Auto token injection** - Adds Bearer token to all requests
- **Auto token refresh** - Refreshes expired tokens automatically
- **Error handling** - Catches 401 errors and redirects to login
- **Request/response interceptors** - Centralized error handling

### State Management

- **Zustand** for global state (auth, user)
- **React Query** for server state (caching, refetching)
- **Local component state** for UI state

## Available Scripts

```bash
# Development
npm run dev          # Start dev server (port 3000)

# Production
npm run build        # Build for production
npm run preview      # Preview production build

# Linting
npm run lint         # Run ESLint
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API URL |
| `VITE_APP_NAME` | `Farm Management System` | Application name |
| `VITE_APP_VERSION` | `1.0.0` | Version number |

## API Integration

All API calls are centralized in `src/api/`:

```javascript
import { authAPI, adminAPI, inventoryAPI, dashboardAPI } from './api';

// Auth
await authAPI.login(email, password);
await authAPI.logout();

// Dashboard
const summary = await dashboardAPI.getSummary();

// Admin
const users = await adminAPI.getUsers();
await adminAPI.createUser(data);

// Inventory
const items = await inventoryAPI.getItems();
await inventoryAPI.addStock(data);
await inventoryAPI.useStock(data);  // FIFO deduction
```

## Routing

| Route | Component | Access |
|-------|-----------|--------|
| `/login` | LoginPage | Public |
| `/dashboard` | DashboardHome | Protected |
| `/admin/users` | AdminPanel (Users) | Admin only |
| `/admin/activity` | AdminPanel (Logs) | Admin only |
| `/inventory/items` | InventoryModule | Inventory access |
| `/inventory/stock` | InventoryModule | Inventory access |
| `/inventory/purchase-orders` | InventoryModule | Inventory access |
| `/inventory/alerts` | InventoryModule | Inventory access |

## Authentication Store (Zustand)

```javascript
import useAuthStore from './store/authStore';

// In components
const { user, isAuthenticated, login, logout } = useAuthStore();

// Login
const result = await login(email, password);
if (result.success) {
  // Redirect to dashboard
}

// Logout
await logout();
```

## Styling

Material-UI theme is configured in `src/theme/theme.js`:

- **Primary color**: Green (#2e7d32) - farm theme
- **Secondary color**: Orange (#ff6f00)
- **Border radius**: 8px
- **Font**: Roboto

## Future Enhancements

- [ ] Biofloc module UI
- [ ] Real-time notifications with WebSockets
- [ ] Advanced filtering and search
- [ ] Export to Excel functionality
- [ ] Charts and analytics with Recharts
- [ ] User profile management
- [ ] Dark mode toggle
- [ ] Offline support with PWA

## Troubleshooting

### CORS errors
Make sure backend CORS settings allow `http://localhost:3000`

### 401 Unauthorized
Check if access token is valid and refresh token works

### Module not loading
Verify user has permission to access the module

## License

Proprietary - Farm Management System v1.0.0

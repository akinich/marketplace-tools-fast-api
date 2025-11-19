# Frontend Core Architecture

**Framework:** React 18.2.0
**Build Tool:** Vite 5.0.8
**UI Library:** Material-UI 5.14.20
**Status:** Production Ready ✅

## Overview

The Farm Management System frontend is built with React 18 and Material-UI, providing a modern, responsive user interface. It features robust authentication, state management with React Query and Zustand, and modular architecture for extensibility.

### Key Features

- **React 18** - Latest React with concurrent features
- **Material-UI** - Professional UI components
- **React Router v6** - Client-side routing with nested routes
- **React Query** - Server state management and caching
- **Zustand** - Lightweight client state management
- **JWT Authentication** - Secure token-based auth with auto-refresh
- **Protected Routes** - Role-based access control
- **Responsive Design** - Mobile and desktop support
- **Theme Customization** - Farm-themed color palette

## Quick Start

### Prerequisites

- Node.js 16+ and npm/yarn
- Backend API running on http://localhost:8000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
# Opens http://localhost:3000
```

### Build for Production

```bash
npm run build
# Output in dist/
```

##Project Structure

```
frontend/
├── src/
│   ├── main.jsx                # Entry point
│   ├── App.jsx                 # Root component with routing
│   │
│   ├── pages/                  # Page components
│   │   ├── LoginPage.jsx
│   │   ├── ResetPasswordPage.jsx
│   │   ├── DashboardHome.jsx
│   │   ├── AdminPanel.jsx
│   │   ├── InventoryModule.jsx
│   │   └── BioflocModule.jsx
│   │
│   ├── components/             # Reusable components
│   │   ├── DashboardLayout.jsx
│   │   ├── ProtectedRoute.jsx
│   │   └── StatCard.jsx
│   │
│   ├── store/                  # State management
│   │   └── authStore.js        # Zustand auth store
│   │
│   ├── api/                    # API clients
│   │   ├── client.js           # Axios instance
│   │   └── index.js            # API services
│   │
│   ├── theme/                  # MUI theme
│   │   └── theme.js
│   │
│   └── utils/                  # Utilities
│       └── formatters.js       # Number/date formatters
│
├── public/                     # Static assets
├── index.html                  # HTML template
├── vite.config.js             # Vite configuration
└── package.json               # Dependencies
```

## Core Technologies

### React & Build Tools
- **react** 18.2.0 - UI library
- **react-dom** 18.2.0 - DOM rendering
- **vite** 5.0.8 - Build tool and dev server

### UI & Styling
- **@mui/material** 5.14.20 - Component library
- **@mui/icons-material** 5.14.19 - Icons
- **@emotion/react** & **@emotion/styled** - CSS-in-JS

### State & Data
- **react-query** 3.39.3 - Server state
- **zustand** 4.4.7 - Client state
- **axios** 1.6.2 - HTTP client

### Routing & Navigation
- **react-router-dom** 6.20.0 - Routing

### Utilities
- **date-fns** 2.30.0 - Date manipulation
- **notistack** 3.0.1 - Notifications
- **recharts** 2.10.3 - Charts

## Key Concepts

### Authentication Flow

1. User enters credentials on LoginPage
2. `authAPI.login()` calls backend `/api/v1/auth/login`
3. Tokens and user info stored in localStorage & Zustand
4. All API requests include `Authorization: Bearer {token}` header
5. 401 responses trigger automatic token refresh
6. If refresh fails, redirect to login

### Protected Routes

```jsx
<ProtectedRoute>
  <DashboardLayout>
    <Outlet /> {/* Child routes render here */}
  </DashboardLayout>
</ProtectedRoute>
```

### State Management

**Zustand (Auth):**
- User info, tokens, authentication status
- Persisted in localStorage

**React Query (Server State):**
- API data caching (5-minute stale time)
- Automatic background refetching
- Optimistic updates

### API Client

**Request Interceptor:**
- Adds auth token to headers

**Response Interceptor:**
- Catches 401 errors
- Attempts token refresh
- Retries original request
- Redirects to login if refresh fails

## Documentation

- **[Technical Guide](./technical-guide.md)** - Architecture, components, patterns
- **[Development Guide](./development-guide.md)** - Development workflow, best practices

## Common Tasks

### Adding a New Page

1. Create component in `src/pages/MyNewPage.jsx`
2. Add route in `App.jsx`
3. Add navigation link in `DashboardLayout.jsx` (if needed)

### Adding a New API Service

1. Add function to `src/api/index.js`
2. Use `apiClient` instance
3. Export as part of API object

### Creating Reusable Component

1. Create in `src/components/MyComponent.jsx`
2. Use Material-UI components
3. Accept props for customization
4. Export default

## Environment Variables

Create `.env` in frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Farm Management System
VITE_APP_VERSION=1.0.0
```

## Available Scripts

```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

Part of the Farm Management System
© 2025 All rights reserved

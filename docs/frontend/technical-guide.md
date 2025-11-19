# Frontend Technical Guide

**Version:** 1.0.0
**Audience:** Frontend Developers

---

## Architecture

### Component Hierarchy

```
main.jsx (Entry)
└── App.jsx (Router)
    ├── LoginPage (Public)
    ├── ResetPasswordPage (Public)
    └── ProtectedRoute
        └── DashboardLayout
            ├── AppBar
            ├── Drawer (Sidebar)
            └── Outlet (Dynamic Routes)
                ├── DashboardHome
                ├── Admin Panel
                ├── Inventory Module
                └── Biofloc Module
```

### State Management

**Zustand (authStore.js):**
```javascript
{
  user: Object | null,
  accessToken: string,
  refreshToken: string,
  isAuthenticated: boolean,
  isLoading: boolean,
  error: string | null,
  
  // Actions
  login: (email, password) => Promise,
  logout: () => void,
  refreshAccessToken: () => Promise,
  clearError: () => void
}
```

**React Query:**
- Cache server data (5-min stale time)
- Automatic refetching
- Query invalidation on mutations

### API Client (axios)

**Base Configuration:**
```javascript
const apiClient = axios.create({
  baseURL: `${import.meta.env.VITE_API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
});
```

**Interceptors:**

Request:
```javascript
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

Response (with auto-refresh):
```javascript
apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      const response = await axios.post('/auth/refresh', { refresh_token: refreshToken });
      
      // Save new token
      localStorage.setItem('access_token', response.data.access_token);
      
      // Retry original request
      error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);
```

---

## Component Patterns

### Page Component

```jsx
import { useQuery } from 'react-query';
import { Box, Typography, CircularProgress } from '@mui/material';
import { dashboardAPI } from '../api';

function DashboardHome() {
  const { data, isLoading, error } = useQuery(
    'dashboardSummary',
    dashboardAPI.getSummary
  );

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography color="error">Error loading data</Typography>;

  return (
    <Box>
      <Typography variant="h4">Dashboard</Typography>
      {/* Render data */}
    </Box>
  );
}

export default DashboardHome;
```

### Form Component with Mutation

```jsx
import { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { useSnackbar } from 'notistack';
import { TextField, Button } from '@mui/material';

function CreateItemForm() {
  const [formData, setFormData] = useState({ name: '', sku: '' });
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  const mutation = useMutation(
    data => inventoryAPI.createItem(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('inventoryItems');
        enqueueSnackbar('Item created', { variant: 'success' });
        setFormData({ name: '', sku: '' });
      },
      onError: (error) => {
        enqueueSnackbar(error.message, { variant: 'error' });
      }
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <TextField 
        label="Name"
        value={formData.name}
        onChange={e => setFormData({...formData, name: e.target.value})}
      />
      <Button type="submit" disabled={mutation.isLoading}>
        Create
      </Button>
    </form>
  );
}
```

---

## Routing

### Route Definition (App.jsx)

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route index element={<DashboardHome />} />
            <Route path="/dashboard" element={<DashboardHome />} />
            <Route path="/admin/*" element={<AdminPanel />} />
            <Route path="/inventory/*" element={<InventoryModule />} />
          </Route>
        </Route>
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### Protected Route Component

```jsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

function ProtectedRoute() {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <Outlet />;
}
```

---

## Theme Configuration

```javascript
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32',    // Green
      light: '#60ad5e',
      dark: '#005005'
    },
    secondary: {
      main: '#ff6f00',    // Orange
      light: '#ffa040',
      dark: '#c43e00'
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff'
    }
  },
  typography: {
    fontFamily: 'Roboto, Helvetica, Arial, sans-serif',
    h4: {
      fontWeight: 500
    }
  },
  shape: {
    borderRadius: 8
  }
});

export default theme;
```

---

## Utility Functions

### Formatters (utils/formatters.js)

```javascript
export const formatCurrency = (amount, decimals = 2) => {
  if (amount == null || isNaN(amount)) return '₹0.00';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(amount);
};

export const formatDate = (date) => {
  if (!date) return '';
  return format(new Date(date), 'dd/MM/yyyy');
};

export const formatQuantity = (qty, unit) => {
  if (qty == null) return '';
  return `${formatNumber(qty)} ${unit}`;
};
```

---

## Best Practices

### State Management
- Use React Query for server state
- Use Zustand for client state (auth, UI preferences)
- Avoid prop drilling with context/hooks

### Performance
- Lazy load routes: `const AdminPanel = lazy(() => import('./pages/AdminPanel'))`
- Memoize expensive calculations: `useMemo`
- Memoize callbacks: `useCallback`

### Error Handling
- Use error boundaries for component errors
- Handle API errors in mutations/queries
- Show user-friendly error messages

### Security
- Store tokens in localStorage (httpOnly cookies preferred for production)
- Clear tokens on logout
- Validate user input
- Sanitize data before rendering

### Code Organization
- One component per file
- Group related components in folders
- Keep components small and focused
- Extract reusable logic to custom hooks

---

## Testing

### Component Test Example

```jsx
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import DashboardHome from './DashboardHome';

const queryClient = new QueryClient();

test('renders dashboard title', () => {
  render(
    <QueryClientProvider client={queryClient}>
      <DashboardHome />
    </QueryClientProvider>
  );
  
  expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
});
```

---

**End of Technical Guide**

For development workflow, see [Development Guide](./development-guide.md).

# Frontend Development Guide

**Version:** 1.0.0
**Audience:** Frontend Developers

---

## Development Setup

### Initial Setup

```bash
# Clone and install
git clone <repository>
cd frontend
npm install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start development server
npm run dev
```

### Environment Variables

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Farm Management System
VITE_APP_VERSION=1.0.0
```

---

## Development Workflow

### 1. Create a New Feature

**Example: Add Stock Alerts Page**

```bash
# Create new page
touch src/pages/StockAlertsPage.jsx
```

```jsx
// src/pages/StockAlertsPage.jsx
import { useQuery } from 'react-query';
import { Box, Typography, Card } from '@mui/material';
import { inventoryAPI } from '../api';

function StockAlertsPage() {
  const { data, isLoading } = useQuery(
    'stockAlerts',
    inventoryAPI.getStockAlerts
  );

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Stock Alerts
      </Typography>
      {/* Render alerts */}
    </Box>
  );
}

export default StockAlertsPage;
```

**Add Route:**
```jsx
// App.jsx
<Route path="/inventory/alerts" element={<StockAlertsPage />} />
```

**Add Navigation:**
```jsx
// DashboardLayout.jsx - Add to sidebar
<ListItem button component={Link} to="/inventory/alerts">
  <ListItemIcon><NotificationsIcon /></ListItemIcon>
  <ListItemText primary="Stock Alerts" />
</ListItem>
```

### 2. Add New API Endpoint

```javascript
// src/api/index.js
export const inventoryAPI = {
  ...existing,
  
  getStockAlerts: () => apiClient.get('/inventory/alerts/low-stock'),
  
  getExpiryAlerts: (days = 30) => 
    apiClient.get(`/inventory/alerts/expiry?days=${days}`)
};
```

### 3. Create Reusable Component

```jsx
// src/components/AlertCard.jsx
import { Card, CardContent, Typography, Chip } from '@mui/material';

function AlertCard({ title, severity, message }) {
  const severityColor = {
    low: 'success',
    medium: 'warning',
    high: 'error'
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between">
          <Typography variant="h6">{title}</Typography>
          <Chip 
            label={severity.toUpperCase()}
            color={severityColor[severity]}
            size="small"
          />
        </Box>
        <Typography color="textSecondary">{message}</Typography>
      </CardContent>
    </Card>
  );
}

export default AlertCard;
```

---

## Code Style Guide

### Component Structure

```jsx
// 1. Imports
import { useState, useEffect } from 'react';
import { useQuery, useMutation } from 'react-query';
import { Box, Typography, Button } from '@mui/material';
import { customAPI } from '../api';

// 2. Component
function MyComponent({ prop1, prop2 }) {
  // 3. State
  const [localState, setLocalState] = useState(initialValue);
  
  // 4. Queries/Mutations
  const { data, isLoading } = useQuery('key', fetchFunction);
  
  // 5. Effects
  useEffect(() => {
    // Side effects
  }, [dependencies]);
  
  // 6. Event Handlers
  const handleClick = () => {
    // Handle event
  };
  
  // 7. Render
  if (isLoading) return <CircularProgress />;
  
  return (
    <Box>
      {/* JSX */}
    </Box>
  );
}

// 8. Export
export default MyComponent;
```

### Naming Conventions

- **Components:** PascalCase (`UserProfile`, `DashboardHome`)
- **Functions:** camelCase (`handleSubmit`, `fetchUserData`)
- **Constants:** UPPER_SNAKE_CASE (`API_BASE_URL`, `MAX_RETRIES`)
- **Files:** PascalCase for components (`UserProfile.jsx`), camelCase for utils (`formatters.js`)

### Props

```jsx
// Use destructuring
function MyComponent({ title, onSave, data }) {
  // ...
}

// Prop types (optional, or use TypeScript)
MyComponent.propTypes = {
  title: PropTypes.string.isRequired,
  onSave: PropTypes.func.isRequired,
  data: PropTypes.object
};
```

---

## Common Patterns

### Data Fetching with React Query

```jsx
const { data, isLoading, error, refetch } = useQuery(
  ['items', filters],  // Query key (dependencies)
  () => inventoryAPI.getItems(filters),
  {
    staleTime: 5 * 60 * 1000,  // 5 minutes
    enabled: !!user,  // Only run if user exists
    onSuccess: (data) => {
      console.log('Data loaded:', data);
    }
  }
);
```

### Form Handling

```jsx
function MyForm() {
  const [formData, setFormData] = useState({
    name: '',
    email: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Submit formData
  };

  return (
    <form onSubmit={handleSubmit}>
      <TextField
        name="name"
        value={formData.name}
        onChange={handleChange}
      />
    </form>
  );
}
```

### Modal/Dialog Pattern

```jsx
function MyPage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setDialogOpen(true)}>
        Open Dialog
      </Button>
      
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>Title</DialogTitle>
        <DialogContent>
          {/* Dialog content */}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
```

---

## Debugging

### React Developer Tools

Install browser extension:
- Chrome: React Developer Tools
- Firefox: React Developer Tools

**Usage:**
- Inspect component props/state
- View component tree
- Profile performance

### React Query DevTools

```jsx
// Add to App.jsx (development only)
import { ReactQueryDevtools } from 'react-query/devtools';

function App() {
  return (
    <>
      {/* Your app */}
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  );
}
```

### Console Debugging

```javascript
// Temporary debugging
console.log('State:', formData);
console.table(items);  // Table format for arrays

// Debug API calls
apiClient.interceptors.request.use(config => {
  console.log('Request:', config.url, config.data);
  return config;
});
```

---

## Performance Optimization

### Lazy Loading

```jsx
import { lazy, Suspense } from 'react';

const AdminPanel = lazy(() => import('./pages/AdminPanel'));

function App() {
  return (
    <Suspense fallback={<CircularProgress />}>
      <AdminPanel />
    </Suspense>
  );
}
```

### Memoization

```jsx
import { useMemo, useCallback } from 'react';

function MyComponent({ items, onItemClick }) {
  // Memoize expensive calculation
  const sortedItems = useMemo(() => {
    return items.sort((a, b) => a.name.localeCompare(b.name));
  }, [items]);

  // Memoize callback
  const handleClick = useCallback((item) => {
    onItemClick(item);
  }, [onItemClick]);

  return <List items={sortedItems} onClick={handleClick} />;
}
```

---

## Error Handling

### Error Boundary

```jsx
import { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}

// Usage
<ErrorBoundary>
  <MyComponent />
</ErrorBoundary>
```

### API Error Handling

```jsx
const mutation = useMutation(
  data => inventoryAPI.createItem(data),
  {
    onError: (error) => {
      const message = error.response?.data?.detail || 'An error occurred';
      enqueueSnackbar(message, { variant: 'error' });
    }
  }
);
```

---

## Testing

### Component Test

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MyComponent from './MyComponent';

test('renders component with title', () => {
  render(<MyComponent title="Test Title" />);
  
  const titleElement = screen.getByText(/test title/i);
  expect(titleElement).toBeInTheDocument();
});

test('handles button click', () => {
  const handleClick = jest.fn();
  render(<MyComponent onClick={handleClick} />);
  
  const button = screen.getByRole('button');
  fireEvent.click(button);
  
  expect(handleClick).toHaveBeenCalledTimes(1);
});
```

---

## Deployment

### Build for Production

```bash
npm run build
```

Output in `dist/` directory.

### Deploy to Server

```bash
# Copy dist/ to web server
scp -r dist/* user@server:/var/www/html/

# Or use deployment tool
# - Vercel
# - Netlify
# - AWS S3 + CloudFront
```

### Environment-Specific Builds

```bash
# Development
VITE_API_BASE_URL=http://localhost:8000 npm run build

# Production
VITE_API_BASE_URL=https://api.production.com npm run build
```

---

## Troubleshooting

### Common Issues

**Issue: "Module not found"**
- Check import path
- Run `npm install`
- Restart dev server

**Issue: API calls failing**
- Check VITE_API_BASE_URL in .env
- Verify backend is running
- Check browser console for CORS errors

**Issue: Changes not reflecting**
- Hard refresh browser (Ctrl+Shift+R)
- Clear browser cache
- Restart Vite dev server

**Issue: Build fails**
- Check for TypeScript errors (if using TS)
- Verify all imports are correct
- Run `npm run lint` to find issues

---

## Best Practices Checklist

### Code Quality
- [ ] Components are small and focused
- [ ] Reusable logic extracted to custom hooks
- [ ] Props are documented
- [ ] Error handling in place
- [ ] Loading states handled

### Performance
- [ ] Large components lazy loaded
- [ ] Expensive calculations memoized
- [ ] Unnecessary re-renders avoided
- [ ] Images optimized

### Accessibility
- [ ] Semantic HTML elements
- [ ] ARIA labels where needed
- [ ] Keyboard navigation supported
- [ ] Color contrast meets WCAG standards

### Security
- [ ] User input sanitized
- [ ] Auth tokens handled securely
- [ ] Sensitive data not in client code
- [ ] HTTPS in production

---

**End of Development Guide**

/**
 * Main Entry Point
 * Version: 1.1.0
 * Last Updated: 2025-11-17
 *
 * Changelog:
 * ----------
 * v1.1.0 (2025-11-17):
 *   - Added autoHideDuration to SnackbarProvider (3 seconds auto-dismiss)
 *   - Added close button with CloseIcon to toast notifications
 *   - Improved UX for notification dismissal
 *
 * v1.0.0 (2025-11-17):
 *   - Initial application entry point
 *   - React 18 setup with providers
 *   - React Query, Theme, and Snackbar configuration
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { SnackbarProvider, useSnackbar } from 'notistack';
import { QueryClient, QueryClientProvider } from 'react-query';
import { IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

import App from './App';
import theme from './theme/theme';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Close button component that uses notistack's closeSnackbar
function SnackbarCloseButton({ snackbarKey }) {
  const { closeSnackbar } = useSnackbar();

  return (
    <IconButton
      size="small"
      aria-label="close"
      color="inherit"
      onClick={() => closeSnackbar(snackbarKey)}
    >
      <CloseIcon fontSize="small" />
    </IconButton>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <SnackbarProvider
            maxSnack={3}
            anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
            autoHideDuration={3000}
            action={(snackbarKey) => <SnackbarCloseButton snackbarKey={snackbarKey} />}
          >
            <App />
          </SnackbarProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>
);

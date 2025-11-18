/**
 * Error Boundary Component
 * Catches React errors and displays a fallback UI instead of crashing the entire app
 */

import React from 'react';
import { Box, Typography, Button, Alert } from '@mui/material';
import { Error as ErrorIcon, Refresh as RefreshIcon } from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px',
            p: 4,
          }}
        >
          <ErrorIcon sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
          <Typography variant="h5" gutterBottom fontWeight="bold">
            Oops! Something went wrong
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
            We encountered an unexpected error. Please try refreshing the page.
          </Typography>

          {this.state.error && (
            <Alert severity="error" sx={{ mb: 3, maxWidth: 600 }}>
              <Typography variant="body2" fontWeight="bold" gutterBottom>
                Error Details:
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                {this.state.error.toString()}
              </Typography>
            </Alert>
          )}

          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={this.handleReset}
            size="large"
          >
            Reload Page
          </Button>

          {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
            <Box sx={{ mt: 4, maxWidth: 800, width: '100%' }}>
              <Alert severity="warning">
                <Typography variant="caption" fontWeight="bold" gutterBottom>
                  Stack Trace (Development Only):
                </Typography>
                <pre style={{ fontSize: '0.75rem', overflow: 'auto' }}>
                  {this.state.errorInfo.componentStack}
                </pre>
              </Alert>
            </Box>
          )}
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

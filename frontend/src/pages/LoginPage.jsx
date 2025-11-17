/**
 * Login Page with Password Reset
 * Version: 1.0.0
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Container,
  Alert,
  Link,
  CircularProgress,
} from '@mui/material';
import { Agriculture as AgricultureIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';

import useAuthStore from '../store/authStore';
import { authAPI } from '../api/auth';

export default function LoginPage() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { login, isLoading, error: authError } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState('');
  const [forgotPasswordLoading, setForgotPasswordLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();

    const result = await login(email, password);

    if (result.success) {
      enqueueSnackbar('Login successful!', { variant: 'success' });
      navigate('/dashboard');
    } else {
      enqueueSnackbar(result.error || 'Login failed', { variant: 'error' });
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();

    if (!forgotPasswordEmail) {
      enqueueSnackbar('Please enter your email', { variant: 'warning' });
      return;
    }

    setForgotPasswordLoading(true);

    try {
      await authAPI.forgotPassword(forgotPasswordEmail);
      enqueueSnackbar('Password reset email sent! Check your inbox.', { variant: 'success' });
      setShowForgotPassword(false);
      setForgotPasswordEmail('');
    } catch (error) {
      enqueueSnackbar('Failed to send reset email', { variant: 'error' });
    } finally {
      setForgotPasswordLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #2e7d32 0%, #60ad5e 100%)',
        padding: 2,
      }}
    >
      <Container maxWidth="sm">
        <Card elevation={8} sx={{ borderRadius: 2 }}>
          <CardContent sx={{ p: 4 }}>
            {/* Logo and Title */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <AgricultureIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
                Farm Management System
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sign in to access your dashboard
              </Typography>
            </Box>

            {/* Error Alert */}
            {authError && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {authError}
              </Alert>
            )}

            {!showForgotPassword ? (
              /* Login Form */
              <form onSubmit={handleLogin}>
                <TextField
                  label="Email"
                  type="email"
                  fullWidth
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  margin="normal"
                  autoComplete="email"
                  autoFocus
                />

                <TextField
                  label="Password"
                  type="password"
                  fullWidth
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  margin="normal"
                  autoComplete="current-password"
                />

                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  size="large"
                  disabled={isLoading}
                  sx={{ mt: 3, mb: 2, py: 1.5 }}
                >
                  {isLoading ? <CircularProgress size={24} /> : 'Sign In'}
                </Button>

                <Box sx={{ textAlign: 'center', mt: 2 }}>
                  <Link
                    component="button"
                    type="button"
                    variant="body2"
                    onClick={() => setShowForgotPassword(true)}
                  >
                    Forgot your password?
                  </Link>
                </Box>
              </form>
            ) : (
              /* Forgot Password Form */
              <form onSubmit={handleForgotPassword}>
                <Typography variant="h6" gutterBottom>
                  Reset Password
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Enter your email address and we'll send you a password reset link.
                </Typography>

                <TextField
                  label="Email"
                  type="email"
                  fullWidth
                  value={forgotPasswordEmail}
                  onChange={(e) => setForgotPasswordEmail(e.target.value)}
                  required
                  margin="normal"
                  autoFocus
                />

                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  size="large"
                  disabled={forgotPasswordLoading}
                  sx={{ mt: 3, mb: 2, py: 1.5 }}
                >
                  {forgotPasswordLoading ? <CircularProgress size={24} /> : 'Send Reset Link'}
                </Button>

                <Box sx={{ textAlign: 'center', mt: 2 }}>
                  <Link
                    component="button"
                    type="button"
                    variant="body2"
                    onClick={() => setShowForgotPassword(false)}
                  >
                    Back to Login
                  </Link>
                </Box>
              </form>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <Typography variant="body2" align="center" sx={{ mt: 3, color: 'white' }}>
          Farm Management System v1.0.0
        </Typography>
      </Container>
    </Box>
  );
}

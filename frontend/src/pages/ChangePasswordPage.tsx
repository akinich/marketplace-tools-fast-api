/**
 * Change Password Page
 * Version: 1.0.0
 * Last Updated: 2025-11-21
 *
 * Allows logged-in users to change their password.
 * Requires current password for verification.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  InputAdornment,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  CheckCircle,
  Cancel,
  Lock,
} from '@mui/icons-material';
import { authAPI } from '../api/auth';
import useAuthStore from '../store/authStore';

export default function ChangePasswordPage() {
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Password requirements check
  const passwordChecks = {
    length: formData.newPassword.length >= 8,
    uppercase: /[A-Z]/.test(formData.newPassword),
    lowercase: /[a-z]/.test(formData.newPassword),
    digit: /\d/.test(formData.newPassword),
    special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(formData.newPassword),
    match: formData.newPassword === formData.confirmPassword && formData.confirmPassword !== '',
  };

  const allChecksPass = Object.values(passwordChecks).every(Boolean);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!allChecksPass) {
      setError('Please ensure all password requirements are met');
      return;
    }

    setLoading(true);

    try {
      await authAPI.changePassword(formData.currentPassword, formData.newPassword);
      setSuccess(true);

      // Log out after successful password change so they can log in with new password
      setTimeout(() => {
        logout();
        navigate('/login');
      }, 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const RequirementItem = ({ met, text }) => (
    <ListItem dense sx={{ py: 0 }}>
      <ListItemIcon sx={{ minWidth: 32 }}>
        {met ? (
          <CheckCircle color="success" fontSize="small" />
        ) : (
          <Cancel color="error" fontSize="small" />
        )}
      </ListItemIcon>
      <ListItemText
        primary={text}
        primaryTypographyProps={{
          variant: 'body2',
          color: met ? 'success.main' : 'text.secondary',
        }}
      />
    </ListItem>
  );

  if (success) {
    return (
      <Container maxWidth="sm">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '80vh',
          }}
        >
          <Paper elevation={3} sx={{ p: 4, width: '100%', textAlign: 'center' }}>
            <CheckCircle sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
            <Typography variant="h5" component="h1" gutterBottom color="success.main">
              Password Changed Successfully!
            </Typography>
            <Typography variant="body1" sx={{ mt: 2, mb: 3 }}>
              Your password has been updated. You will be logged out and redirected to the login page.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Redirecting...
            </Typography>
          </Paper>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          py: 4,
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
            <Lock sx={{ fontSize: 40, color: 'primary.main', mr: 1 }} />
            <Typography variant="h4" component="h1">
              Change Password
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
            Enter your current password and choose a new one
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Current Password"
              name="currentPassword"
              type={showCurrentPassword ? 'text' : 'password'}
              value={formData.currentPassword}
              onChange={handleChange}
              required
              sx={{ mb: 2 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      edge="end"
                    >
                      {showCurrentPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              fullWidth
              label="New Password"
              name="newPassword"
              type={showNewPassword ? 'text' : 'password'}
              value={formData.newPassword}
              onChange={handleChange}
              required
              sx={{ mb: 2 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      edge="end"
                    >
                      {showNewPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              fullWidth
              label="Confirm New Password"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              sx={{ mb: 2 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      edge="end"
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            {/* Password Requirements */}
            <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
              <Typography variant="subtitle2" gutterBottom>
                Password Requirements:
              </Typography>
              <List dense disablePadding>
                <RequirementItem met={passwordChecks.length} text="At least 8 characters" />
                <RequirementItem met={passwordChecks.uppercase} text="One uppercase letter" />
                <RequirementItem met={passwordChecks.lowercase} text="One lowercase letter" />
                <RequirementItem met={passwordChecks.digit} text="One number" />
                <RequirementItem met={passwordChecks.special} text="One special character (!@#$%^&*)" />
                <RequirementItem met={passwordChecks.match} text="Passwords match" />
              </List>
            </Paper>

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading || !allChecksPass || !formData.currentPassword}
              sx={{ mb: 2 }}
            >
              {loading ? 'Changing Password...' : 'Change Password'}
            </Button>

            <Button
              fullWidth
              variant="text"
              onClick={() => navigate(-1)}
              disabled={loading}
            >
              Cancel
            </Button>
          </form>
        </Paper>
      </Box>
    </Container>
  );
}

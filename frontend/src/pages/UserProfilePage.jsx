/**
 * User Profile Page
 * Version: 1.0.0
 * Last Updated: 2025-11-21
 *
 * Displays user profile information and allows editing full name.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Divider,
  Grid,
  Skeleton,
  Chip,
} from '@mui/material';
import {
  Person,
  Email,
  Badge,
  CalendarMonth,
  Lock,
  Edit,
  Save,
  Cancel,
} from '@mui/icons-material';
import { authAPI } from '../api/auth';
import useAuthStore from '../store/authStore';

export default function UserProfilePage() {
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const data = await authAPI.getProfile();
      setProfile(data);
      setFullName(data.full_name);
    } catch (err) {
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!fullName.trim()) {
      setError('Name cannot be empty');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const result = await authAPI.updateProfile(fullName.trim());
      setProfile({ ...profile, full_name: result.full_name });
      setEditing(false);
      setSuccess('Profile updated successfully');

      // Update user in auth store
      if (user) {
        setUser({ ...user, full_name: result.full_name });
      }

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFullName(profile?.full_name || '');
    setEditing(false);
    setError('');
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const InfoRow = ({ icon: Icon, label, value, chip }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', py: 1.5 }}>
      <Icon sx={{ color: 'text.secondary', mr: 2 }} />
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {label}
        </Typography>
        {chip ? (
          <Box>
            <Chip label={value} size="small" color="primary" variant="outlined" />
          </Box>
        ) : (
          <Typography variant="body1">{value || '-'}</Typography>
        )}
      </Box>
    </Box>
  );

  if (loading) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ py: 4 }}>
          <Paper elevation={3} sx={{ p: 4 }}>
            <Skeleton variant="text" width="60%" height={40} />
            <Skeleton variant="text" width="100%" height={60} sx={{ mt: 2 }} />
            <Skeleton variant="text" width="100%" height={60} />
            <Skeleton variant="text" width="100%" height={60} />
          </Paper>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Person sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
            <Typography variant="h4" component="h1">
              My Profile
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
              {success}
            </Alert>
          )}

          {/* Editable Name Section */}
          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Full Name
              </Typography>
              {!editing && (
                <Button
                  size="small"
                  startIcon={<Edit />}
                  onClick={() => setEditing(true)}
                >
                  Edit
                </Button>
              )}
            </Box>

            {editing ? (
              <Box>
                <TextField
                  fullWidth
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  size="small"
                  autoFocus
                  sx={{ mb: 1 }}
                />
                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                  <Button
                    size="small"
                    onClick={handleCancel}
                    startIcon={<Cancel />}
                    disabled={saving}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="small"
                    variant="contained"
                    onClick={handleSave}
                    startIcon={<Save />}
                    disabled={saving || !fullName.trim()}
                  >
                    {saving ? 'Saving...' : 'Save'}
                  </Button>
                </Box>
              </Box>
            ) : (
              <Typography variant="h6">{profile?.full_name}</Typography>
            )}
          </Paper>

          <Divider sx={{ my: 2 }} />

          {/* Read-only Info */}
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Account Information
          </Typography>

          <InfoRow icon={Email} label="Email" value={profile?.email} />
          <InfoRow icon={Badge} label="Role" value={profile?.role} chip />

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Security
          </Typography>

          <InfoRow
            icon={CalendarMonth}
            label="Account Created"
            value={formatDate(profile?.created_at)}
          />
          <InfoRow
            icon={Lock}
            label="Last Password Change"
            value={formatDate(profile?.last_password_change)}
          />

          <Divider sx={{ my: 2 }} />

          <Button
            fullWidth
            variant="outlined"
            onClick={() => navigate('/change-password')}
            startIcon={<Lock />}
          >
            Change Password
          </Button>

          <Button
            fullWidth
            variant="text"
            onClick={() => navigate(-1)}
            sx={{ mt: 1 }}
          >
            Back
          </Button>
        </Paper>
      </Box>
    </Container>
  );
}

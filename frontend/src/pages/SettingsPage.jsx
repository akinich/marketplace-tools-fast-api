/**
 * ============================================================================
 * Farm Management System - Settings Page
 * ============================================================================
 * Version: 1.1.0
 * Last Updated: 2025-11-22
 *
 * Changelog:
 * ----------
 * v1.1.0 (2025-11-22):
 *   - Added Audit Log tab to view settings change history
 *   - Display audit log with setting key, old/new values, user, and timestamp
 *   - Auto-load audit logs when tab is selected
 *   - Formatted value display with monospace font for readability
 *
 * v1.0.0 (2025-11-22):
 *   - Initial settings page
 *   - Tabbed interface for setting categories
 *   - Form inputs with validation
 *   - Real-time save/reset functionality
 *   - Admin-only access
 * ============================================================================
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Tabs,
  Tab,
  Typography,
  TextField,
  Switch,
  Button,
  FormControlLabel,
  Grid,
  Alert,
  CircularProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';
import { settingsAPI } from '../api/settings';

const CATEGORY_LABELS = {
  auth: 'Authentication',
  email: 'Email / SMTP',
  webhooks: 'Webhooks',
  app: 'Application',
  features: 'Feature Flags',
  audit: 'Audit Log'
};

function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [currentTab, setCurrentTab] = useState('auth');
  const [settingsByCategory, setSettingsByCategory] = useState({});
  const [formData, setFormData] = useState({});
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loadingAuditLogs, setLoadingAuditLogs] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    if (currentTab === 'audit') {
      loadAuditLogs();
    }
  }, [currentTab]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const allSettings = await settingsAPI.getAll();

      // Group by category
      const grouped = {};
      allSettings.forEach(setting => {
        if (!grouped[setting.category]) {
          grouped[setting.category] = [];
        }
        grouped[setting.category].push(setting);
      });

      setSettingsByCategory(grouped);

      // Initialize form data
      const initialData = {};
      allSettings.forEach(setting => {
        initialData[setting.setting_key] = parseSettingValue(setting);
      });
      setFormData(initialData);

      setLoading(false);
    } catch (error) {
      console.error('Failed to load settings:', error);
      setError(error.response?.data?.detail || 'Failed to load settings');
      setLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    try {
      setLoadingAuditLogs(true);
      setError(null);
      const logs = await settingsAPI.getAuditLog(null, 100);
      setAuditLogs(logs);
      setLoadingAuditLogs(false);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
      setError(error.response?.data?.detail || 'Failed to load audit logs');
      setLoadingAuditLogs(false);
    }
  };

  const parseSettingValue = (setting) => {
    let value = setting.setting_value;

    // Parse JSON string if needed
    if (typeof value === 'string') {
      try {
        value = JSON.parse(value);
      } catch (e) {
        // If JSON parse fails, use the string as-is
      }
    }

    if (setting.data_type === 'boolean') {
      // Handle boolean values properly
      if (typeof value === 'boolean') {
        return value;
      }
      if (typeof value === 'string') {
        return value.toLowerCase() === 'true';
      }
      return Boolean(value);
    } else if (setting.data_type === 'integer') {
      return parseInt(value, 10) || 0;
    } else if (setting.data_type === 'float') {
      return parseFloat(value) || 0;
    } else if (setting.data_type === 'string') {
      return String(value);
    } else {
      return value;
    }
  };

  const handleChange = (settingKey, value) => {
    setFormData(prev => ({
      ...prev,
      [settingKey]: value
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      // Get current category settings
      const categorySettings = settingsByCategory[currentTab] || [];

      // Update each changed setting
      const updates = [];
      for (const setting of categorySettings) {
        const newValue = formData[setting.setting_key];
        const oldValue = parseSettingValue(setting);

        if (newValue !== oldValue) {
          updates.push(
            settingsAPI.update(setting.setting_key, newValue)
          );
        }
      }

      if (updates.length === 0) {
        setSuccess('No changes to save');
        setSaving(false);
        return;
      }

      await Promise.all(updates);

      setSuccess(`${updates.length} setting(s) updated successfully`);
      setHasChanges(false);

      // Reload settings
      await loadSettings();

      setSaving(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
      setError(error.response?.data?.detail || 'Failed to save settings');
      setSaving(false);
    }
  };

  const handleReset = () => {
    // Reset form data to original values
    const categorySettings = settingsByCategory[currentTab] || [];
    const resetData = { ...formData };

    categorySettings.forEach(setting => {
      resetData[setting.setting_key] = parseSettingValue(setting);
    });

    setFormData(resetData);
    setHasChanges(false);
    setError(null);
    setSuccess(null);
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) {
      return 'null';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const renderSettingInput = (setting) => {
    const value = formData[setting.setting_key];
    const validationRules = setting.validation_rules || {};

    if (setting.data_type === 'boolean') {
      return (
        <FormControlLabel
          control={
            <Switch
              checked={Boolean(value)}
              onChange={(e) => handleChange(setting.setting_key, e.target.checked)}
            />
          }
          label={setting.description || setting.setting_key}
        />
      );
    }

    return (
      <TextField
        fullWidth
        label={setting.description || setting.setting_key}
        value={value || ''}
        onChange={(e) => {
          let newValue = e.target.value;
          if (setting.data_type === 'integer') {
            newValue = parseInt(newValue, 10) || 0;
          } else if (setting.data_type === 'float') {
            newValue = parseFloat(newValue) || 0;
          }
          handleChange(setting.setting_key, newValue);
        }}
        type={setting.data_type === 'integer' || setting.data_type === 'float' ? 'number' : 'text'}
        InputProps={{
          inputProps: {
            min: validationRules.min,
            max: validationRules.max,
            step: setting.data_type === 'float' ? 0.1 : 1
          }
        }}
        helperText={
          validationRules.min !== undefined && validationRules.max !== undefined
            ? `Range: ${validationRules.min} - ${validationRules.max}`
            : ''
        }
      />
    );
  };

  const renderAuditLog = () => {
    if (loadingAuditLogs) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" py={4}>
          <CircularProgress />
        </Box>
      );
    }

    if (auditLogs.length === 0) {
      return (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
          No audit log entries found.
        </Typography>
      );
    }

    return (
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Setting Key</TableCell>
              <TableCell>Old Value</TableCell>
              <TableCell>New Value</TableCell>
              <TableCell>Changed By</TableCell>
              <TableCell>Changed At</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {auditLogs.map((log) => (
              <TableRow key={log.id}>
                <TableCell>
                  <Chip label={log.setting_key} size="small" variant="outlined" />
                </TableCell>
                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                  {formatValue(log.old_value)}
                </TableCell>
                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                  {formatValue(log.new_value)}
                </TableCell>
                <TableCell>{log.changed_by}</TableCell>
                <TableCell>{formatDate(log.changed_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  const categorySettings = settingsByCategory[currentTab] || [];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          System Settings
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Configure application settings. Changes take effect immediately.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {hasChanges && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            You have unsaved changes. Click Save to apply them.
          </Alert>
        )}

        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
            {Object.keys(CATEGORY_LABELS).map(category => (
              <Tab
                key={category}
                label={CATEGORY_LABELS[category]}
                value={category}
              />
            ))}
          </Tabs>
        </Box>

        {currentTab === 'audit' ? (
          renderAuditLog()
        ) : (
          <>
            <Grid container spacing={3}>
              {categorySettings.map(setting => (
                <Grid item xs={12} md={6} key={setting.setting_key}>
                  {renderSettingInput(setting)}
                </Grid>
              ))}
            </Grid>

            {categorySettings.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                No settings available in this category.
              </Typography>
            )}

            <Divider sx={{ my: 3 }} />

            <Box display="flex" justifyContent="flex-end" gap={2}>
              <Button
                variant="outlined"
                onClick={handleReset}
                disabled={!hasChanges || saving}
              >
                Reset
              </Button>
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={!hasChanges || saving}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </Box>
          </>
        )}
      </Paper>
    </Container>
  );
}

export default SettingsPage;

/**
 * API Keys Management Page
 * File: frontend/src/pages/APIKeysPage.jsx
 * Description: User interface for managing API keys with scope-based permissions
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Typography,
  Box,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Grid,
  Card,
  CardContent,
  TableContainer,
  OutlinedInput,
  Checkbox,
  ListItemText
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  Visibility as VisibilityIcon,
  VpnKey as VpnKeyIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { apiKeysAPI } from '../api/apiKeys';

function APIKeysPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [apiKeys, setApiKeys] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [keyCreatedDialogOpen, setKeyCreatedDialogOpen] = useState(false);
  const [usageDialogOpen, setUsageDialogOpen] = useState(false);
  const [newApiKey, setNewApiKey] = useState('');
  const [availableScopes, setAvailableScopes] = useState([]);
  const [selectedKeyUsage, setSelectedKeyUsage] = useState([]);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    scopes: [],
    expires_in_days: 365
  });

  useEffect(() => {
    loadApiKeys();
    loadAvailableScopes();
  }, []);

  const loadApiKeys = async () => {
    try {
      setLoading(true);
      const data = await apiKeysAPI.list();
      setApiKeys(data);
    } catch (error) {
      enqueueSnackbar('Failed to load API keys', { variant: 'error' });
      console.error('Load API keys error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableScopes = async () => {
    try {
      const data = await apiKeysAPI.getAvailableScopes();
      setAvailableScopes(data.scopes);
    } catch (error) {
      console.error('Failed to load scopes:', error);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || formData.scopes.length === 0) {
      enqueueSnackbar('Name and at least one scope are required', { variant: 'warning' });
      return;
    }

    try {
      setLoading(true);
      const result = await apiKeysAPI.create(formData);
      setNewApiKey(result.api_key);
      setKeyCreatedDialogOpen(true);
      setDialogOpen(false);
      loadApiKeys();
      setFormData({ name: '', description: '', scopes: [], expires_in_days: 365 });
      enqueueSnackbar('API key created successfully', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar(
        error.response?.data?.detail || 'Failed to create API key',
        { variant: 'error' }
      );
      console.error('Create API key error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (id, name) => {
    if (!window.confirm(`Revoke API key "${name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      await apiKeysAPI.revoke(id);
      enqueueSnackbar('API key revoked successfully', { variant: 'success' });
      loadApiKeys();
    } catch (error) {
      enqueueSnackbar('Failed to revoke API key', { variant: 'error' });
      console.error('Revoke API key error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewUsage = async (id) => {
    try {
      setLoading(true);
      const usage = await apiKeysAPI.getUsage(id);
      setSelectedKeyUsage(usage);
      setUsageDialogOpen(true);
    } catch (error) {
      enqueueSnackbar('Failed to load usage data', { variant: 'error' });
      console.error('Load usage error:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    enqueueSnackbar('Copied to clipboard', { variant: 'success' });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  // Group scopes by resource for better UI
  const groupedScopes = availableScopes.reduce((acc, scope) => {
    const [resource] = scope.split(':');
    if (!acc[resource]) {
      acc[resource] = [];
    }
    acc[resource].push(scope);
    return acc;
  }, {});

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box display="flex" alignItems="center" gap={2}>
            <VpnKeyIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Typography variant="h4">API Keys</Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDialogOpen(true)}
            disabled={loading}
          >
            Create API Key
          </Button>
        </Box>

        {/* Info Alert */}
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>API keys allow programmatic access to your account.</strong>
            <br />
            • Keys are shown only once during creation - store them securely
            <br />
            • Use scopes to limit what each key can access
            <br />
            • Include keys in requests via the <code>X-API-Key</code> header
          </Typography>
        </Alert>

        {/* Statistics */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Keys
                </Typography>
                <Typography variant="h4">
                  {apiKeys.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Active Keys
                </Typography>
                <Typography variant="h4" color="success.main">
                  {apiKeys.filter(k => k.is_active).length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Revoked Keys
                </Typography>
                <Typography variant="h4" color="error.main">
                  {apiKeys.filter(k => !k.is_active).length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* API Keys Table */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Key Prefix</strong></TableCell>
                <TableCell><strong>Scopes</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Expires</strong></TableCell>
                <TableCell><strong>Last Used</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {apiKeys.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="textSecondary" sx={{ py: 3 }}>
                      No API keys yet. Create one to get started!
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                apiKeys.map(key => (
                  <TableRow key={key.id} sx={{ opacity: key.is_active ? 1 : 0.5 }}>
                    <TableCell>
                      <Typography variant="body1"><strong>{key.name}</strong></Typography>
                      {key.description && (
                        <Typography variant="caption" color="textSecondary">
                          {key.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <code style={{ fontSize: '0.9em' }}>{key.key_prefix}</code>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {key.scopes.slice(0, 2).map(scope => (
                          <Chip key={scope} label={scope} size="small" />
                        ))}
                        {key.scopes.length > 2 && (
                          <Chip
                            label={`+${key.scopes.length - 2} more`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={key.is_active ? 'Active' : 'Revoked'}
                        color={key.is_active ? 'success' : 'error'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {key.expires_at ? formatDate(key.expires_at) : 'Never'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(key.last_used_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={1}>
                        <Tooltip title="View Usage">
                          <IconButton
                            size="small"
                            onClick={() => handleViewUsage(key.id)}
                            disabled={loading}
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {key.is_active && (
                          <Tooltip title="Revoke Key">
                            <IconButton
                              size="small"
                              onClick={() => handleRevoke(key.id, key.name)}
                              disabled={loading}
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Create API Key Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create API Key</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name *"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            sx={{ mt: 2, mb: 2 }}
            placeholder="e.g., Production Integration"
          />

          <TextField
            fullWidth
            label="Description"
            multiline
            rows={2}
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            sx={{ mb: 2 }}
            placeholder="Optional description of what this key is used for"
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Scopes *</InputLabel>
            <Select
              multiple
              value={formData.scopes}
              onChange={(e) => setFormData({...formData, scopes: e.target.value})}
              input={<OutlinedInput label="Scopes *" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {Object.entries(groupedScopes).map(([resource, scopes]) => [
                <MenuItem key={resource} disabled>
                  <strong>{resource.toUpperCase()}</strong>
                </MenuItem>,
                ...scopes.map(scope => (
                  <MenuItem key={scope} value={scope}>
                    <Checkbox checked={formData.scopes.indexOf(scope) > -1} />
                    <ListItemText primary={scope} />
                  </MenuItem>
                ))
              ])}
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Expires in (days)"
            type="number"
            value={formData.expires_in_days}
            onChange={(e) => setFormData({...formData, expires_in_days: parseInt(e.target.value) || null})}
            inputProps={{ min: 1, max: 365 }}
            helperText="Leave empty for no expiration, or set 1-365 days"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            variant="contained"
            disabled={!formData.name || formData.scopes.length === 0 || loading}
          >
            Create Key
          </Button>
        </DialogActions>
      </Dialog>

      {/* Key Created Dialog */}
      <Dialog
        open={keyCreatedDialogOpen}
        onClose={() => setKeyCreatedDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>API Key Created Successfully</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <strong>Important:</strong> This is the only time you'll see this key.
            Copy it now and store it securely. If you lose it, you'll need to create a new one.
          </Alert>

          <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
            Your API Key:
          </Typography>

          <Box display="flex" alignItems="center" gap={1}>
            <TextField
              fullWidth
              value={newApiKey}
              InputProps={{
                readOnly: true,
                style: { fontFamily: 'monospace', fontSize: '0.9em' }
              }}
            />
            <IconButton onClick={() => copyToClipboard(newApiKey)} color="primary">
              <CopyIcon />
            </IconButton>
          </Box>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>How to use:</strong><br />
              Include this key in your API requests via the X-API-Key header:
              <br />
              <code>X-API-Key: {newApiKey.substring(0, 20)}...</code>
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setKeyCreatedDialogOpen(false)} variant="contained">
            I've Saved My Key
          </Button>
        </DialogActions>
      </Dialog>

      {/* Usage Dialog */}
      <Dialog
        open={usageDialogOpen}
        onClose={() => setUsageDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>API Key Usage</DialogTitle>
        <DialogContent>
          {selectedKeyUsage.length === 0 ? (
            <Typography color="textSecondary" align="center" sx={{ py: 3 }}>
              No usage data available
            </Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Endpoint</TableCell>
                    <TableCell>Method</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>IP Address</TableCell>
                    <TableCell>Time</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedKeyUsage.map(usage => (
                    <TableRow key={usage.id}>
                      <TableCell><code>{usage.endpoint}</code></TableCell>
                      <TableCell>
                        <Chip label={usage.method} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={usage.status_code}
                          size="small"
                          color={usage.status_code < 400 ? 'success' : 'error'}
                        />
                      </TableCell>
                      <TableCell>{usage.ip_address || 'N/A'}</TableCell>
                      <TableCell>{formatDate(usage.created_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUsageDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default APIKeysPage;

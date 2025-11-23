/**
 * Webhooks Page Component
 * Version: 1.0.0
 *
 * Allows admins to manage webhooks for event-driven integrations.
 * Features: Create/Edit/Delete webhooks, test webhooks, view delivery logs.
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Typography,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  History as HistoryIcon,
  ContentCopy as CopyIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { webhooksAPI } from '../api/webhooks';

function WebhooksPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [webhooks, setWebhooks] = useState([]);
  const [availableEvents, setAvailableEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState(null);
  const [deliveriesDialogOpen, setDeliveriesDialogOpen] = useState(false);
  const [deliveries, setDeliveries] = useState([]);

  const [formData, setFormData] = useState({
    name: '',
    url: '',
    events: [],
    description: '',
    is_active: true,
    timeout_seconds: 30,
    retry_attempts: 3
  });

  useEffect(() => {
    loadWebhooks();
    loadAvailableEvents();
  }, []);

  const loadWebhooks = async () => {
    try {
      setLoading(true);
      const data = await webhooksAPI.list();
      setWebhooks(data);
      setLoading(false);
    } catch (error) {
      enqueueSnackbar('Failed to load webhooks', { variant: 'error' });
      setLoading(false);
    }
  };

  const loadAvailableEvents = async () => {
    try {
      const data = await webhooksAPI.getAvailableEvents();
      setAvailableEvents(data.events);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  };

  const handleSubmit = async () => {
    try {
      if (editingWebhook) {
        await webhooksAPI.update(editingWebhook.id, formData);
        enqueueSnackbar('Webhook updated', { variant: 'success' });
      } else {
        await webhooksAPI.create(formData);
        enqueueSnackbar('Webhook created', { variant: 'success' });
      }
      setDialogOpen(false);
      setEditingWebhook(null);
      loadWebhooks();
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to save webhook', { variant: 'error' });
    }
  };

  const handleEdit = (webhook) => {
    setEditingWebhook(webhook);
    setFormData({
      name: webhook.name,
      url: webhook.url,
      events: webhook.events,
      description: webhook.description || '',
      is_active: webhook.is_active,
      timeout_seconds: webhook.timeout_seconds,
      retry_attempts: webhook.retry_attempts
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this webhook?')) return;

    try {
      await webhooksAPI.delete(id);
      enqueueSnackbar('Webhook deleted', { variant: 'success' });
      loadWebhooks();
    } catch (error) {
      enqueueSnackbar('Failed to delete webhook', { variant: 'error' });
    }
  };

  const handleTest = async (webhook) => {
    try {
      const result = await webhooksAPI.test(webhook.id);
      if (result.success) {
        enqueueSnackbar('Test webhook sent successfully', { variant: 'success' });
      } else {
        enqueueSnackbar(`Test failed: ${result.error}`, { variant: 'error' });
      }
    } catch (error) {
      enqueueSnackbar('Failed to test webhook', { variant: 'error' });
    }
  };

  const handleViewDeliveries = async (webhook) => {
    try {
      const data = await webhooksAPI.getDeliveries(webhook.id);
      setDeliveries(data);
      setDeliveriesDialogOpen(true);
    } catch (error) {
      enqueueSnackbar('Failed to load deliveries', { variant: 'error' });
    }
  };

  const handleCopySecret = (secret) => {
    navigator.clipboard.writeText(secret);
    enqueueSnackbar('Secret copied to clipboard', { variant: 'success' });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'success';
      case 'failed': return 'error';
      case 'pending': return 'warning';
      case 'retrying': return 'info';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">Webhooks</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setEditingWebhook(null);
              setFormData({
                name: '',
                url: '',
                events: [],
                description: '',
                is_active: true,
                timeout_seconds: 30,
                retry_attempts: 3
              });
              setDialogOpen(true);
            }}
          >
            Add Webhook
          </Button>
        </Box>

        <Alert severity="info" sx={{ mb: 2 }}>
          Webhooks allow you to receive real-time notifications when events occur.
          Configure endpoints to integrate with external services like Slack, Discord, or custom applications.
        </Alert>

        {webhooks.length === 0 ? (
          <Box textAlign="center" py={4}>
            <Typography variant="body1" color="textSecondary">
              No webhooks configured yet. Click "Add Webhook" to create one.
            </Typography>
          </Box>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>URL</TableCell>
                <TableCell>Events</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {webhooks.map(webhook => (
                <TableRow key={webhook.id}>
                  <TableCell>{webhook.name}</TableCell>
                  <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {webhook.url}
                  </TableCell>
                  <TableCell>
                    {webhook.events.map(event => (
                      <Chip key={event} label={event} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={webhook.is_active ? 'Active' : 'Inactive'}
                      color={webhook.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton size="small" onClick={() => handleTest(webhook)} title="Test">
                      <SendIcon />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleViewDeliveries(webhook)} title="View Deliveries">
                      <HistoryIcon />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleEdit(webhook)} title="Edit">
                      <EditIcon />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(webhook.id)} title="Delete">
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingWebhook ? 'Edit Webhook' : 'Create Webhook'}</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            sx={{ mt: 2, mb: 2 }}
            required
          />
          <TextField
            fullWidth
            label="URL"
            value={formData.url}
            onChange={(e) => setFormData({...formData, url: e.target.value})}
            sx={{ mb: 2 }}
            placeholder="https://example.com/webhook"
            required
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Events *</InputLabel>
            <Select
              multiple
              value={formData.events}
              onChange={(e) => setFormData({...formData, events: e.target.value})}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map(value => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {availableEvents.map(event => (
                <MenuItem key={event} value={event}>{event}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={2}
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            sx={{ mb: 2 }}
          />
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Timeout (seconds)"
                type="number"
                value={formData.timeout_seconds}
                onChange={(e) => setFormData({...formData, timeout_seconds: parseInt(e.target.value)})}
                inputProps={{ min: 5, max: 120 }}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Retry Attempts"
                type="number"
                value={formData.retry_attempts}
                onChange={(e) => setFormData({...formData, retry_attempts: parseInt(e.target.value)})}
                inputProps={{ min: 0, max: 10 }}
              />
            </Grid>
          </Grid>
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
              />
            }
            label="Active"
          />
          {editingWebhook && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="caption" display="block" gutterBottom>
                Webhook Secret (for signature verification):
              </Typography>
              <Box display="flex" alignItems="center">
                <Typography variant="body2" sx={{ fontFamily: 'monospace', flex: 1, wordBreak: 'break-all' }}>
                  {editingWebhook.secret}
                </Typography>
                <IconButton size="small" onClick={() => handleCopySecret(editingWebhook.secret)}>
                  <CopyIcon fontSize="small" />
                </IconButton>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={!formData.name || !formData.url || formData.events.length === 0}>
            {editingWebhook ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Deliveries Dialog */}
      <Dialog
        open={deliveriesDialogOpen}
        onClose={() => setDeliveriesDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Delivery Log</DialogTitle>
        <DialogContent>
          {deliveries.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography variant="body2" color="textSecondary">
                No deliveries yet
              </Typography>
            </Box>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Event</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Attempts</TableCell>
                  <TableCell>Time</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {deliveries.map(delivery => (
                  <TableRow key={delivery.id}>
                    <TableCell>{delivery.event_type}</TableCell>
                    <TableCell>
                      <Chip label={delivery.status} color={getStatusColor(delivery.status)} size="small" />
                    </TableCell>
                    <TableCell>{delivery.attempts}</TableCell>
                    <TableCell>{new Date(delivery.created_at).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeliveriesDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default WebhooksPage;

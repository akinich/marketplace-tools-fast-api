/**
 * Telegram Notifications Settings Page
 * Version: 1.2.2
 * Last Updated: 2025-11-21
 *
 * Changelog:
 * ----------
 * v1.2.2 (2025-11-21):
 *   - Fix: Moved settings parsing from onSuccess to useEffect for better reliability
 *   - Added isSuccess check to prevent stuck loading state
 *   - Disabled refetchOnWindowFocus to prevent unnecessary refetches
 *   - Added loading text indicator for better UX
 *
 * v1.2.1 (2025-11-21):
 *   - Fix: Loading state now properly handles errors (error check before loading check)
 *   - Added retry logic (2 retries with 1s delay) for failed API requests
 *   - Added error logging for better debugging
 *   - Added reload button when error occurs
 *
 * v1.2.0 (2025-11-21):
 *   - Fix: Toggle states now properly reflect database values on load
 *   - Added toBool() helper for proper string-to-boolean conversion
 *   - Settings state starts as null until data is fetched
 *   - Prevents false defaults from overriding actual saved values
 *
 * v1.1.0 (2025-11-21):
 *   - Added granular event-level notification toggles
 *   - Tickets: created, updated, closed, comment, priority_changed
 *   - POs: created, status_changed
 *   - Inventory: first_alert, daily_summary
 *   - Expandable event toggles shown when channel notifications enabled
 *
 * v1.0.0 (2025-11-20):
 *   - Initial Telegram notifications settings page
 *   - Bot status indicator with health check
 *   - Channel ID configuration for tickets, POs, and inventory
 *   - Toggle switches for each notification type
 *   - Test notification functionality per channel
 *   - Real-time settings updates with validation
 *   - User account linking interface (for future personal DMs)
 *   - Material-UI components matching AdminPanel style
 *
 * Description:
 *   Admin interface for managing Telegram bot notifications. Allows configuration
 *   of channel IDs, enabling/disabling notifications per module, testing bot
 *   connectivity, and managing user account linking.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Switch,
  FormControlLabel,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Divider,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
} from '@mui/material';
import {
  Telegram as TelegramIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Send as SendIcon,
  Refresh as RefreshIcon,
  Link as LinkIcon,
  LinkOff as LinkOffIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { telegramAPI } from '../api';
import { useSnackbar } from 'notistack';

function TelegramSettings() {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  const [settings, setSettings] = useState(null); // Start with null until data loads

  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [testChannelType, setTestChannelType] = useState('');
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [linkCode, setLinkCode] = useState(null);

  // Helper to convert string/boolean to boolean
  const toBool = (val, defaultVal = true) => {
    if (val === null || val === undefined) return defaultVal;
    if (typeof val === 'boolean') return val;
    if (typeof val === 'string') return val.toLowerCase() === 'true';
    return Boolean(val);
  };

  // ========================================================================
  // FETCH SETTINGS
  // ========================================================================

  const { data: settingsData, isLoading: loadingSettings, isSuccess, error: settingsError } = useQuery(
    'telegramSettings',
    () => telegramAPI.getSettings(),
    {
      retry: 2, // Retry failed requests twice
      retryDelay: 1000, // Wait 1 second between retries
      staleTime: 30 * 1000, // 30 seconds
      cacheTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false, // Don't refetch on window focus to avoid flashing
      onError: (error) => {
        console.error('Failed to load Telegram settings:', error);
      },
    }
  );

  // Parse settings when data is available
  useEffect(() => {
    if (settingsData) {
      setSettings({
        tickets_channel_id: settingsData.tickets_channel_id || null,
        po_channel_id: settingsData.po_channel_id || null,
        inventory_channel_id: settingsData.inventory_channel_id || null,
        enable_ticket_notifications: toBool(settingsData.enable_ticket_notifications, true),
        enable_po_notifications: toBool(settingsData.enable_po_notifications, true),
        enable_inventory_notifications: toBool(settingsData.enable_inventory_notifications, true),
        enable_personal_notifications: toBool(settingsData.enable_personal_notifications, false),
        // Granular ticket notifications
        notify_ticket_created: toBool(settingsData.notify_ticket_created, true),
        notify_ticket_updated: toBool(settingsData.notify_ticket_updated, true),
        notify_ticket_closed: toBool(settingsData.notify_ticket_closed, true),
        notify_ticket_comment: toBool(settingsData.notify_ticket_comment, true),
        notify_ticket_priority_changed: toBool(settingsData.notify_ticket_priority_changed, true),
        // Granular PO notifications
        notify_po_created: toBool(settingsData.notify_po_created, true),
        notify_po_status_changed: toBool(settingsData.notify_po_status_changed, true),
        // Granular inventory notifications
        notify_low_stock_first_alert: toBool(settingsData.notify_low_stock_first_alert, true),
        notify_low_stock_daily_summary: toBool(settingsData.notify_low_stock_daily_summary, true),
      });
    }
  }, [settingsData]);

  // ========================================================================
  // FETCH BOT STATUS
  // ========================================================================

  const { data: statusData, isLoading: loadingStatus, refetch: refetchStatus } = useQuery(
    'telegramStatus',
    () => telegramAPI.getStatus(),
    {
      staleTime: 10 * 1000, // 10 seconds
      refetchInterval: 30 * 1000, // Refetch every 30 seconds
    }
  );

  // ========================================================================
  // FETCH USER LINK STATUS
  // ========================================================================

  const { data: linkStatusData, refetch: refetchLinkStatus } = useQuery(
    'telegramLinkStatus',
    () => telegramAPI.getLinkStatus(),
    {
      staleTime: 30 * 1000,
    }
  );

  // ========================================================================
  // MUTATIONS
  // ========================================================================

  const updateSettingsMutation = useMutation(
    (data) => telegramAPI.updateSettings(data),
    {
      onSuccess: () => {
        enqueueSnackbar('Settings updated successfully!', { variant: 'success' });
        queryClient.invalidateQueries('telegramSettings');
        queryClient.invalidateQueries('telegramStatus');
      },
      onError: (error) => {
        enqueueSnackbar(
          `Failed to update settings: ${error.response?.data?.detail || error.message}`,
          { variant: 'error' }
        );
      },
    }
  );

  const testNotificationMutation = useMutation(
    (data) => telegramAPI.sendTest(data),
    {
      onSuccess: (data) => {
        enqueueSnackbar(
          `Test notification sent to ${data.channel_type} channel!`,
          { variant: 'success' }
        );
        setTestDialogOpen(false);
      },
      onError: (error) => {
        enqueueSnackbar(
          `Failed to send test: ${error.response?.data?.detail || error.message}`,
          { variant: 'error' }
        );
      },
    }
  );

  const createLinkCodeMutation = useMutation(
    () => telegramAPI.createLinkCode(),
    {
      onSuccess: (data) => {
        setLinkCode(data);
        setLinkDialogOpen(true);
      },
      onError: (error) => {
        enqueueSnackbar(
          `Failed to create link code: ${error.response?.data?.detail || error.message}`,
          { variant: 'error' }
        );
      },
    }
  );

  const unlinkMutation = useMutation(
    () => telegramAPI.unlinkTelegram(),
    {
      onSuccess: () => {
        enqueueSnackbar('Telegram account unlinked successfully!', { variant: 'success' });
        refetchLinkStatus();
      },
      onError: (error) => {
        enqueueSnackbar(
          `Failed to unlink: ${error.response?.data?.detail || error.message}`,
          { variant: 'error' }
        );
      },
    }
  );

  // ========================================================================
  // HANDLERS
  // ========================================================================

  const handleSettingChange = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setSettings({
      ...settings,
      [field]: value,
    });
  };

  const handleSaveSettings = () => {
    // Filter out unchanged values and null values for optional fields
    const updates = {};

    if (settings.tickets_channel_id !== null && settings.tickets_channel_id !== '') {
      updates.tickets_channel_id = parseInt(settings.tickets_channel_id);
    }
    if (settings.po_channel_id !== null && settings.po_channel_id !== '') {
      updates.po_channel_id = parseInt(settings.po_channel_id);
    }
    if (settings.inventory_channel_id !== null && settings.inventory_channel_id !== '') {
      updates.inventory_channel_id = parseInt(settings.inventory_channel_id);
    }

    updates.enable_ticket_notifications = settings.enable_ticket_notifications;
    updates.enable_po_notifications = settings.enable_po_notifications;
    updates.enable_inventory_notifications = settings.enable_inventory_notifications;
    updates.enable_personal_notifications = settings.enable_personal_notifications;

    // Granular ticket notification settings
    updates.notify_ticket_created = settings.notify_ticket_created;
    updates.notify_ticket_updated = settings.notify_ticket_updated;
    updates.notify_ticket_closed = settings.notify_ticket_closed;
    updates.notify_ticket_comment = settings.notify_ticket_comment;
    updates.notify_ticket_priority_changed = settings.notify_ticket_priority_changed;

    // Granular PO notification settings
    updates.notify_po_created = settings.notify_po_created;
    updates.notify_po_status_changed = settings.notify_po_status_changed;

    // Granular inventory notification settings
    updates.notify_low_stock_first_alert = settings.notify_low_stock_first_alert;
    updates.notify_low_stock_daily_summary = settings.notify_low_stock_daily_summary;

    updateSettingsMutation.mutate(updates);
  };

  const handleTestNotification = (channelType) => {
    setTestChannelType(channelType);
    setTestDialogOpen(true);
  };

  const handleConfirmTest = () => {
    testNotificationMutation.mutate({ channel_type: testChannelType });
  };

  const handleCopyLinkCode = () => {
    if (linkCode?.link_code) {
      navigator.clipboard.writeText(linkCode.link_code);
      enqueueSnackbar('Link code copied to clipboard!', { variant: 'success' });
    }
  };

  // ========================================================================
  // RENDER
  // ========================================================================

  // Check for errors first (before loading state)
  if (settingsError) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load settings: {settingsError.message}
        </Alert>
        <Button
          variant="outlined"
          onClick={() => window.location.reload()}
        >
          Reload Page
        </Button>
      </Box>
    );
  }

  // Show loading only when actually loading (not when data is being processed)
  if (loadingSettings || !isSuccess || !settings) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 4, minHeight: '400px' }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Loading Telegram settings...
        </Typography>
      </Box>
    );
  }

  const botStatus = statusData?.status || 'inactive';
  const isHealthy = botStatus === 'active';

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <TelegramIcon sx={{ fontSize: 40, color: '#0088cc' }} />
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Telegram Notifications
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure Telegram bot for real-time notifications
          </Typography>
        </Box>
      </Box>

      {/* BOT STATUS CARD */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Bot Status
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {isHealthy ? (
                  <CheckCircleIcon sx={{ color: 'success.main' }} />
                ) : (
                  <ErrorIcon sx={{ color: 'error.main' }} />
                )}
                <Chip
                  label={isHealthy ? 'Connected' : 'Disconnected'}
                  color={isHealthy ? 'success' : 'error'}
                  size="small"
                />
                {statusData?.bot_username && (
                  <Typography variant="body2" color="text.secondary">
                    @{statusData.bot_username}
                  </Typography>
                )}
              </Box>
              {statusData?.message && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {statusData.message}
                </Typography>
              )}
            </Box>
            <IconButton onClick={() => refetchStatus()} disabled={loadingStatus}>
              <RefreshIcon />
            </IconButton>
          </Box>

          {!isHealthy && settingsData?.last_error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {settingsData.last_error}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* CHANNEL CONFIGURATION */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Channel Configuration
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Enter your Telegram channel IDs (negative numbers for channels/groups)
          </Typography>

          <Grid container spacing={3}>
            {/* Tickets Channel */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="subtitle2" gutterBottom>
                  🎫 Tickets Channel
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  label="Channel ID"
                  type="number"
                  value={settings.tickets_channel_id || ''}
                  onChange={handleSettingChange('tickets_channel_id')}
                  placeholder="-1001234567890"
                  sx={{ mb: 2 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enable_ticket_notifications}
                      onChange={handleSettingChange('enable_ticket_notifications')}
                      color="primary"
                    />
                  }
                  label="Enable Notifications"
                />
                {settings.enable_ticket_notifications && (
                  <Box sx={{ ml: 2, mt: 1, borderLeft: '2px solid', borderColor: 'divider', pl: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      Event Types:
                    </Typography>
                    <FormControlLabel
                      control={<Switch size="small" checked={settings.notify_ticket_created} onChange={handleSettingChange('notify_ticket_created')} />}
                      label={<Typography variant="body2">Ticket Created</Typography>}
                    />
                    <FormControlLabel
                      control={<Switch size="small" checked={settings.notify_ticket_updated} onChange={handleSettingChange('notify_ticket_updated')} />}
                      label={<Typography variant="body2">Ticket Updated</Typography>}
                    />
                    <FormControlLabel
                      control={<Switch size="small" checked={settings.notify_ticket_closed} onChange={handleSettingChange('notify_ticket_closed')} />}
                      label={<Typography variant="body2">Ticket Closed</Typography>}
                    />
                    <FormControlLabel
                      control={<Switch size="small" checked={settings.notify_ticket_comment} onChange={handleSettingChange('notify_ticket_comment')} />}
                      label={<Typography variant="body2">New Comment</Typography>}
                    />
                    <FormControlLabel
                      control={<Switch size="small" checked={settings.notify_ticket_priority_changed} onChange={handleSettingChange('notify_ticket_priority_changed')} />}
                      label={<Typography variant="body2">Priority Changed</Typography>}
                    />
                  </Box>
                )}
                <Box sx={{ mt: 1 }}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<SendIcon />}
                    onClick={() => handleTestNotification('tickets')}
                    disabled={!settings.tickets_channel_id}
                  >
                    Test
                  </Button>
                </Box>
              </Paper>
            </Grid>

            {/* Purchase Orders Channel */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="subtitle2" gutterBottom>
                  📦 Purchase Orders Channel
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  label="Channel ID"
                  type="number"
                  value={settings.po_channel_id || ''}
                  onChange={handleSettingChange('po_channel_id')}
                  placeholder="-1001234567891"
                  sx={{ mb: 2 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enable_po_notifications}
                      onChange={handleSettingChange('enable_po_notifications')}
                      color="primary"
                    />
                  }
                  label="Enable Notifications"
                />
                {settings.enable_po_notifications && (
                  <Box sx={{ ml: 2, mt: 1, borderLeft: '2px solid', borderColor: 'divider', pl: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      Event Types:
                    </Typography>
                    <FormControlLabel
                      control={<Switch size="small" checked={settings.notify_po_created} onChange={handleSettingChange('notify_po_created')} />}
                      label={<Typography variant="body2">PO Created</Typography>}
                    />
                    <FormControlLabel
                      control={<Switch size="small" checked={settings.notify_po_status_changed} onChange={handleSettingChange('notify_po_status_changed')} />}
                      label={<Typography variant="body2">Status Changed</Typography>}
                    />
                  </Box>
                )}
                <Box sx={{ mt: 1 }}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<SendIcon />}
                    onClick={() => handleTestNotification('po')}
                    disabled={!settings.po_channel_id}
                  >
                    Test
                  </Button>
                </Box>
              </Paper>
            </Grid>

            {/* Inventory Channel */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="subtitle2" gutterBottom>
                  📊 Inventory Channel
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  label="Channel ID"
                  type="number"
                  value={settings.inventory_channel_id || ''}
                  onChange={handleSettingChange('inventory_channel_id')}
                  placeholder="-1001234567892"
                  sx={{ mb: 2 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enable_inventory_notifications}
                      onChange={handleSettingChange('enable_inventory_notifications')}
                      color="primary"
                    />
                  }
                  label="Enable Notifications"
                />
                {settings.enable_inventory_notifications && (
                  <Box sx={{ ml: 2, mt: 1, borderLeft: '2px solid', borderColor: 'divider', pl: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      Event Types:
                    </Typography>
                    <FormControlLabel
                      control={<Switch size="small" checked={settings.notify_low_stock_first_alert} onChange={handleSettingChange('notify_low_stock_first_alert')} />}
                      label={<Typography variant="body2">Low Stock First Alert</Typography>}
                    />
                    <FormControlLabel
                      control={<Switch size="small" checked={settings.notify_low_stock_daily_summary} onChange={handleSettingChange('notify_low_stock_daily_summary')} />}
                      label={<Typography variant="body2">Daily Summary</Typography>}
                    />
                  </Box>
                )}
                <Box sx={{ mt: 1 }}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<SendIcon />}
                    onClick={() => handleTestNotification('inventory')}
                    disabled={!settings.inventory_channel_id}
                  >
                    Test
                  </Button>
                </Box>
              </Paper>
            </Grid>
          </Grid>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              onClick={handleSaveSettings}
              disabled={updateSettingsMutation.isLoading}
              startIcon={updateSettingsMutation.isLoading ? <CircularProgress size={20} /> : null}
            >
              Save Settings
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* PERSONAL NOTIFICATIONS (FUTURE FEATURE) */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Personal Notifications
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Link your Telegram account to receive personal direct messages (optional)
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            {linkStatusData?.is_linked ? (
              <>
                <Chip
                  icon={<LinkIcon />}
                  label="Telegram Linked"
                  color="success"
                  variant="outlined"
                />
                <Button
                  size="small"
                  variant="outlined"
                  color="error"
                  startIcon={<LinkOffIcon />}
                  onClick={() => unlinkMutation.mutate()}
                  disabled={unlinkMutation.isLoading}
                >
                  Unlink
                </Button>
              </>
            ) : (
              <Button
                variant="outlined"
                startIcon={<LinkIcon />}
                onClick={() => createLinkCodeMutation.mutate()}
                disabled={createLinkCodeMutation.isLoading}
              >
                Link Telegram Account
              </Button>
            )}
          </Box>

          <FormControlLabel
            control={
              <Switch
                checked={settings.enable_personal_notifications}
                onChange={handleSettingChange('enable_personal_notifications')}
                color="primary"
                disabled={!linkStatusData?.is_linked}
              />
            }
            label="Enable Personal DMs (requires account linking)"
          />

          {!linkStatusData?.is_linked && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Personal notifications are currently disabled. Link your Telegram account to enable.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* SETUP INSTRUCTIONS */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Setup Instructions
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            1. Create Telegram Bot
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            • Open Telegram and search for @BotFather
            <br />
            • Send /newbot and follow instructions
            <br />
            • Copy the bot token and add it to your .env file
          </Typography>

          <Typography variant="subtitle2" gutterBottom>
            2. Create Channels
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            • Create 3 Telegram channels (or use existing ones)
            <br />
            • Add your bot as an admin to each channel
            <br />
            • Forward a message from each channel to @userinfobot to get the channel ID
          </Typography>

          <Typography variant="subtitle2" gutterBottom>
            3. Configure Settings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Enter the channel IDs above (they should be negative numbers)
            <br />
            • Enable notifications for each module
            <br />
            • Click "Test" to verify the bot can send messages
            <br />
            • Save your settings
          </Typography>
        </CardContent>
      </Card>

      {/* TEST CONFIRMATION DIALOG */}
      <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)}>
        <DialogTitle>Send Test Notification</DialogTitle>
        <DialogContent>
          <Typography>
            This will send a test message to the <strong>{testChannelType}</strong> channel.
            <br />
            Make sure your bot is added as an admin to the channel.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmTest}
            variant="contained"
            disabled={testNotificationMutation.isLoading}
            startIcon={testNotificationMutation.isLoading ? <CircularProgress size={20} /> : <SendIcon />}
          >
            Send Test
          </Button>
        </DialogActions>
      </Dialog>

      {/* LINK CODE DIALOG */}
      <Dialog open={linkDialogOpen} onClose={() => setLinkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Link Your Telegram Account</DialogTitle>
        <DialogContent>
          {linkCode && (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                Link code generated successfully!
              </Alert>

              <Typography variant="body2" gutterBottom>
                1. Open Telegram and search for your bot
              </Typography>
              <Typography variant="body2" gutterBottom sx={{ mb: 2 }}>
                2. Send this command to the bot:
              </Typography>

              <Paper sx={{ p: 2, bgcolor: 'grey.100', display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography
                  variant="h6"
                  sx={{ fontFamily: 'monospace', flex: 1 }}
                >
                  /start {linkCode.link_code}
                </Typography>
                <IconButton onClick={handleCopyLinkCode} size="small">
                  <ContentCopyIcon />
                </IconButton>
              </Paper>

              <Alert severity="warning" sx={{ mt: 2 }}>
                <Typography variant="caption">
                  This code expires in 15 minutes: {new Date(linkCode.expires_at).toLocaleTimeString()}
                </Typography>
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setLinkDialogOpen(false);
            setLinkCode(null);
            refetchLinkStatus();
          }} variant="contained">
            Done
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default TelegramSettings;

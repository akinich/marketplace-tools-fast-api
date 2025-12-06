/**
 * Security Dashboard Page
 * Version: 1.0.0
 * Last Updated: 2025-11-21
 *
 * Admin dashboard for security monitoring:
 * - Active sessions management
 * - Login history
 * - Security statistics
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Grid,
  Tabs,
  Tab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  History as HistoryIcon,
  Devices as DevicesIcon,
  CheckCircle,
  Cancel,
  Warning,
  LockOpen,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { securityAPI, adminAPI } from '../api';

// Tab Panel Component
function TabPanel({ children, value, index }) {
  return value === index ? <Box sx={{ pt: 2 }}>{children}</Box> : null;
}

export default function SecurityDashboard() {
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [confirmDialog, setConfirmDialog] = useState({ open: false, session: null });

  // Queries
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['securityStats'],
    queryFn: securityAPI.getSecurityStats,
    refetchInterval: 30000,
  });

  const { data: sessionsData, isLoading: sessionsLoading, refetch: refetchSessions } = useQuery({
    queryKey: ['allSessions'],
    queryFn: securityAPI.getAllSessions,
  });

  const { data: historyData, isLoading: historyLoading, refetch: refetchHistory } = useQuery({
    queryKey: ['allLoginHistory', statusFilter],
    queryFn: () => securityAPI.getAllLoginHistory(50, statusFilter || null),
  });

  // Mutations
  const revokeSessionMutation = useMutation({
    mutationFn: securityAPI.adminRevokeSession,
    onSuccess: () => {
      enqueueSnackbar('Session revoked successfully', { variant: 'success' });
      queryClient.invalidateQueries(['allSessions']);
      queryClient.invalidateQueries(['securityStats']);
      setConfirmDialog({ open: false, session: null });
    },
    onError: (error) => {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to revoke session', { variant: 'error' });
    },
  });

  const unlockUserMutation = useMutation({
    mutationFn: adminAPI.unlockUser,
    onSuccess: () => {
      enqueueSnackbar('Account unlocked successfully', { variant: 'success' });
      queryClient.invalidateQueries(['allLoginHistory']);
    },
    onError: (error) => {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to unlock account', { variant: 'error' });
    },
  });

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  const formatDevice = (userAgent) => {
    if (!userAgent) return 'Unknown';
    if (userAgent.includes('Mobile')) return 'Mobile';
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    return 'Browser';
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <SecurityIcon /> Security Dashboard
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Active Sessions</Typography>
              <Typography variant="h4">
                {statsLoading ? <CircularProgress size={24} /> : stats?.active_sessions || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Logins (24h)</Typography>
              <Typography variant="h4" color="success.main">
                {statsLoading ? <CircularProgress size={24} /> : stats?.logins_24h || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Failed Logins (24h)</Typography>
              <Typography variant="h4" color="warning.main">
                {statsLoading ? <CircularProgress size={24} /> : stats?.failed_logins_24h || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Lockouts (24h)</Typography>
              <Typography variant="h4" color="error.main">
                {statsLoading ? <CircularProgress size={24} /> : stats?.lockouts_24h || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab icon={<DevicesIcon />} label="Active Sessions" />
          <Tab icon={<HistoryIcon />} label="Login History" />
        </Tabs>
      </Paper>

      {/* Active Sessions Tab */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button startIcon={<RefreshIcon />} onClick={() => refetchSessions()}>
            Refresh
          </Button>
        </Box>
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>User</TableCell>
                <TableCell>Device</TableCell>
                <TableCell>IP Address</TableCell>
                <TableCell>Last Activity</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sessionsLoading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center"><CircularProgress /></TableCell>
                </TableRow>
              ) : sessionsData?.sessions?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">No active sessions</TableCell>
                </TableRow>
              ) : (
                sessionsData?.sessions?.map((session) => (
                  <TableRow key={session.id}>
                    <TableCell>
                      <Typography variant="body2">{session.user_name}</Typography>
                      <Typography variant="caption" color="textSecondary">{session.user_email}</Typography>
                    </TableCell>
                    <TableCell>{formatDevice(session.device_info)}</TableCell>
                    <TableCell>{session.ip_address || '-'}</TableCell>
                    <TableCell>{formatDate(session.last_activity)}</TableCell>
                    <TableCell>
                      <Tooltip title="Revoke Session">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => setConfirmDialog({ open: true, session })}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Login History Tab */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status Filter</InputLabel>
            <Select
              value={statusFilter}
              label="Status Filter"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="success">Success</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
              <MenuItem value="locked">Locked</MenuItem>
            </Select>
          </FormControl>
          <Button startIcon={<RefreshIcon />} onClick={() => refetchHistory()}>
            Refresh
          </Button>
        </Box>
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>User</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>IP Address</TableCell>
                <TableCell>Device</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {historyLoading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center"><CircularProgress /></TableCell>
                </TableRow>
              ) : historyData?.history?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">No login history</TableCell>
                </TableRow>
              ) : (
                historyData?.history?.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>{formatDate(entry.login_at)}</TableCell>
                    <TableCell>
                      <Typography variant="body2">{entry.user_name || 'Unknown'}</Typography>
                      <Typography variant="caption" color="textSecondary">{entry.user_email}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        icon={entry.login_status === 'success' ? <CheckCircle /> : entry.login_status === 'locked' ? <Warning /> : <Cancel />}
                        label={entry.login_status}
                        color={entry.login_status === 'success' ? 'success' : entry.login_status === 'locked' ? 'error' : 'warning'}
                      />
                      {entry.is_new_device && <Chip size="small" label="New Device" sx={{ ml: 0.5 }} />}
                    </TableCell>
                    <TableCell>{entry.ip_address || '-'}</TableCell>
                    <TableCell>{formatDevice(entry.device_info)}</TableCell>
                    <TableCell>
                      {entry.login_status === 'locked' && entry.user_id && (
                        <Tooltip title="Unlock Account">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => unlockUserMutation.mutate(entry.user_id)}
                          >
                            <LockOpen />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Confirm Revoke Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ open: false, session: null })}>
        <DialogTitle>Revoke Session?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to revoke this session for {confirmDialog.session?.user_email}?
            They will be logged out immediately.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, session: null })}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            onClick={() => revokeSessionMutation.mutate(confirmDialog.session?.id)}
          >
            Revoke
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

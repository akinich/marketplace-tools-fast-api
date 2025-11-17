/**
 * Admin Panel - User Management, Modules, Permissions & Activity Logs
 * Version: 1.1.0
 * Last Updated: 2025-11-17
 *
 * Changelog:
 * ----------
 * v1.1.0 (2025-11-17):
 *   - Added Module Management page to view all system modules
 *   - Added User Permissions dialog with checkbox interface
 *   - Added permissions icon button to user management table
 *   - Integrated permission management with backend API
 *   - Added real-time permission updates with notifications
 *
 * v1.0.0 (2025-11-17):
 *   - Initial admin panel with User Management and Activity Logs
 */

import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Checkbox,
  FormControlLabel,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  VpnKey as PermissionsIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { adminAPI } from '../api';
import { useSnackbar } from 'notistack';

// User Management Page
function UserManagementPage() {
  const { data, isLoading, error } = useQuery('adminUsers', () => adminAPI.getUsers());
  const [selectedUser, setSelectedUser] = useState(null);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load users: {error.message}</Alert>;
  }

  const handleManagePermissions = (user) => {
    setSelectedUser(user);
    setPermissionsDialogOpen(true);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold">
          User Management
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} disabled>
          Add User (Use Supabase UI)
        </Button>
      </Box>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.users?.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>{user.full_name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={user.role_name}
                        color={user.role_name === 'Admin' ? 'primary' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={user.is_active ? 'Active' : 'Inactive'}
                        color={user.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{new Date(user.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleManagePermissions(user)}
                        title="Manage Permissions"
                      >
                        <PermissionsIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Permissions Dialog */}
      {selectedUser && (
        <PermissionsDialog
          open={permissionsDialogOpen}
          onClose={() => {
            setPermissionsDialogOpen(false);
            setSelectedUser(null);
          }}
          user={selectedUser}
        />
      )}
    </Box>
  );
}

// Permissions Dialog Component
function PermissionsDialog({ open, onClose, user }) {
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();

  const { data: permissionsData, isLoading } = useQuery(
    ['userPermissions', user.id],
    () => adminAPI.getUserPermissions(user.id),
    { enabled: open }
  );

  const { data: modulesData } = useQuery('allModules', () => adminAPI.getModules());

  const [selectedModules, setSelectedModules] = useState([]);

  React.useEffect(() => {
    if (permissionsData?.modules) {
      setSelectedModules(permissionsData.modules.map((m) => m.module_id));
    }
  }, [permissionsData]);

  const updatePermissionsMutation = useMutation(
    (moduleIds) => adminAPI.updateUserPermissions(user.id, moduleIds),
    {
      onSuccess: () => {
        enqueueSnackbar('Permissions updated successfully', { variant: 'success' });
        queryClient.invalidateQueries(['userPermissions', user.id]);
        onClose();
      },
      onError: (error) => {
        enqueueSnackbar(`Failed to update permissions: ${error.message}`, { variant: 'error' });
      },
    }
  );

  const handleToggleModule = (moduleId) => {
    setSelectedModules((prev) =>
      prev.includes(moduleId) ? prev.filter((id) => id !== moduleId) : [...prev, moduleId]
    );
  };

  const handleSave = () => {
    updatePermissionsMutation.mutate(selectedModules);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Manage Permissions - {user.full_name}
      </DialogTitle>
      <DialogContent>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Select modules this user can access:
            </Typography>
            {modulesData?.modules?.map((module) => (
              <FormControlLabel
                key={module.id}
                control={
                  <Checkbox
                    checked={selectedModules.includes(module.id)}
                    onChange={() => handleToggleModule(module.id)}
                  />
                }
                label={`${module.module_name} - ${module.description}`}
              />
            ))}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={updatePermissionsMutation.isLoading}
        >
          {updatePermissionsMutation.isLoading ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// Module Management Page
function ModuleManagementPage() {
  const { data, isLoading, error } = useQuery('allModules', () => adminAPI.getModules());

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load modules: {error.message}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Module Management
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        System modules available in the application
      </Typography>

      <Grid container spacing={3}>
        {data?.modules?.map((module) => (
          <Grid item xs={12} md={6} key={module.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <Box>
                    <Typography variant="h6">{module.module_name}</Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {module.description}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Key: {module.module_key} | Order: {module.display_order}
                    </Typography>
                  </Box>
                  <Chip
                    label={module.is_active ? 'Active' : 'Inactive'}
                    color={module.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

// Activity Logs Page
function ActivityLogsPage() {
  const { data, isLoading, error } = useQuery('activityLogs', () =>
    adminAPI.getActivityLogs({ days: 7, limit: 50 })
  );

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load activity logs: {error.message}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Activity Logs
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Recent system activity (last 7 days)
      </Typography>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date/Time</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Module</TableCell>
                  <TableCell>Description</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.logs?.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>{new Date(log.created_at).toLocaleString()}</TableCell>
                    <TableCell>{log.user_email}</TableCell>
                    <TableCell>
                      <Chip label={log.action_type} size="small" />
                    </TableCell>
                    <TableCell>{log.module_key || '-'}</TableCell>
                    <TableCell>{log.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}

// Main Admin Panel Component
export default function AdminPanel() {
  return (
    <Routes>
      <Route index element={<Navigate to="users" replace />} />
      <Route path="users" element={<UserManagementPage />} />
      <Route path="modules" element={<ModuleManagementPage />} />
      <Route path="activity" element={<ActivityLogsPage />} />
    </Routes>
  );
}

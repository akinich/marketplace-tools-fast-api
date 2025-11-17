/**
 * Admin Panel - User Management, Modules, Permissions & Activity Logs
 * Version: 1.3.0
 * Last Updated: 2025-11-17
 *
 * Changelog:
 * ----------
 * v1.3.0 (2025-11-17):
 *   - PHASE 3: Enhanced hierarchical permissions dialog
 *   - Shows parent modules with expandable/collapsible children
 *   - Sub-modules displayed with indentation for visual hierarchy
 *   - "Grant All Sub-modules" checkbox for parent modules
 *   - Selecting parent auto-selects all children
 *   - Improved UX with expandable sections and visual grouping
 *
 * v1.2.0 (2025-11-17):
 *   - Implemented Create User dialog with full form functionality
 *   - Added email validation and role selection
 *   - Shows temporary password to admin after user creation
 *   - User can be created directly from Admin Panel (no Supabase UI needed)
 *   - Auto-refreshes user list after creation
 *   - Added proper form validation and error handling
 *
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
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  VpnKey as PermissionsIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { adminAPI } from '../api';
import { useSnackbar } from 'notistack';

// Create User Dialog Component
function CreateUserDialog({ open, onClose }) {
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    role_id: 2, // Default to regular user
  });

  const [errors, setErrors] = useState({});
  const [tempPassword, setTempPassword] = useState(null);

  // Fetch roles for dropdown
  const { data: rolesData } = useQuery('adminRoles', () => adminAPI.getRoles(), {
    enabled: open,
  });

  const createUserMutation = useMutation((data) => adminAPI.createUser(data), {
    onSuccess: (response) => {
      enqueueSnackbar('User created successfully!', { variant: 'success' });
      setTempPassword(response.temporary_password);
      queryClient.invalidateQueries('adminUsers');
      // Don't close immediately - show password first
    },
    onError: (error) => {
      enqueueSnackbar(
        `Failed to create user: ${error.response?.data?.detail || error.message}`,
        { variant: 'error' }
      );
    },
  });

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
    if (errors[field]) {
      setErrors({ ...errors, [field]: null });
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Full name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    createUserMutation.mutate(formData);
  };

  const handleClose = () => {
    setFormData({ email: '', full_name: '', role_id: 2 });
    setErrors({});
    setTempPassword(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {tempPassword ? 'User Created Successfully' : 'Create New User'}
      </DialogTitle>
      <DialogContent>
        {!tempPassword ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Email Address"
              type="email"
              required
              fullWidth
              value={formData.email}
              onChange={handleChange('email')}
              error={!!errors.email}
              helperText={errors.email}
              placeholder="user@example.com"
              autoFocus
            />

            <TextField
              label="Full Name"
              required
              fullWidth
              value={formData.full_name}
              onChange={handleChange('full_name')}
              error={!!errors.full_name}
              helperText={errors.full_name}
              placeholder="John Doe"
            />

            <FormControl fullWidth required>
              <InputLabel>Role</InputLabel>
              <Select
                value={formData.role_id}
                onChange={handleChange('role_id')}
                label="Role"
              >
                {rolesData?.roles?.map((role) => (
                  <MenuItem key={role.id} value={role.id}>
                    {role.role_name}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>Assign a role to this user</FormHelperText>
            </FormControl>
          </Box>
        ) : (
          <Box>
            <Alert severity="success" sx={{ mb: 2 }}>
              User account created successfully!
            </Alert>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                <strong>Temporary Password (share securely with user):</strong>
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  fontFamily: 'monospace',
                  bgcolor: 'background.paper',
                  p: 1.5,
                  borderRadius: 1,
                  mt: 1,
                  userSelect: 'all',
                }}
              >
                {tempPassword}
              </Typography>
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                The user should change this password after first login.
              </Typography>
            </Alert>
            <Typography variant="body2" color="text.secondary">
              Email: <strong>{formData.email}</strong>
              <br />
              Name: <strong>{formData.full_name}</strong>
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        {!tempPassword ? (
          <>
            <Button onClick={handleClose} disabled={createUserMutation.isLoading}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              variant="contained"
              disabled={createUserMutation.isLoading}
              startIcon={createUserMutation.isLoading ? <CircularProgress size={20} /> : <AddIcon />}
            >
              Create User
            </Button>
          </>
        ) : (
          <Button onClick={handleClose} variant="contained">
            Done
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

// User Management Page
function UserManagementPage() {
  const { data, isLoading, error } = useQuery('adminUsers', () => adminAPI.getUsers());
  const [selectedUser, setSelectedUser] = useState(null);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [createUserDialogOpen, setCreateUserDialogOpen] = useState(false);

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
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateUserDialogOpen(true)}
        >
          Add User
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

      {/* Create User Dialog */}
      <CreateUserDialog
        open={createUserDialogOpen}
        onClose={() => setCreateUserDialogOpen(false)}
      />

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

// Permissions Dialog Component - ENHANCED HIERARCHICAL VERSION (Phase 3)
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
  const [expandedParents, setExpandedParents] = useState({});

  React.useEffect(() => {
    if (permissionsData?.modules) {
      setSelectedModules(permissionsData.modules.map((m) => m.module_id));
    }
  }, [permissionsData]);

  // Separate top-level modules and sub-modules
  const topLevelModules = React.useMemo(() => {
    return modulesData?.modules?.filter((m) => !m.parent_module_id && m.module_key !== 'dashboard') || [];
  }, [modulesData]);

  const getSubModules = React.useCallback((parentId) => {
    return modulesData?.modules?.filter((m) => m.parent_module_id === parentId) || [];
  }, [modulesData]);

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

  const handleToggleModule = (moduleId, subModules = []) => {
    setSelectedModules((prev) => {
      if (prev.includes(moduleId)) {
        // Deselecting - also deselect all children
        const subModuleIds = subModules.map((sm) => sm.id);
        return prev.filter((id) => id !== moduleId && !subModuleIds.includes(id));
      } else {
        // Selecting - add module
        return [...prev, moduleId];
      }
    });
  };

  const handleToggleAllSubModules = (parentId, subModules) => {
    const subModuleIds = subModules.map((sm) => sm.id);
    const allSelected = subModuleIds.every((id) => selectedModules.includes(id));

    setSelectedModules((prev) => {
      if (allSelected) {
        // Deselect all sub-modules
        return prev.filter((id) => !subModuleIds.includes(id));
      } else {
        // Select parent and all sub-modules
        const newSelection = [...prev];
        if (!newSelection.includes(parentId)) {
          newSelection.push(parentId);
        }
        subModuleIds.forEach((id) => {
          if (!newSelection.includes(id)) {
            newSelection.push(id);
          }
        });
        return newSelection;
      }
    });
  };

  const toggleExpanded = (moduleId) => {
    setExpandedParents((prev) => ({
      ...prev,
      [moduleId]: !prev[moduleId],
    }));
  };

  const handleSave = () => {
    updatePermissionsMutation.mutate(selectedModules);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Manage Permissions - {user.full_name}
        {user.role_name === 'Admin' && (
          <Typography variant="caption" display="block" color="text.secondary">
            Admin users have full access to all modules
          </Typography>
        )}
      </DialogTitle>
      <DialogContent>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : user.role_name === 'Admin' ? (
          <Alert severity="info" sx={{ mt: 2 }}>
            This user has the Admin role and automatically has access to all modules.
            Permission management is only available for non-admin users.
          </Alert>
        ) : (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ mb: 2 }}>
              Select modules this user can access:
            </Typography>

            {/* Hierarchical Module List */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {topLevelModules.map((parentModule) => {
                const subModules = getSubModules(parentModule.id);
                const hasChildren = subModules.length > 0;
                const isExpanded = expandedParents[parentModule.id] ?? true; // Default expanded
                const allSubModulesSelected = hasChildren && subModules.every((sm) => selectedModules.includes(sm.id));

                return (
                  <Box key={parentModule.id} sx={{ mb: 1 }}>
                    {/* Parent Module */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        bgcolor: 'action.hover',
                        borderRadius: 1,
                        p: 1,
                      }}
                    >
                      {hasChildren && (
                        <IconButton
                          size="small"
                          onClick={() => toggleExpanded(parentModule.id)}
                          sx={{ mr: 1 }}
                        >
                          {isExpanded ? <ExpandMoreIcon /> : <ChevronRightIcon />}
                        </IconButton>
                      )}
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={selectedModules.includes(parentModule.id)}
                            onChange={() => handleToggleModule(parentModule.id, subModules)}
                          />
                        }
                        label={
                          <Box>
                            <Typography variant="body1" fontWeight="medium">
                              {parentModule.icon} {parentModule.module_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {parentModule.description}
                            </Typography>
                          </Box>
                        }
                        sx={{ flex: 1, mr: 0 }}
                      />
                      {hasChildren && (
                        <Button
                          size="small"
                          variant={allSubModulesSelected ? 'outlined' : 'text'}
                          onClick={() => handleToggleAllSubModules(parentModule.id, subModules)}
                          sx={{ minWidth: 'auto', whiteSpace: 'nowrap' }}
                        >
                          {allSubModulesSelected ? 'Deselect All' : 'Grant All'}
                        </Button>
                      )}
                    </Box>

                    {/* Sub-Modules (Collapsible) */}
                    {hasChildren && isExpanded && (
                      <Box sx={{ ml: 6, mt: 0.5, borderLeft: '2px solid', borderColor: 'divider', pl: 2 }}>
                        {subModules.map((subModule) => (
                          <FormControlLabel
                            key={subModule.id}
                            control={
                              <Checkbox
                                checked={selectedModules.includes(subModule.id)}
                                onChange={() => handleToggleModule(subModule.id)}
                              />
                            }
                            label={
                              <Box>
                                <Typography variant="body2">
                                  {subModule.icon} {subModule.module_name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {subModule.description}
                                </Typography>
                              </Box>
                            }
                            sx={{ display: 'flex', mb: 0.5 }}
                          />
                        ))}
                      </Box>
                    )}
                  </Box>
                );
              })}
            </Box>

            {topLevelModules.length === 0 && (
              <Alert severity="info">No modules available</Alert>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={updatePermissionsMutation.isLoading || user.role_name === 'Admin'}
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

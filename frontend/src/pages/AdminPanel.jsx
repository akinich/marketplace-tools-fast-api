/**
 * Admin Panel - User Management & Activity Logs
 * Version: 1.0.0
 */

import React from 'react';
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
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { useQuery } from 'react-query';
import { adminAPI } from '../api';

// User Management Page
function UserManagementPage() {
  const { data, isLoading, error } = useQuery('adminUsers', () => adminAPI.getUsers());

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

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold">
          User Management
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />}>
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
      <Route path="activity" element={<ActivityLogsPage />} />
    </Routes>
  );
}

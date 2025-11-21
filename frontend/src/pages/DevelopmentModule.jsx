/**
 * Development Planning Module
 * Feature planning and progress tracking
 * Version: 1.2.0
 * Last Updated: 2025-11-21
 *
 * Changelog:
 * v1.2.0 (2025-11-21):
 *   - Converted Material-UI icon imports to individual imports for better tree-shaking
 *   - Migrated from react-query v3 to @tanstack/react-query v5
 *   - Bundle size optimization as part of code splitting initiative
 *
 * v1.1.0 (2025-11-20):
 *   - Added delete functionality for features
 *   - Delete button in feature detail view (admin only)
 *   - Delete button in features list table (admin only)
 *   - Confirmation dialogs before deletion
 *   - Shows count of steps and comments that will be deleted
 *
 * v1.0.0 (2025-11-20):
 *   - Initial release
 *   - Features list with filters and pagination
 *   - Feature detail view with steps and comments
 *   - Admin can create/edit features and steps
 *   - All users can view and comment
 */

import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TablePagination,
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemAvatar,
  Avatar,
  Checkbox,
  LinearProgress,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ViewIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';
import DoneIcon from '@mui/icons-material/CheckCircle';
import TodoIcon from '@mui/icons-material/RadioButtonUnchecked';
import InProgressIcon from '@mui/icons-material/PlayCircle';
import CommentIcon from '@mui/icons-material/Comment';
import PriorityIcon from '@mui/icons-material/Flag';
import { useSnackbar } from 'notistack';
import useAuthStore from '../store/authStore';
import { developmentAPI } from '../api';

// ============================================================================
// CONSTANTS
// ============================================================================

const FEATURE_STATUS = [
  { value: 'planned', label: 'Planned', color: 'default' },
  { value: 'in_development', label: 'In Development', color: 'info' },
  { value: 'testing', label: 'Testing', color: 'warning' },
  { value: 'completed', label: 'Completed', color: 'success' },
  { value: 'on_hold', label: 'On Hold', color: 'error' },
];

const FEATURE_PRIORITY = [
  { value: 'low', label: 'Low', color: 'success' },
  { value: 'medium', label: 'Medium', color: 'info' },
  { value: 'high', label: 'High', color: 'warning' },
  { value: 'critical', label: 'Critical', color: 'error' },
];

const STEP_STATUS = [
  { value: 'todo', label: 'To Do', icon: <TodoIcon /> },
  { value: 'in_progress', label: 'In Progress', icon: <InProgressIcon color="info" /> },
  { value: 'done', label: 'Done', icon: <DoneIcon color="success" /> },
];

const getStatusConfig = (status) => FEATURE_STATUS.find((s) => s.value === status) || FEATURE_STATUS[0];
const getPriorityConfig = (priority) => FEATURE_PRIORITY.find((p) => p.value === priority) || FEATURE_PRIORITY[1];
const getStepStatusConfig = (status) => STEP_STATUS.find((s) => s.value === status) || STEP_STATUS[0];

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString();
};

// ============================================================================
// FEATURES LIST COMPONENT
// ============================================================================

function FeaturesList() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role?.toLowerCase() === 'admin';

  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [stats, setStats] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [newFeature, setNewFeature] = useState({
    title: '',
    description: '',
    priority: 'medium',
    target_date: '',
  });

  // Delete confirmation
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [featureToDelete, setFeatureToDelete] = useState(null);

  const fetchFeatures = async () => {
    setLoading(true);
    try {
      const params = {
        page: page + 1,
        limit: rowsPerPage,
      };
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;

      const data = await developmentAPI.getFeatures(params);
      setFeatures(data.features || []);
      setTotal(data.total || 0);
    } catch (error) {
      enqueueSnackbar('Failed to fetch features', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await developmentAPI.getFeatureStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    fetchFeatures();
    fetchStats();
  }, [page, rowsPerPage, statusFilter, priorityFilter]);

  const handleCreateFeature = async () => {
    if (!newFeature.title.trim()) {
      enqueueSnackbar('Please enter a title', { variant: 'warning' });
      return;
    }

    try {
      const data = {
        title: newFeature.title,
        description: newFeature.description || null,
        priority: newFeature.priority,
        target_date: newFeature.target_date || null,
      };
      await developmentAPI.createFeature(data);
      enqueueSnackbar('Feature created successfully', { variant: 'success' });
      setCreateOpen(false);
      setNewFeature({ title: '', description: '', priority: 'medium', target_date: '' });
      fetchFeatures();
      fetchStats();
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to create feature', { variant: 'error' });
    }
  };

  const handleDeleteFeature = async () => {
    if (!featureToDelete) return;

    try {
      await developmentAPI.deleteFeature(featureToDelete.id);
      enqueueSnackbar('Feature deleted successfully', { variant: 'success' });
      setDeleteDialog(false);
      setFeatureToDelete(null);
      fetchFeatures();
      fetchStats();
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to delete feature', { variant: 'error' });
    }
  };

  const getProgress = (stepCount, completedSteps) => {
    if (stepCount === 0) return 0;
    return Math.round((completedSteps / stepCount) * 100);
  };

  return (
    <Box>
      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4">{stats.planned}</Typography>
                <Typography variant="body2" color="text.secondary">Planned</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="info.main">{stats.in_development}</Typography>
                <Typography variant="body2" color="text.secondary">In Dev</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="warning.main">{stats.testing}</Typography>
                <Typography variant="body2" color="text.secondary">Testing</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="success.main">{stats.completed}</Typography>
                <Typography variant="body2" color="text.secondary">Completed</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={2.4}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4">{stats.total_features}</Typography>
                <Typography variant="body2" color="text.secondary">Total</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Development Roadmap</Typography>
        {isAdmin && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
          >
            Add Feature
          </Button>
        )}
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
                >
                  <MenuItem value="">All Status</MenuItem>
                  {FEATURE_STATUS.map((status) => (
                    <MenuItem key={status.value} value={status.value}>{status.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Priority</InputLabel>
                <Select
                  value={priorityFilter}
                  label="Priority"
                  onChange={(e) => { setPriorityFilter(e.target.value); setPage(0); }}
                >
                  <MenuItem value="">All Priorities</MenuItem>
                  {FEATURE_PRIORITY.map((priority) => (
                    <MenuItem key={priority.value} value={priority.value}>{priority.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Features Table */}
      <TableContainer component={Paper}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : features.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary">No features found</Typography>
          </Box>
        ) : (
          <>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Feature</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Target Date</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {features.map((feature) => {
                  const statusConfig = getStatusConfig(feature.status);
                  const priorityConfig = getPriorityConfig(feature.priority);
                  const progress = getProgress(feature.step_count, feature.completed_steps);

                  return (
                    <TableRow key={feature.id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {feature.title}
                        </Typography>
                        {feature.description && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            {feature.description.substring(0, 60)}
                            {feature.description.length > 60 ? '...' : ''}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip label={statusConfig.label} size="small" color={statusConfig.color} />
                      </TableCell>
                      <TableCell>
                        <Chip label={priorityConfig.label} size="small" color={priorityConfig.color} variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={progress}
                            sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                          />
                          <Typography variant="caption">
                            {feature.completed_steps}/{feature.step_count}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{formatDate(feature.target_date)}</TableCell>
                      <TableCell align="right">
                        <IconButton size="small" onClick={() => navigate(`/development/${feature.id}`)} title="View">
                          <ViewIcon />
                        </IconButton>
                        {isAdmin && (
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => { setFeatureToDelete(feature); setDeleteDialog(true); }}
                            title="Delete"
                          >
                            <DeleteIcon />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            <TablePagination
              component="div"
              count={total}
              page={page}
              onPageChange={(e, newPage) => setPage(newPage)}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
              rowsPerPageOptions={[5, 10, 25, 50]}
            />
          </>
        )}
      </TableContainer>

      {/* Create Feature Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Feature</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Title"
              fullWidth
              required
              value={newFeature.title}
              onChange={(e) => setNewFeature({ ...newFeature, title: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={newFeature.description}
              onChange={(e) => setNewFeature({ ...newFeature, description: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={newFeature.priority}
                label="Priority"
                onChange={(e) => setNewFeature({ ...newFeature, priority: e.target.value })}
              >
                {FEATURE_PRIORITY.map((p) => (
                  <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Target Date"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newFeature.target_date}
              onChange={(e) => setNewFeature({ ...newFeature, target_date: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateFeature}>Create</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Feature Confirmation Dialog */}
      <Dialog open={deleteDialog} onClose={() => { setDeleteDialog(false); setFeatureToDelete(null); }} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Feature</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this feature?
          </Typography>
          {featureToDelete && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                "{featureToDelete.title}"
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                This will permanently delete the feature and all its {featureToDelete.step_count} steps and {featureToDelete.comment_count} comments.
              </Typography>
            </Box>
          )}
          <Typography color="error" sx={{ mt: 2, fontWeight: 'bold' }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDeleteDialog(false); setFeatureToDelete(null); }}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDeleteFeature}>
            Delete Permanently
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// ============================================================================
// FEATURE DETAIL COMPONENT
// ============================================================================

function FeatureDetail() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role?.toLowerCase() === 'admin';

  const featureId = window.location.pathname.split('/').pop();

  const [feature, setFeature] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Step dialog
  const [stepDialog, setStepDialog] = useState(false);
  const [newStep, setNewStep] = useState({ title: '', description: '' });

  // Edit dialog
  const [editDialog, setEditDialog] = useState(false);
  const [editData, setEditData] = useState({});

  // Delete confirmation
  const [deleteDialog, setDeleteDialog] = useState(false);

  const fetchFeature = async () => {
    setLoading(true);
    try {
      const data = await developmentAPI.getFeature(featureId);
      setFeature(data);
      setEditData({
        title: data.title,
        description: data.description || '',
        status: data.status,
        priority: data.priority,
        target_date: data.target_date || '',
      });
    } catch (error) {
      enqueueSnackbar('Failed to fetch feature', { variant: 'error' });
      navigate('/development');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeature();
  }, [featureId]);

  const handleAddStep = async () => {
    if (!newStep.title.trim()) return;

    try {
      await developmentAPI.createStep(featureId, newStep);
      setNewStep({ title: '', description: '' });
      setStepDialog(false);
      fetchFeature();
      enqueueSnackbar('Step added', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to add step', { variant: 'error' });
    }
  };

  const handleToggleStep = async (step) => {
    const newStatus = step.status === 'done' ? 'todo' : 'done';
    try {
      await developmentAPI.updateStep(step.id, { status: newStatus });
      fetchFeature();
    } catch (error) {
      enqueueSnackbar('Failed to update step', { variant: 'error' });
    }
  };

  const handleDeleteStep = async (stepId) => {
    try {
      await developmentAPI.deleteStep(stepId);
      fetchFeature();
      enqueueSnackbar('Step deleted', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Failed to delete step', { variant: 'error' });
    }
  };

  const handleUpdateFeature = async () => {
    try {
      await developmentAPI.updateFeature(featureId, editData);
      setEditDialog(false);
      fetchFeature();
      enqueueSnackbar('Feature updated', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to update', { variant: 'error' });
    }
  };

  const handleDeleteFeature = async () => {
    try {
      await developmentAPI.deleteFeature(featureId);
      enqueueSnackbar('Feature deleted successfully', { variant: 'success' });
      navigate('/development');
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to delete feature', { variant: 'error' });
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;

    setSubmitting(true);
    try {
      await developmentAPI.addComment(featureId, { comment: newComment });
      setNewComment('');
      fetchFeature();
      enqueueSnackbar('Comment added', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Failed to add comment', { variant: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!feature) {
    return <Alert severity="error">Feature not found</Alert>;
  }

  const statusConfig = getStatusConfig(feature.status);
  const priorityConfig = getPriorityConfig(feature.priority);
  const progress = feature.steps?.length > 0
    ? Math.round((feature.steps.filter(s => s.status === 'done').length / feature.steps.length) * 100)
    : 0;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom>{feature.title}</Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip label={statusConfig.label} color={statusConfig.color} />
            <Chip label={priorityConfig.label} color={priorityConfig.color} variant="outlined" />
            {feature.target_date && (
              <Chip label={`Target: ${formatDate(feature.target_date)}`} variant="outlined" />
            )}
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" onClick={() => navigate('/development')}>Back</Button>
          {isAdmin && (
            <>
              <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setEditDialog(true)}>
                Edit
              </Button>
              <Button variant="outlined" color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteDialog(true)}>
                Delete
              </Button>
            </>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} md={8}>
          {/* Description */}
          {feature.description && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>Description</Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>{feature.description}</Typography>
              </CardContent>
            </Card>
          )}

          {/* Steps */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle1">
                  Steps ({feature.steps?.filter(s => s.status === 'done').length || 0}/{feature.steps?.length || 0})
                </Typography>
                {isAdmin && (
                  <Button size="small" startIcon={<AddIcon />} onClick={() => setStepDialog(true)}>
                    Add Step
                  </Button>
                )}
              </Box>

              {progress > 0 && (
                <LinearProgress variant="determinate" value={progress} sx={{ mb: 2, height: 8, borderRadius: 4 }} />
              )}

              {feature.steps?.length > 0 ? (
                <List>
                  {feature.steps.map((step) => (
                    <ListItem
                      key={step.id}
                      secondaryAction={
                        isAdmin && (
                          <IconButton size="small" onClick={() => handleDeleteStep(step.id)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        )
                      }
                      sx={{ px: 0 }}
                    >
                      <ListItemIcon>
                        <Checkbox
                          checked={step.status === 'done'}
                          onChange={() => handleToggleStep(step)}
                          disabled={!isAdmin}
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={step.title}
                        secondary={step.description}
                        sx={{ textDecoration: step.status === 'done' ? 'line-through' : 'none' }}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  No steps added yet
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Comments */}
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Comments ({feature.comments?.length || 0})
              </Typography>
              <Divider sx={{ mb: 2 }} />

              {feature.comments?.length > 0 ? (
                <List>
                  {feature.comments.map((comment) => (
                    <ListItem key={comment.id} alignItems="flex-start" sx={{ px: 0 }}>
                      <ListItemAvatar>
                        <Avatar>{comment.user_name?.charAt(0) || '?'}</Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Typography variant="subtitle2">{comment.user_name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {formatDate(comment.created_at)}
                            </Typography>
                          </Box>
                        }
                        secondary={comment.comment}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  No comments yet
                </Typography>
              )}

              {/* Add Comment */}
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Add a comment..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  multiline
                  maxRows={4}
                />
                <IconButton color="primary" onClick={handleAddComment} disabled={!newComment.trim() || submitting}>
                  <SendIcon />
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">Created By</Typography>
              <Typography variant="body1" gutterBottom>{feature.created_by_name}</Typography>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" color="text.secondary">Created At</Typography>
              <Typography variant="body1">{formatDate(feature.created_at)}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Add Step Dialog */}
      <Dialog open={stepDialog} onClose={() => setStepDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Step</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Step Title"
              fullWidth
              required
              value={newStep.title}
              onChange={(e) => setNewStep({ ...newStep, title: e.target.value })}
            />
            <TextField
              label="Description (Optional)"
              fullWidth
              multiline
              rows={2}
              value={newStep.description}
              onChange={(e) => setNewStep({ ...newStep, description: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStepDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddStep}>Add</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Feature Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Feature</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Title"
              fullWidth
              value={editData.title || ''}
              onChange={(e) => setEditData({ ...editData, title: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={editData.description || ''}
              onChange={(e) => setEditData({ ...editData, description: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={editData.status || ''}
                label="Status"
                onChange={(e) => setEditData({ ...editData, status: e.target.value })}
              >
                {FEATURE_STATUS.map((s) => (
                  <MenuItem key={s.value} value={s.value}>{s.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={editData.priority || ''}
                label="Priority"
                onChange={(e) => setEditData({ ...editData, priority: e.target.value })}
              >
                {FEATURE_PRIORITY.map((p) => (
                  <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Target Date"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={editData.target_date || ''}
              onChange={(e) => setEditData({ ...editData, target_date: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateFeature}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Feature Confirmation Dialog */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Feature</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this feature? This will permanently delete:
          </Typography>
          <Box component="ul" sx={{ mt: 1 }}>
            <li>The feature "{feature?.title}"</li>
            <li>All {feature?.steps?.length || 0} implementation steps</li>
            <li>All {feature?.comments?.length || 0} comments</li>
          </Box>
          <Typography color="error" sx={{ mt: 2, fontWeight: 'bold' }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={() => { setDeleteDialog(false); handleDeleteFeature(); }}>
            Delete Permanently
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// ============================================================================
// MAIN MODULE COMPONENT
// ============================================================================

export default function DevelopmentModule() {
  return (
    <Box sx={{ p: 3 }}>
      <Routes>
        <Route index element={<FeaturesList />} />
        <Route path=":featureId" element={<FeatureDetail />} />
        <Route path="*" element={<Navigate to="/development" replace />} />
      </Routes>
    </Box>
  );
}

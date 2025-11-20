/**
 * ============================================================================
 * Farm Management System - Tickets Module Frontend
 * ============================================================================
 * Version: 1.0.1
 * Last Updated: 2025-11-20
 *
 * Changelog:
 * ----------
 * v1.0.1 (2025-11-20):
 *   - Version bump to match backend fixes
 *   - No frontend changes required for SQL fix
 *
 * v1.0.0 (2025-11-20):
 *   - Initial tickets module frontend implementation
 *   - Ticket listing with filters (status, type, priority)
 *   - Create new ticket dialog
 *   - View ticket details with comments
 *   - Add/edit/delete comments functionality
 *   - Admin features: set priority, change status, close tickets
 *   - Ticket statistics dashboard
 *   - Pagination support
 *   - Responsive design with Material-UI
 *
 * Description:
 *   Complete frontend interface for the ticket system module. Allows users
 *   to create, view, and manage tickets for issues, feature requests, and
 *   upgrade suggestions. Includes comment threads and admin controls.
 * ============================================================================
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
  ListItemAvatar,
  Avatar,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Close as CloseIcon,
  Send as SendIcon,
  Delete as DeleteIcon,
  BugReport as BugIcon,
  Lightbulb as FeatureIcon,
  TrendingUp as UpgradeIcon,
  MoreHoriz as OthersIcon,
  Comment as CommentIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import useAuthStore from '../store/authStore';
import { ticketsAPI } from '../api';

// ============================================================================
// CONSTANTS
// ============================================================================

const TICKET_TYPES = [
  { value: 'issue', label: 'Issue', icon: <BugIcon />, color: 'error' },
  { value: 'feature_request', label: 'Feature Request', icon: <FeatureIcon />, color: 'info' },
  { value: 'upgrade', label: 'Upgrade', icon: <UpgradeIcon />, color: 'success' },
  { value: 'others', label: 'Others', icon: <OthersIcon />, color: 'default' },
];

const TICKET_STATUS = [
  { value: 'open', label: 'Open', color: 'info' },
  { value: 'in_progress', label: 'In Progress', color: 'warning' },
  { value: 'resolved', label: 'Resolved', color: 'success' },
  { value: 'closed', label: 'Closed', color: 'default' },
];

const TICKET_PRIORITY = [
  { value: 'low', label: 'Low', color: 'success' },
  { value: 'medium', label: 'Medium', color: 'info' },
  { value: 'high', label: 'High', color: 'warning' },
  { value: 'critical', label: 'Critical', color: 'error' },
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const getTypeConfig = (type) => TICKET_TYPES.find((t) => t.value === type) || TICKET_TYPES[3];
const getStatusConfig = (status) => TICKET_STATUS.find((s) => s.value === status) || TICKET_STATUS[0];
const getPriorityConfig = (priority) => TICKET_PRIORITY.find((p) => p.value === priority);

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString();
};

// ============================================================================
// TICKETS LIST COMPONENT
// ============================================================================

function TicketsList() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role?.toLowerCase() === 'admin';

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [stats, setStats] = useState(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [newTicket, setNewTicket] = useState({
    title: '',
    description: '',
    ticket_type: 'issue',
  });

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const params = {
        page: page + 1,
        limit: rowsPerPage,
      };
      if (typeFilter) params.ticket_type = typeFilter;
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;

      const data = await ticketsAPI.getTickets(params);
      setTickets(data.tickets || []);
      setTotal(data.total || 0);
    } catch (error) {
      enqueueSnackbar('Failed to fetch tickets', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await ticketsAPI.getTicketStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    fetchTickets();
    fetchStats();
  }, [page, rowsPerPage, typeFilter, statusFilter, priorityFilter]);

  const handleCreateTicket = async () => {
    if (!newTicket.title.trim() || !newTicket.description.trim()) {
      enqueueSnackbar('Please fill in all required fields', { variant: 'warning' });
      return;
    }

    try {
      await ticketsAPI.createTicket(newTicket);
      enqueueSnackbar('Ticket created successfully', { variant: 'success' });
      setCreateOpen(false);
      setNewTicket({ title: '', description: '', ticket_type: 'issue' });
      fetchTickets();
      fetchStats();
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to create ticket', { variant: 'error' });
    }
  };

  return (
    <Box>
      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="info.main">{stats.open_tickets}</Typography>
                <Typography variant="body2" color="text.secondary">Open</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="warning.main">{stats.in_progress_tickets}</Typography>
                <Typography variant="body2" color="text.secondary">In Progress</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="success.main">{stats.resolved_tickets}</Typography>
                <Typography variant="body2" color="text.secondary">Resolved</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4">{stats.total_tickets}</Typography>
                <Typography variant="body2" color="text.secondary">Total</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Tickets</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
        >
          Create Ticket
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Type</InputLabel>
                <Select
                  value={typeFilter}
                  label="Type"
                  onChange={(e) => { setTypeFilter(e.target.value); setPage(0); }}
                >
                  <MenuItem value="">All Types</MenuItem>
                  {TICKET_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
                >
                  <MenuItem value="">All Status</MenuItem>
                  {TICKET_STATUS.map((status) => (
                    <MenuItem key={status.value} value={status.value}>{status.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Priority</InputLabel>
                <Select
                  value={priorityFilter}
                  label="Priority"
                  onChange={(e) => { setPriorityFilter(e.target.value); setPage(0); }}
                >
                  <MenuItem value="">All Priorities</MenuItem>
                  {TICKET_PRIORITY.map((priority) => (
                    <MenuItem key={priority.value} value={priority.value}>{priority.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tickets Table */}
      <TableContainer component={Paper}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : tickets.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary">No tickets found</Typography>
          </Box>
        ) : (
          <>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Created By</TableCell>
                  <TableCell>Created At</TableCell>
                  <TableCell>Comments</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tickets.map((ticket) => {
                  const typeConfig = getTypeConfig(ticket.ticket_type);
                  const statusConfig = getStatusConfig(ticket.status);
                  const priorityConfig = getPriorityConfig(ticket.priority);

                  return (
                    <TableRow key={ticket.id} hover>
                      <TableCell>#{ticket.id}</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {ticket.title}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={typeConfig.icon}
                          label={typeConfig.label}
                          size="small"
                          color={typeConfig.color}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={statusConfig.label}
                          size="small"
                          color={statusConfig.color}
                        />
                      </TableCell>
                      <TableCell>
                        {priorityConfig ? (
                          <Chip
                            label={priorityConfig.label}
                            size="small"
                            color={priorityConfig.color}
                            variant="outlined"
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell>{ticket.created_by_name}</TableCell>
                      <TableCell>{formatDate(ticket.created_at)}</TableCell>
                      <TableCell>
                        <Chip
                          icon={<CommentIcon />}
                          label={ticket.comment_count}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/tickets/${ticket.id}`)}
                        >
                          <ViewIcon />
                        </IconButton>
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

      {/* Create Ticket Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Ticket</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Title"
              fullWidth
              required
              value={newTicket.title}
              onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
            />
            <FormControl fullWidth required>
              <InputLabel>Type</InputLabel>
              <Select
                value={newTicket.ticket_type}
                label="Type"
                onChange={(e) => setNewTicket({ ...newTicket, ticket_type: e.target.value })}
              >
                {TICKET_TYPES.map((type) => (
                  <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Description"
              fullWidth
              required
              multiline
              rows={4}
              value={newTicket.description}
              onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
              placeholder="Describe your issue, feature request, or suggestion in detail..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateTicket}>Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// ============================================================================
// TICKET DETAIL COMPONENT
// ============================================================================

function TicketDetail() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role?.toLowerCase() === 'admin';

  const ticketId = window.location.pathname.split('/').pop();

  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Admin controls
  const [adminDialog, setAdminDialog] = useState(false);
  const [adminUpdate, setAdminUpdate] = useState({
    status: '',
    priority: '',
  });
  const [closeDialog, setCloseDialog] = useState(false);
  const [closeComment, setCloseComment] = useState('');

  const fetchTicket = async () => {
    setLoading(true);
    try {
      const data = await ticketsAPI.getTicket(ticketId);
      setTicket(data);
      setAdminUpdate({
        status: data.status || '',
        priority: data.priority || '',
      });
    } catch (error) {
      enqueueSnackbar('Failed to fetch ticket', { variant: 'error' });
      navigate('/tickets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTicket();
  }, [ticketId]);

  const handleAddComment = async () => {
    if (!newComment.trim()) return;

    setSubmitting(true);
    try {
      await ticketsAPI.addComment(ticketId, { comment: newComment });
      setNewComment('');
      fetchTicket();
      enqueueSnackbar('Comment added', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to add comment', { variant: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAdminUpdate = async () => {
    try {
      const updateData = {};
      if (adminUpdate.status) updateData.status = adminUpdate.status;
      if (adminUpdate.priority) updateData.priority = adminUpdate.priority;

      await ticketsAPI.adminUpdateTicket(ticketId, updateData);
      setAdminDialog(false);
      fetchTicket();
      enqueueSnackbar('Ticket updated', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to update ticket', { variant: 'error' });
    }
  };

  const handleCloseTicket = async () => {
    try {
      await ticketsAPI.closeTicket(ticketId, closeComment || null);
      setCloseDialog(false);
      fetchTicket();
      enqueueSnackbar('Ticket closed', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to close ticket', { variant: 'error' });
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!ticket) {
    return (
      <Alert severity="error">Ticket not found</Alert>
    );
  }

  const typeConfig = getTypeConfig(ticket.ticket_type);
  const statusConfig = getStatusConfig(ticket.status);
  const priorityConfig = getPriorityConfig(ticket.priority);
  const isClosed = ticket.status === 'closed';

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            #{ticket.id} - {ticket.title}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              icon={typeConfig.icon}
              label={typeConfig.label}
              color={typeConfig.color}
              variant="outlined"
            />
            <Chip label={statusConfig.label} color={statusConfig.color} />
            {priorityConfig && (
              <Chip label={priorityConfig.label} color={priorityConfig.color} variant="outlined" />
            )}
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" onClick={() => navigate('/tickets')}>
            Back
          </Button>
          {isAdmin && !isClosed && (
            <>
              <Button variant="outlined" onClick={() => setAdminDialog(true)}>
                Update
              </Button>
              <Button
                variant="contained"
                color="error"
                startIcon={<CloseIcon />}
                onClick={() => setCloseDialog(true)}
              >
                Close Ticket
              </Button>
            </>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} md={8}>
          {/* Description */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Description
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {ticket.description}
              </Typography>
            </CardContent>
          </Card>

          {/* Comments */}
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Comments ({ticket.comments?.length || 0})
              </Typography>
              <Divider sx={{ mb: 2 }} />

              {ticket.comments?.length > 0 ? (
                <List>
                  {ticket.comments.map((comment) => (
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
                        secondary={
                          <Typography variant="body2" sx={{ mt: 1, whiteSpace: 'pre-wrap' }}>
                            {comment.comment}
                          </Typography>
                        }
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
              {!isClosed && (
                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  <TextField
                    fullWidth
                    size="small"
                    placeholder="Add a comment..."
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleAddComment();
                      }
                    }}
                    multiline
                    maxRows={4}
                  />
                  <IconButton
                    color="primary"
                    onClick={handleAddComment}
                    disabled={!newComment.trim() || submitting}
                  >
                    <SendIcon />
                  </IconButton>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">Created By</Typography>
              <Typography variant="body1" gutterBottom>{ticket.created_by_name}</Typography>
              <Typography variant="caption" color="text.secondary">{ticket.created_by_email}</Typography>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" color="text.secondary">Created At</Typography>
              <Typography variant="body1" gutterBottom>{formatDate(ticket.created_at)}</Typography>

              {ticket.updated_at && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" color="text.secondary">Last Updated</Typography>
                  <Typography variant="body1" gutterBottom>{formatDate(ticket.updated_at)}</Typography>
                </>
              )}

              {ticket.closed_at && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" color="text.secondary">Closed At</Typography>
                  <Typography variant="body1" gutterBottom>{formatDate(ticket.closed_at)}</Typography>
                  <Typography variant="subtitle2" color="text.secondary">Closed By</Typography>
                  <Typography variant="body1">{ticket.closed_by_name}</Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Admin Update Dialog */}
      <Dialog open={adminDialog} onClose={() => setAdminDialog(false)}>
        <DialogTitle>Update Ticket</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 300 }}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={adminUpdate.status}
                label="Status"
                onChange={(e) => setAdminUpdate({ ...adminUpdate, status: e.target.value })}
              >
                {TICKET_STATUS.filter(s => s.value !== 'closed').map((status) => (
                  <MenuItem key={status.value} value={status.value}>{status.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={adminUpdate.priority}
                label="Priority"
                onChange={(e) => setAdminUpdate({ ...adminUpdate, priority: e.target.value })}
              >
                <MenuItem value="">Not Set</MenuItem>
                {TICKET_PRIORITY.map((priority) => (
                  <MenuItem key={priority.value} value={priority.value}>{priority.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdminDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAdminUpdate}>Update</Button>
        </DialogActions>
      </Dialog>

      {/* Close Ticket Dialog */}
      <Dialog open={closeDialog} onClose={() => setCloseDialog(false)}>
        <DialogTitle>Close Ticket</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Are you sure you want to close this ticket? You can optionally add a closing comment.
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Closing Comment (Optional)"
            value={closeComment}
            onChange={(e) => setCloseComment(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCloseDialog(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleCloseTicket}>
            Close Ticket
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// ============================================================================
// MAIN MODULE COMPONENT
// ============================================================================

export default function TicketsModule() {
  return (
    <Box sx={{ p: 3 }}>
      <Routes>
        <Route index element={<TicketsList />} />
        <Route path=":ticketId" element={<TicketDetail />} />
        <Route path="*" element={<Navigate to="/tickets" replace />} />
      </Routes>
    </Box>
  );
}

/**
 * ============================================================================
 * Marketplace ERP - Tickets Module Frontend (TypeScript)
 * ============================================================================
 * Version: 2.0.0
 * Last Updated: 2025-12-07
 *
 * Changelog:
 * ----------
 * v2.0.0 (2025-12-07):
 *   - MAJOR: Rewritten in TypeScript with category-based tabs
 *   - Added ticket categories: Internal, B2B, B2C
 *   - Tab interface for filtering by category
 *   - Category selector in create ticket dialog
 *   - Improved type safety with TypeScript
 *
 * Description:
 *   Complete frontend interface for the categorized ticket system. Allows users
 *   to create, view, and manage tickets across three categories: Internal (ERP
 *   issues), B2B (B2B customer complaints), and B2C (B2C customer complaints).
 * ============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Tabs,
  Tab,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
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
  Grid,
  SelectChangeEvent,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  BugReport as BugIcon,
  Lightbulb as FeatureIcon,
  TrendingUp as UpgradeIcon,
  MoreHoriz as OthersIcon,
  Business as B2BIcon,
  People as B2CIcon,
  HomeWork as InternalIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import useAuthStore from '../store/authStore';
import { ticketsAPI } from '../api';

// ============================================================================
// TYPES
// ============================================================================

type TicketCategory = 'internal' | 'b2b' | 'b2c';
type TicketType = 'issue' | 'feature_request' | 'upgrade' | 'others';
type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed';
type TicketPriority = 'low' | 'medium' | 'high' | 'critical';

interface Ticket {
  id: number;
  title: string;
  description: string;
  ticket_type: TicketType;
  ticket_category: TicketCategory;
  status: TicketStatus;
  priority?: TicketPriority;
  created_by_id: string;
  created_by_name: string;
  created_by_email?: string;
  closed_by_id?: string;
  closed_by_name?: string;
  closed_at?: string;
  created_at: string;
  updated_at?: string;
  comment_count?: number;
}

interface TicketsListResponse {
  tickets: Ticket[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

interface CreateTicketData {
  title: string;
  description: string;
  ticket_type: TicketType;
  ticket_category: TicketCategory;
}

interface TicketStats {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  by_category: Record<string, number>;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const TICKET_CATEGORIES = [
  { value: 'internal' as TicketCategory, label: 'Internal', icon: <InternalIcon />, color: '#7b1fa2' as const },
  { value: 'b2b' as TicketCategory, label: 'B2B', icon: <B2BIcon />, color: '#1976d2' as const },
  { value: 'b2c' as TicketCategory, label: 'B2C', icon: <B2CIcon />, color: '#388e3c' as const },
];

const TICKET_TYPES = [
  { value: 'issue' as TicketType, label: 'Issue', icon: <BugIcon />, color: 'error' as const },
  { value: 'feature_request' as TicketType, label: 'Feature Request', icon: <FeatureIcon />, color: 'info' as const },
  { value: 'upgrade' as TicketType, label: 'Upgrade', icon: <UpgradeIcon />, color: 'success' as const },
  { value: 'others' as TicketType, label: 'Others', icon: <OthersIcon />, color: 'default' as const },
];

const TICKET_STATUS = [
  { value: 'open' as TicketStatus, label: 'Open', color: 'info' as const },
  { value: 'in_progress' as TicketStatus, label: 'In Progress', color: 'warning' as const },
  { value: 'resolved' as TicketStatus, label: 'Resolved', color: 'success' as const },
  { value: 'closed' as TicketStatus, label: 'Closed', color: 'default' as const },
];

const TICKET_PRIORITY = [
  { value: 'low' as TicketPriority, label: 'Low', color: 'success' as const },
  { value: 'medium' as TicketPriority, label: 'Medium', color: 'info' as const },
  { value: 'high' as TicketPriority, label: 'High', color: 'warning' as const },
  { value: 'critical' as TicketPriority, label: 'Critical', color: 'error' as const },
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const getCategoryConfig = (category: TicketCategory) =>
  TICKET_CATEGORIES.find((c) => c.value === category) || TICKET_CATEGORIES[0];

const getTypeConfig = (type: TicketType) =>
  TICKET_TYPES.find((t) => t.value === type) || TICKET_TYPES[0];

const getStatusConfig = (status: TicketStatus) =>
  TICKET_STATUS.find((s) => s.value === status) || TICKET_STATUS[0];

const getPriorityConfig = (priority: TicketPriority) =>
  TICKET_PRIORITY.find((p) => p.value === priority);

const formatDate = (dateString?: string): string => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString();
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function TicketsModule() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === 'Admin';

  // Tickets state
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const [rowsPerPage, setRowsPerPage] = useState<number>(10);
  const [stats, setStats] = useState<TicketStats | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');

  // Create dialog
  const [createOpen, setCreateOpen] = useState<boolean>(false);
  const [newTicket, setNewTicket] = useState<CreateTicketData>({
    title: '',
    description: '',
    ticket_type: 'issue',
    ticket_category: 'internal',
  });

  // ============================================================================
  // API CALLS
  // ============================================================================

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const params: any = {
        page: page + 1,
        limit: rowsPerPage,
        ticket_category: 'internal',
      };
      if (typeFilter) params.ticket_type = typeFilter;
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;

      const data: TicketsListResponse = await ticketsAPI.getTickets(params);
      setTickets(data.tickets || []);
      setTotal(data.total || 0);
    } catch (error: any) {
      enqueueSnackbar('Failed to fetch internal tickets', { variant: 'error' });
      console.error('Failed to fetch tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data: TicketStats = await ticketsAPI.getTicketStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [page, rowsPerPage, typeFilter, statusFilter, priorityFilter]);

  useEffect(() => {
    fetchStats();
  }, []);

  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================

  const handleCreateTicket = async () => {
    if (!newTicket.title.trim() || !newTicket.description.trim()) {
      enqueueSnackbar('Please fill in all required fields', { variant: 'warning' });
      return;
    }

    try {
      await ticketsAPI.createTicket({
        title: newTicket.title,
        description: newTicket.description,
        ticket_type: newTicket.ticket_type,
        ticket_category: newTicket.ticket_category,
      });

      enqueueSnackbar('Ticket created successfully', { variant: 'success' });
      setCreateOpen(false);
      setNewTicket({
        title: '',
        description: '',
        ticket_type: 'issue',
        ticket_category: 'internal', // Hardcoded to internal
      });

      // Refresh if the created ticket matches current tab
      // Always refresh for internal tickets
      fetchTickets();
      fetchStats();
    } catch (error: any) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to create ticket', {
        variant: 'error',
      });
    }
  };

  const handleOpenCreate = () => {
    // Set default category to current tab when opening dialog
    setNewTicket((prev) => ({
      ...prev,
      ticket_category: 'internal',
    }));
    setCreateOpen(true);
  };

  const handleViewTicket = (ticketId: number) => {
    navigate(`/tickets/${ticketId}`);
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // ============================================================================
  // RENDER
  // ============================================================================



  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Tickets
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage support tickets across Internal, B2B, and B2C categories
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenCreate}
          sx={{ minWidth: 150 }}
        >
          New Ticket
        </Button>
      </Box>

      {/* Statistics Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography variant="overline" color="text.secondary">
                  Total
                </Typography>
                <Typography variant="h4">{stats.total_tickets}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography variant="overline" color="text.secondary">
                  Open
                </Typography>
                <Typography variant="h4" color="info.main">
                  {stats.open_tickets}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography variant="overline" color="text.secondary">
                  In Progress
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {stats.in_progress_tickets}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography variant="overline" color="text.secondary">
                  Resolved
                </Typography>
                <Typography variant="h4" color="success.main">
                  {stats.resolved_tickets}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography variant="overline" color="text.secondary">
                  Closed
                </Typography>
                <Typography variant="h4" color="text.disabled">
                  {stats.closed_tickets}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}



      {/* Filters */}
      <Card sx={{ mb: 3, p: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Type</InputLabel>
              <Select
                value={typeFilter}
                onChange={(e: SelectChangeEvent) => setTypeFilter(e.target.value)}
                label="Type"
              >
                <MenuItem value="">All Types</MenuItem>
                {TICKET_TYPES.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e: SelectChangeEvent) => setStatusFilter(e.target.value)}
                label="Status"
              >
                <MenuItem value="">All Statuses</MenuItem>
                {TICKET_STATUS.map((status) => (
                  <MenuItem key={status.value} value={status.value}>
                    {status.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Priority</InputLabel>
              <Select
                value={priorityFilter}
                onChange={(e: SelectChangeEvent) => setPriorityFilter(e.target.value)}
                label="Priority"
              >
                <MenuItem value="">All Priorities</MenuItem>
                {TICKET_PRIORITY.map((priority) => (
                  <MenuItem key={priority.value} value={priority.value}>
                    {priority.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Card>

      {/* Tickets Table */}
      <Card>
        <TableContainer>
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
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 5 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : tickets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 5 }}>
                    <Typography variant="body2" color="text.secondary">
                      No Internal tickets found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                tickets.map((ticket) => {
                  const typeConfig = getTypeConfig(ticket.ticket_type);
                  const statusConfig = getStatusConfig(ticket.status);
                  const priorityConfig = ticket.priority
                    ? getPriorityConfig(ticket.priority)
                    : null;

                  return (
                    <TableRow key={ticket.id} hover>
                      <TableCell>#{ticket.id}</TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
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
                          />
                        ) : (
                          <Typography variant="caption" color="text.disabled">
                            Unassigned
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {ticket.created_by_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(ticket.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={ticket.comment_count || 0}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Button
                          size="small"
                          startIcon={<ViewIcon />}
                          onClick={() => handleViewTicket(ticket.id)}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Card>

      {/* Create Ticket Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Ticket</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>


            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={newTicket.ticket_type}
                onChange={(e: SelectChangeEvent<TicketType>) =>
                  setNewTicket({ ...newTicket, ticket_type: e.target.value as TicketType })
                }
                label="Type"
              >
                {TICKET_TYPES.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {type.icon}
                      {type.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Title"
              value={newTicket.title}
              onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
              required
            />

            <TextField
              fullWidth
              label="Description"
              value={newTicket.description}
              onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
              multiline
              rows={6}
              required
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateTicket} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

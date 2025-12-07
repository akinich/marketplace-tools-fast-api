/**
 * ============================================================================
 * Marketplace ERP - Tickets Dashboard (TypeScript)
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-12-07
 *
 * Description:
 *   Unified dashboard for all ticket categories (Internal, B2B, B2C).
 *   Shows category-wise statistics cards and a combined table of recent
 *   tickets from all categories.
 *
 * Features:
 *   - Category cards with status breakdown (Open, In Progress, Resolved, Closed)
 *   - Recent tickets table from all categories
 *   - Click to view ticket details
 *   - View-only interface (no create/edit actions)
 * ============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
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
  IconButton,
  Divider,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Business as B2BIcon,
  People as B2CIcon,
  HomeWork as InternalIcon,
  BugReport as BugIcon,
  Lightbulb as FeatureIcon,
  TrendingUp as UpgradeIcon,
  MoreHoriz as OthersIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { ticketsAPI } from '../api';

// ============================================================================
// TYPES
// ============================================================================

type TicketCategory = 'internal' | 'b2b' | 'b2c';
type TicketType = 'issue' | 'feature_request' | 'upgrade' | 'others';
type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed';
type TicketPriority = 'low' | 'medium' | 'high' | 'critical';

interface CategoryStats {
  total: number;
  open: number;
  in_progress: number;
  resolved: number;
  closed: number;
}

interface DashboardStats {
  internal: CategoryStats;
  b2b: CategoryStats;
  b2c: CategoryStats;
  total_across_categories: CategoryStats;
}

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
  created_at: string;
  updated_at?: string;
  comment_count?: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const TICKET_CATEGORIES = [
  { value: 'internal' as TicketCategory, label: 'Internal', icon: <InternalIcon />, color: '#7b1fa2' },
  { value: 'b2b' as TicketCategory, label: 'B2B', icon: <B2BIcon />, color: '#1976d2' },
  { value: 'b2c' as TicketCategory, label: 'B2C', icon: <B2CIcon />, color: '#388e3c' },
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

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const getCategoryConfig = (category: TicketCategory) =>
  TICKET_CATEGORIES.find((c) => c.value === category) || TICKET_CATEGORIES[0];

const getTypeConfig = (type: TicketType) =>
  TICKET_TYPES.find((t) => t.value === type) || TICKET_TYPES[0];

const getStatusConfig = (status: TicketStatus) =>
  TICKET_STATUS.find((s) => s.value === status) || TICKET_STATUS[0];

const formatDate = (dateString?: string): string => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString();
};

// ============================================================================
// CATEGORY CARD COMPONENT
// ============================================================================

interface CategoryCardProps {
  category: TicketCategory;
  stats: CategoryStats;
  onClick?: () => void;
}

function CategoryCard({ category, stats, onClick }: CategoryCardProps) {
  const config = getCategoryConfig(category);

  return (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s',
        '&:hover': onClick ? {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        } : {},
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Box sx={{ color: config.color }}>{config.icon}</Box>
          <Typography variant="h6" fontWeight="bold">
            {config.label}
          </Typography>
        </Box>

        <Typography variant="h3" sx={{ mb: 2, color: config.color }}>
          {stats.total}
        </Typography>

        <Divider sx={{ my: 2 }} />

        <Grid container spacing={1}>
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Open
              </Typography>
              <Typography variant="h6" color="info.main">
                {stats.open}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                In Progress
              </Typography>
              <Typography variant="h6" color="warning.main">
                {stats.in_progress}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Resolved
              </Typography>
              <Typography variant="h6" color="success.main">
                {stats.resolved}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Closed
              </Typography>
              <Typography variant="h6" color="text.disabled">
                {stats.closed}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function TicketsDashboard() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const [loading, setLoading] = useState<boolean>(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentTickets, setRecentTickets] = useState<Ticket[]>([]);

  // ============================================================================
  // API CALLS
  // ============================================================================

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch dashboard stats
      const dashboardStats: DashboardStats = await ticketsAPI.getDashboardStats();
      setStats(dashboardStats);

      // Fetch recent tickets from all categories (last 20 tickets)
      const ticketsData = await ticketsAPI.getTickets({ page: 1, limit: 20 });
      setRecentTickets(ticketsData.tickets || []);
    } catch (error: any) {
      enqueueSnackbar('Failed to fetch dashboard data', { variant: 'error' });
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================

  const handleViewTicket = (ticketId: number) => {
    navigate(`/tickets/${ticketId}`);
  };

  const handleNavigateToCategory = (category: TicketCategory) => {
    navigate(`/tickets?category=${category}`);
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!stats) {
    return (
      <Alert severity="error">
        Failed to load dashboard data. Please try again.
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom fontWeight="bold">
          Tickets Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Overview of all tickets across Internal, B2B, and B2C categories
        </Typography>
      </Box>

      {/* Category Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <CategoryCard
            category="internal"
            stats={stats.internal}
            onClick={() => handleNavigateToCategory('internal')}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <CategoryCard
            category="b2b"
            stats={stats.b2b}
            onClick={() => handleNavigateToCategory('b2b')}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <CategoryCard
            category="b2c"
            stats={stats.b2c}
            onClick={() => handleNavigateToCategory('b2c')}
          />
        </Grid>
      </Grid>

      {/* Total Summary Card */}
      <Card sx={{ mb: 4, bgcolor: 'primary.main', color: 'white' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Total Across All Categories
          </Typography>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption">Total</Typography>
              <Typography variant="h4">{stats.total_across_categories.total}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption">Open</Typography>
              <Typography variant="h4">{stats.total_across_categories.open}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption">In Progress</Typography>
              <Typography variant="h4">{stats.total_across_categories.in_progress}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption">Resolved</Typography>
              <Typography variant="h4">{stats.total_across_categories.resolved}</Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Recent Tickets Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Tickets
          </Typography>
        </CardContent>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created By</TableCell>
                <TableCell>Created At</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recentTickets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 5 }}>
                    <Typography variant="body2" color="text.secondary">
                      No tickets found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                recentTickets.map((ticket) => {
                  const categoryConfig = getCategoryConfig(ticket.ticket_category);
                  const typeConfig = getTypeConfig(ticket.ticket_type);
                  const statusConfig = getStatusConfig(ticket.status);

                  return (
                    <TableRow key={ticket.id} hover>
                      <TableCell>#{ticket.id}</TableCell>
                      <TableCell>
                        <Chip
                          icon={categoryConfig.icon}
                          label={categoryConfig.label}
                          size="small"
                          sx={{
                            bgcolor: categoryConfig.color,
                            color: 'white',
                          }}
                        />
                      </TableCell>
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
                        <Typography variant="body2">
                          {ticket.created_by_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(ticket.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          onClick={() => handleViewTicket(ticket.id)}
                          color="primary"
                        >
                          <ViewIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Box>
  );
}

/**
 * Dashboard Home Page - Role-Based Dynamic Dashboard
 * Version: 2.1.0
 * Last Updated: 2025-11-22
 *
 * Changelog:
 * ----------
 * v2.1.0 (2025-11-22):
 *   - Integrated WebSocket real-time dashboard updates
 *   - Auto-refetch data when dashboard.update event is received
 *   - Maintains 60-second polling as fallback
 *
 * v2.0.0 (2025-11-22):
 *   - BREAKING: Complete rewrite for role-based dynamic widgets
 *   - Widgets now rendered based on user's module access
 *   - Separate widget sections for inventory, biofloc, admin, tickets
 *   - Uses new /dashboard/widgets endpoint
 *   - Admins see all widgets, users see only modules they have access to
 *
 * v1.1.0 (2025-11-17):
 *   - Added INR currency formatting for inventory value
 *   - Uses formatCurrency utility with Indian Rupee symbol (₹)
 *
 * v1.0.0 (2025-11-17):
 *   - Initial dashboard home page
 */

import React, { useEffect } from 'react';
import { useQuery } from 'react-query';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Divider,
  Chip,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  Warning as WarningIcon,
  People as PeopleIcon,
  ShoppingCart as ShoppingCartIcon,
  Science as BioflocIcon,
  WaterDrop as WaterIcon,
  ConfirmationNumber as TicketsIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

import { dashboardAPI } from '../api';
import { formatCurrency } from '../utils/formatters';
import useAuthStore from '../store/authStore';
import websocketService from '../services/websocket';

const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography color="textSecondary" gutterBottom variant="overline">
            {title}
          </Typography>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {subtitle}
            </Typography>
          )}
        </Box>
        <Icon sx={{ fontSize: 48, color: color || 'primary.main', opacity: 0.3 }} />
      </Box>
    </CardContent>
  </Card>
);

const SectionHeader = ({ title, icon: Icon, color }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, mt: 4 }}>
    <Icon sx={{ color: color || 'primary.main' }} />
    <Typography variant="h6" fontWeight="bold">
      {title}
    </Typography>
  </Box>
);

export default function DashboardHome() {
  const { user } = useAuthStore();
  const { data: widgets, isLoading, error, refetch } = useQuery('dashboardWidgets', dashboardAPI.getWidgets, {
    refetchInterval: 60000, // Refresh every minute
  });

  // Listen for WebSocket dashboard updates
  useEffect(() => {
    const handleDashboardUpdate = (data) => {
      console.log('Dashboard update received via WebSocket');
      // Refetch data when update is received
      refetch();
    };

    websocketService.on('dashboard.update', handleDashboardUpdate);

    return () => {
      websocketService.off('dashboard.update', handleDashboardUpdate);
    };
  }, [refetch]);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load dashboard data: {error.message}
      </Alert>
    );
  }

  const hasInventory = widgets?.inventory !== undefined;
  const hasBiofloc = widgets?.biofloc !== undefined;
  const hasAdmin = widgets?.admin !== undefined;
  const hasTickets = widgets?.tickets !== undefined;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom fontWeight="bold">
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back, {user?.full_name || 'User'}! Here's your farm overview.
        </Typography>
        <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {hasInventory && <Chip label="Inventory" size="small" color="primary" variant="outlined" />}
          {hasBiofloc && <Chip label="Biofloc" size="small" color="success" variant="outlined" />}
          {hasAdmin && <Chip label="Admin" size="small" color="secondary" variant="outlined" />}
          {hasTickets && <Chip label="Tickets" size="small" color="warning" variant="outlined" />}
        </Box>
      </Box>

      {/* Inventory Section */}
      {hasInventory && (
        <>
          <SectionHeader title="Inventory Management" icon={InventoryIcon} color="#2e7d32" />
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Items"
                value={widgets.inventory.total_items}
                icon={InventoryIcon}
                color="#2e7d32"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Low Stock Items"
                value={widgets.inventory.low_stock_items}
                icon={WarningIcon}
                color="#ff9800"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Pending POs"
                value={widgets.inventory.pending_pos}
                icon={ShoppingCartIcon}
                color="#ff6f00"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom variant="overline">
                    Total Inventory Value
                  </Typography>
                  <Typography variant="h5" component="div">
                    {formatCurrency(widgets.inventory.total_stock_value)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Current stock value (INR)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}

      {/* Biofloc Section */}
      {hasBiofloc && (
        <>
          <SectionHeader title="Biofloc Operations" icon={BioflocIcon} color="#1976d2" />
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Active Tanks"
                value={widgets.biofloc.active_tanks}
                icon={WaterIcon}
                color="#1976d2"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Active Batches"
                value={widgets.biofloc.active_batches}
                icon={BioflocIcon}
                color="#0288d1"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Stock"
                value={widgets.biofloc.total_stock.toLocaleString()}
                icon={TrendingUpIcon}
                color="#00897b"
                subtitle="Fish count"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Tanks Needing Attention"
                value={widgets.biofloc.tanks_needing_attention}
                icon={WarningIcon}
                color="#f57c00"
              />
            </Grid>
          </Grid>
        </>
      )}

      {/* Admin Section */}
      {hasAdmin && (
        <>
          <SectionHeader title="Administration" icon={PeopleIcon} color="#7b1fa2" />
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Users"
                value={widgets.admin.total_users}
                icon={PeopleIcon}
                color="#7b1fa2"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Active Users"
                value={widgets.admin.active_users}
                icon={CheckCircleIcon}
                color="#388e3c"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Logins (24h)"
                value={widgets.admin.recent_logins_24h}
                icon={TrendingUpIcon}
                color="#1976d2"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Activities (7 days)"
                value={widgets.admin.total_activities_7d.toLocaleString()}
                icon={TrendingUpIcon}
                color="#0288d1"
              />
            </Grid>
          </Grid>
        </>
      )}

      {/* Tickets Section */}
      {hasTickets && (
        <>
          <SectionHeader title="Tickets & Support" icon={TicketsIcon} color="#f57c00" />
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Open Tickets"
                value={widgets.tickets.open_tickets}
                icon={TicketsIcon}
                color="#f57c00"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="In Progress"
                value={widgets.tickets.in_progress_tickets}
                icon={WarningIcon}
                color="#ff9800"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Resolved"
                value={widgets.tickets.resolved_tickets}
                icon={CheckCircleIcon}
                color="#388e3c"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Closed"
                value={widgets.tickets.closed_tickets}
                icon={CheckCircleIcon}
                color="#616161"
              />
            </Grid>
          </Grid>
        </>
      )}

      {/* No modules message */}
      {!hasInventory && !hasBiofloc && !hasAdmin && !hasTickets && (
        <Alert severity="info" sx={{ mt: 3 }}>
          You don't have access to any modules yet. Please contact your administrator to request access.
        </Alert>
      )}

      {/* Footer spacing */}
      <Box sx={{ pb: 4 }} />
    </Box>
  );
}

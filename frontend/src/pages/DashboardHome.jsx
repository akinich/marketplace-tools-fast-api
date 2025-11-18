/**
 * Dashboard Home Page
 * Version: 1.1.0
 * Last Updated: 2025-11-17
 *
 * Changelog:
 * ----------
 * v1.1.0 (2025-11-17):
 *   - Added INR currency formatting for inventory value
 *   - Uses formatCurrency utility with Indian Rupee symbol (₹)
 *
 * v1.0.0 (2025-11-17):
 *   - Initial dashboard home page
 */

import React from 'react';
import { useQuery } from 'react-query';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  Warning as WarningIcon,
  People as PeopleIcon,
  ShoppingCart as ShoppingCartIcon,
} from '@mui/icons-material';

import { dashboardAPI } from '../api';
import { formatCurrency } from '../utils/formatters';

const StatCard = ({ title, value, icon: Icon, color }) => (
  <Card>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography color="textSecondary" gutterBottom variant="overline">
            {title}
          </Typography>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
        </Box>
        <Icon sx={{ fontSize: 48, color: color || 'primary.main', opacity: 0.3 }} />
      </Box>
    </CardContent>
  </Card>
);

export default function DashboardHome() {
  const { data, isLoading, error } = useQuery('dashboardSummary', dashboardAPI.getSummary);

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

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Welcome back! Here's your farm overview.
      </Typography>

      <Grid container spacing={3}>
        {/* Inventory Stats */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Items"
            value={data?.total_inventory_items || 0}
            icon={InventoryIcon}
            color="#2e7d32"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Low Stock Items"
            value={data?.low_stock_items || 0}
            icon={WarningIcon}
            color="#ff9800"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending POs"
            value={data?.pending_pos || 0}
            icon={ShoppingCartIcon}
            color="#ff6f00"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Users"
            value={data?.active_users || 0}
            icon={PeopleIcon}
            color="#1976d2"
          />
        </Grid>

        {/* Activity Summary */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Logins (24h): {data?.recent_logins_24h || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Activities (7 days): {data?.total_activities_7d || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Inventory Value */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Inventory Value
              </Typography>
              <Typography variant="h4">
                {formatCurrency(data?.total_inventory_value || 0)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total stock value (INR)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

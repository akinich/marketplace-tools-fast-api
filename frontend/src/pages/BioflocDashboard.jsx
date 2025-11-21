/**
 * ============================================================================
 * Biofloc Dashboard Page
 * ============================================================================
 * Version: 1.2.0
 * Last Updated: 2025-11-21
 *
 * Changelog:
 * ----------
 * v1.2.0 (2025-11-21):
 *   - Converted Material-UI icon imports to individual imports for better tree-shaking
 *   - Migrated from react-query v3 to @tanstack/react-query v5
 *   - Bundle size optimization as part of code splitting initiative
 *
 * v1.1.0 (2025-11-19):
 *   - CRITICAL FIX: Added safeToFixed() helper to prevent .toFixed() crashes
 *   - Fixed TypeError when backend returns string values instead of numbers
 *   - Applied safe number formatting to biomass and utilization displays
 *
 * v1.0.0 (2025-11-18):
 *   - Initial biofloc dashboard with key metrics
 *   - Dashboard summary statistics
 *   - Quick access to operations
 * ============================================================================
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Chip,
  LinearProgress,
} from '@mui/material';
import TankIcon from '@mui/icons-material/Pool';
import BatchIcon from '@mui/icons-material/Inventory2';
import GrowthIcon from '@mui/icons-material/ShowChart';
import WarningIcon from '@mui/icons-material/Warning';
import WaterIcon from '@mui/icons-material/Opacity';
import HarvestIcon from '@mui/icons-material/LocalShipping';
import AddIcon from '@mui/icons-material/Add';

import { bioflocAPI } from '../api';

// Safe number formatting helper
const safeToFixed = (value, decimals = 0) => {
  const num = Number(value);
  return (isNaN(num) || !isFinite(num) ? 0 : num).toFixed(decimals);
};

// Stat Card Component
const StatCard = ({ title, value, subtitle, icon: Icon, color, onClick }) => (
  <Card sx={{ cursor: onClick ? 'pointer' : 'default' }} onClick={onClick}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography color="textSecondary" gutterBottom variant="overline">
            {title}
          </Typography>
          <Typography variant="h3" component="div" fontWeight="bold">
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {subtitle}
            </Typography>
          )}
        </Box>
        <Icon sx={{ fontSize: 56, color: color || 'primary.main', opacity: 0.3 }} />
      </Box>
    </CardContent>
  </Card>
);

// Alert Card Component
const AlertCard = ({ title, count, severity, icon: Icon }) => (
  <Card sx={{ borderLeft: `4px solid ${
    severity === 'error' ? '#f44336' :
    severity === 'warning' ? '#ff9800' :
    '#4caf50'
  }` }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Icon sx={{ fontSize: 40, color:
          severity === 'error' ? '#f44336' :
          severity === 'warning' ? '#ff9800' :
          '#4caf50'
        }} />
        <Box>
          <Typography variant="h6">{title}</Typography>
          <Typography variant="h4" fontWeight="bold">{count}</Typography>
        </Box>
      </Box>
    </CardContent>
  </Card>
);

export default function BioflocDashboard() {
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery(
    'bioflocDashboard',
    bioflocAPI.getDashboard,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load biofloc dashboard: {error.message}
      </Alert>
    );
  }

  // Calculate tank utilization percentage
  const tankUtilization = data?.avg_tank_utilization || 0;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Biofloc Aquaculture Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time monitoring and management of your aquaculture operations
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/biofloc/tanks/new')}
          >
            New Tank
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<AddIcon />}
            onClick={() => navigate('/biofloc/batches/new')}
          >
            New Batch
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Tank Statistics */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Tanks"
            value={data?.active_tanks || 0}
            subtitle={`${data?.available_tanks || 0} available`}
            icon={TankIcon}
            color="#0288d1"
            onClick={() => navigate('/biofloc/tanks')}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Batches"
            value={data?.active_batches || 0}
            subtitle={`${data?.total_fish_count?.toLocaleString() || 0} fish`}
            icon={BatchIcon}
            color="#388e3c"
            onClick={() => navigate('/biofloc/batches')}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Biomass"
            value={`${safeToFixed(data?.total_biomass_kg, 1)} kg`}
            subtitle="Current stock weight"
            icon={GrowthIcon}
            color="#7b1fa2"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Upcoming Harvests"
            value={data?.upcoming_harvests || 0}
            subtitle="Ready for harvest"
            icon={HarvestIcon}
            color="#f57c00"
            onClick={() => navigate('/biofloc/harvests')}
          />
        </Grid>

        {/* Tank Utilization */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tank Utilization
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={tankUtilization}
                    sx={{
                      height: 10,
                      borderRadius: 5,
                      backgroundColor: '#e0e0e0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: tankUtilization > 80 ? '#f44336' : tankUtilization > 60 ? '#ff9800' : '#4caf50',
                      },
                    }}
                  />
                </Box>
                <Typography variant="h6" fontWeight="bold">
                  {safeToFixed(tankUtilization, 0)}%
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">In Use</Typography>
                  <Typography variant="h6">{data?.active_tanks || 0}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Available</Typography>
                  <Typography variant="h6">{data?.available_tanks || 0}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Maintenance</Typography>
                  <Typography variant="h6">{data?.maintenance_tanks || 0}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity (7 days)
              </Typography>
              <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Mortalities</Typography>
                  <Chip
                    label={data?.recent_mortalities_7d || 0}
                    size="small"
                    color={data?.recent_mortalities_7d > 100 ? 'error' : 'default'}
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Water Tests</Typography>
                  <Chip label="Check" size="small" color="primary" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Feeding Sessions</Typography>
                  <Chip label="Active" size="small" color="success" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Water Quality Alerts */}
        <Grid item xs={12} md={4}>
          <AlertCard
            title="Low Dissolved Oxygen"
            count={data?.low_do_alerts || 0}
            severity="error"
            icon={WaterIcon}
          />
        </Grid>

        <Grid item xs={12} md={4}>
          <AlertCard
            title="High Ammonia Levels"
            count={data?.high_ammonia_alerts || 0}
            severity="warning"
            icon={WarningIcon}
          />
        </Grid>

        <Grid item xs={12} md={4}>
          <AlertCard
            title="Upcoming Harvests"
            count={data?.upcoming_harvests || 0}
            severity="success"
            icon={HarvestIcon}
          />
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/biofloc/feeding/new')}
                >
                  Record Feeding
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/biofloc/sampling/new')}
                >
                  Record Sampling
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/biofloc/water-tests/new')}
                >
                  Water Test
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/biofloc/mortality/new')}
                >
                  Record Mortality
                </Button>
                <Button
                  variant="outlined"
                  color="secondary"
                  onClick={() => navigate('/biofloc/harvests/new')}
                >
                  Record Harvest
                </Button>
                <Button
                  variant="outlined"
                  color="info"
                  onClick={() => navigate('/biofloc/reports')}
                >
                  View Reports
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

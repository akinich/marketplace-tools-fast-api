/**
 * ============================================================================
 * Biofloc Batch Detail Page
 * ============================================================================
 * Version: 1.0.0
 * Created: 2025-11-19
 *
 * Comprehensive batch detail view showing:
 * - Current batch metrics
 * - Performance indicators (FCR, SGR, survival rate)
 * - Growth curve
 * - Feeding history
 * - Sampling records
 * - Mortality events
 * - Harvest records
 * - Cost breakdown
 * - Parent/child batch relationships (for graded batches)
 * ============================================================================
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  TrendingUp as GrowthIcon,
  ShowChart as ChartIcon,
  Restaurant as FeedIcon,
  Science as SamplingIcon,
  Warning as MortalityIcon,
  ShoppingCart as HarvestIcon,
  MonetizationOn as CostIcon,
  CompareArrows as TransferIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';

export default function BioflocBatchDetail() {
  const { batchId } = useParams();
  const navigate = useNavigate();

  // Fetch batch data
  const { data: batch, isLoading: batchLoading, error: batchError } = useQuery(
    ['bioflocBatch', batchId],
    () => bioflocAPI.getBatch(batchId)
  );

  // Fetch performance data
  const { data: performance, isLoading: perfLoading } = useQuery(
    ['bioflocBatchPerformance', batchId],
    () => bioflocAPI.getBatchPerformance(batchId),
    {
      enabled: !!batchId,
      retry: false,
      onError: (error) => {
        console.log('Performance data not available:', error);
      }
    }
  );

  if (batchLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (batchError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load batch details: {batchError.message}
        </Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/biofloc/batches')} sx={{ mt: 2 }}>
          Back to Batches
        </Button>
      </Box>
    );
  }

  if (!batch) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">Batch not found</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/biofloc/batches')} sx={{ mt: 2 }}>
          Back to Batches
        </Button>
      </Box>
    );
  }

  const getStatusColor = (status) => {
    const colors = {
      active: 'success',
      transferred: 'info',
      harvested: 'default',
      graded: 'warning',
    };
    return colors[status] || 'default';
  };

  const biomassGain = batch.current_total_biomass_kg - batch.initial_total_biomass_kg;
  const cycleDays = batch.cycle_duration_days || 0;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Button startIcon={<BackIcon />} onClick={() => navigate('/biofloc/batches')} sx={{ mb: 1 }}>
            Back to Batches
          </Button>
          <Typography variant="h4" fontWeight="bold">
            {batch.batch_code}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
            <Chip label={batch.status} color={getStatusColor(batch.status)} size="small" />
            <Chip label={batch.species} variant="outlined" size="small" />
            {batch.parent_batch_code && (
              <Chip
                label={`Child of ${batch.parent_batch_code}`}
                color="warning"
                size="small"
                icon={<TransferIcon />}
              />
            )}
          </Box>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary">
            Stocked: {new Date(batch.stocking_date).toLocaleDateString()}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            Cycle: {cycleDays} days
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Current Metrics */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                <GrowthIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                Current Metrics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">
                    Current Population
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {batch.current_count?.toLocaleString() || 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    fish
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">
                    Avg Weight
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {batch.current_avg_weight_g || 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    grams
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">
                    Total Biomass
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {batch.current_total_biomass_kg?.toFixed(2) || 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    kg
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">
                    Current Tank
                  </Typography>
                  <Typography variant="h6" fontWeight="bold">
                    {batch.current_tank_code || 'N/A'}
                  </Typography>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">
                    Initial Count
                  </Typography>
                  <Typography variant="body1">
                    {batch.initial_count?.toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">
                    Initial Weight
                  </Typography>
                  <Typography variant="body1">
                    {batch.initial_avg_weight_g}g
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">
                    Source
                  </Typography>
                  <Typography variant="body1">
                    {batch.source || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">
                    Biomass Gain
                  </Typography>
                  <Typography variant="body1" color={biomassGain > 0 ? 'success.main' : 'text.primary'}>
                    {biomassGain > 0 ? '+' : ''}{biomassGain.toFixed(2)} kg
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Indicators */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                <ChartIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                Performance
              </Typography>

              {/* Survival Rate */}
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="caption">Survival Rate</Typography>
                  <Typography variant="caption" fontWeight="bold">
                    {batch.survival_rate?.toFixed(1) || 0}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={batch.survival_rate || 0}
                  color={batch.survival_rate >= 90 ? 'success' : batch.survival_rate >= 80 ? 'warning' : 'error'}
                />
              </Box>

              {/* FCR */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  FCR (Feed Conversion Ratio)
                </Typography>
                <Typography variant="h5" fontWeight="bold" color={batch.fcr <= 1.5 ? 'success.main' : 'text.primary'}>
                  {batch.fcr?.toFixed(2) || 'N/A'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {batch.fcr <= 1.5 ? 'Excellent' : batch.fcr <= 2.0 ? 'Good' : 'Needs improvement'}
                </Typography>
              </Box>

              {/* SGR */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  SGR (Specific Growth Rate)
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {batch.sgr?.toFixed(2) || 'N/A'}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  per day
                </Typography>
              </Box>

              {/* Total Feed */}
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Total Feed Given
                </Typography>
                <Typography variant="h6" fontWeight="bold">
                  {batch.total_feed_kg?.toFixed(2) || 0} kg
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Report (if available) */}
        {performance && (
          <>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    <CostIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                    Cost & Revenue Analysis
                  </Typography>

                  <Grid container spacing={3}>
                    {/* Costs */}
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                        Cost Breakdown
                      </Typography>
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell>Feed</TableCell>
                            <TableCell align="right">₹{performance.feed_cost?.toFixed(2) || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Fingerlings</TableCell>
                            <TableCell align="right">₹{performance.fingerling_cost?.toFixed(2) || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Chemicals</TableCell>
                            <TableCell align="right">₹{performance.chemical_cost?.toFixed(2) || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Labor</TableCell>
                            <TableCell align="right">₹{performance.labor_cost?.toFixed(2) || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Utilities</TableCell>
                            <TableCell align="right">₹{performance.utilities_cost?.toFixed(2) || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Other</TableCell>
                            <TableCell align="right">₹{performance.other_cost?.toFixed(2) || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Total Cost</strong></TableCell>
                            <TableCell align="right"><strong>₹{performance.total_cost?.toFixed(2) || 0}</strong></TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </Grid>

                    {/* Revenue & Profit */}
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                        Revenue & Profitability
                      </Typography>
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell>Total Revenue</TableCell>
                            <TableCell align="right">₹{performance.total_revenue?.toFixed(2) || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Gross Profit</TableCell>
                            <TableCell align="right" sx={{ color: performance.gross_profit >= 0 ? 'success.main' : 'error.main' }}>
                              ₹{performance.gross_profit?.toFixed(2) || 0}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Cost per kg</TableCell>
                            <TableCell align="right">₹{performance.cost_per_kg?.toFixed(2) || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Profit per kg</TableCell>
                            <TableCell align="right">₹{performance.profit_per_kg?.toFixed(2) || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>ROI</strong></TableCell>
                            <TableCell align="right">
                              <strong style={{ color: performance.roi_percentage >= 0 ? 'green' : 'red' }}>
                                {performance.roi_percentage?.toFixed(1) || 0}%
                              </strong>
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}

        {/* Notes */}
        {batch.notes && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  Notes
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {batch.notes}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Grading Information (if child batch) */}
        {batch.parent_batch_code && (
          <Grid item xs={12}>
            <Card sx={{ bgcolor: 'warning.50' }}>
              <CardContent>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  <TransferIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Grading Information
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" color="text.secondary">
                      Parent Batch
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {batch.parent_batch_code}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" color="text.secondary">
                      Grading Date
                    </Typography>
                    <Typography variant="body1">
                      {batch.grading_date ? new Date(batch.grading_date).toLocaleDateString() : 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" color="text.secondary">
                      Original Stocking Date (Inherited)
                    </Typography>
                    <Typography variant="body1">
                      {new Date(batch.stocking_date).toLocaleDateString()}
                    </Typography>
                  </Grid>
                </Grid>
                <Alert severity="info" sx={{ mt: 2 }}>
                  This batch was created from grading. Feed costs were proportionally allocated from parent batch based on biomass at grading.
                </Alert>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<FeedIcon />}
                onClick={() => navigate('/biofloc/feeding')}
              >
                Record Feeding
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={<SamplingIcon />}
                onClick={() => navigate('/biofloc/sampling')}
              >
                Record Sampling
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={<MortalityIcon />}
                onClick={() => navigate('/biofloc/mortality')}
              >
                Record Mortality
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={<HarvestIcon />}
                onClick={() => navigate('/biofloc/harvests')}
              >
                Record Harvest
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={<TransferIcon />}
                onClick={() => navigate('/biofloc/transfer')}
              >
                Transfer/Grade
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

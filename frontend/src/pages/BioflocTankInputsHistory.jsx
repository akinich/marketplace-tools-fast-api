/**
 * ============================================================================
 * Biofloc Tank Inputs History Page
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 *
 * Displays history of all tank inputs (chemicals, probiotics, etc.) with filtering.
 * ============================================================================
 */

import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Grid,
  TextField,
  Autocomplete,
  Chip,
  Paper,
} from '@mui/material';
import { Science as InputIcon } from '@mui/icons-material';

import { bioflocAPI } from '../api';

const INPUT_TYPE_COLORS = {
  chemical: 'error',
  probiotic: 'success',
  carbon_source: 'warning',
  mineral: 'info',
  other: 'default',
};

export default function BioflocTankInputsHistory() {
  const [filters, setFilters] = useState({
    tank_id: null,
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Last 30 days
    end_date: new Date().toISOString().split('T')[0],
  });

  // Fetch tank inputs
  const { data, isLoading, error } = useQuery(
    ['bioflocTankInputs', filters],
    () => bioflocAPI.getTankInputs({
      tank_id: filters.tank_id,
      start_date: filters.start_date,
      end_date: filters.end_date,
      limit: 200,
    }),
    { keepPreviousData: true }
  );

  // Fetch tanks for filter
  const { data: tanksData } = useQuery('bioflocTanksAll', () =>
    bioflocAPI.getTanks({ limit: 100 })
  );

  const tanks = tanksData?.tanks || [];
  const inputs = data?.tank_inputs || [];

  const handleFilterChange = (field, value) => {
    setFilters({ ...filters, [field]: value });
  };

  // Calculate summary stats
  const summaryStats = inputs.reduce((acc, input) => {
    const type = input.input_type;
    if (!acc[type]) {
      acc[type] = { count: 0, totalCost: 0 };
    }
    acc[type].count++;
    if (input.total_cost) {
      acc[type].totalCost += parseFloat(input.total_cost);
    }
    return acc;
  }, {});

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load tank inputs history: {error.message}</Alert>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <InputIcon color="success" />
        <Typography variant="h5" fontWeight="bold">
          Tank Inputs History
        </Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Complete history of all tank inputs (chemicals, probiotics, carbon sources, etc.)
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
            Filters
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Autocomplete
                options={tanks}
                getOptionLabel={(option) => option.tank_code}
                value={tanks.find(t => t.id === filters.tank_id) || null}
                onChange={(e, value) => handleFilterChange('tank_id', value?.id || null)}
                renderInput={(params) => (
                  <TextField {...params} label="Filter by Tank" size="small" />
                )}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Start Date"
                type="date"
                value={filters.start_date}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
                size="small"
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="End Date"
                type="date"
                value={filters.end_date}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
                size="small"
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {Object.keys(summaryStats).length > 0 && (
        <Grid container spacing={2} sx={{ mb: 2 }}>
          {Object.entries(summaryStats).map(([type, stats]) => (
            <Grid item xs={12} sm={6} md={2.4} key={type}>
              <Paper sx={{ p: 2 }}>
                <Chip
                  label={type.replace('_', ' ').toUpperCase()}
                  color={INPUT_TYPE_COLORS[type] || 'default'}
                  size="small"
                  sx={{ mb: 1 }}
                />
                <Typography variant="h6">{stats.count}</Typography>
                <Typography variant="caption" color="text.secondary">
                  applications
                </Typography>
                {stats.totalCost > 0 && (
                  <Typography variant="caption" display="block" color="text.secondary">
                    ₹{stats.totalCost.toFixed(2)}
                  </Typography>
                )}
              </Paper>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Results summary */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="body2">
          Found <strong>{inputs.length}</strong> tank input records
        </Typography>
      </Paper>

      {/* Tank inputs table */}
      <Card>
        <CardContent>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Date/Time</TableCell>
                  <TableCell>Tank</TableCell>
                  <TableCell>Batch</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Item</TableCell>
                  <TableCell align="right">Quantity</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell align="right">Cost</TableCell>
                  <TableCell>Notes</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {inputs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No tank inputs found for the selected filters
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  inputs.map((input) => (
                    <TableRow key={input.id} hover>
                      <TableCell>
                        <Typography variant="caption" display="block">
                          {new Date(input.input_date).toLocaleDateString()}
                        </Typography>
                        {input.input_time && (
                          <Typography variant="caption" color="text.secondary">
                            {input.input_time}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{input.tank_name || '-'}</TableCell>
                      <TableCell>{input.batch_code || '-'}</TableCell>
                      <TableCell>
                        <Chip
                          label={input.input_type.replace('_', ' ')}
                          color={INPUT_TYPE_COLORS[input.input_type] || 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{input.item_name}</Typography>
                        {input.item_sku && (
                          <Typography variant="caption" color="text.secondary">
                            SKU: {input.item_sku}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Typography fontWeight="bold">
                          {input.quantity} {input.unit}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {input.reason || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {input.total_cost ? `₹${parseFloat(input.total_cost).toFixed(2)}` : '-'}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" noWrap sx={{ maxWidth: 150, display: 'block' }}>
                          {input.notes || '-'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}

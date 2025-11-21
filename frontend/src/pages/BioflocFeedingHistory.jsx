/**
 * ============================================================================
 * Biofloc Feeding History Page
 * ============================================================================
 * Version: 1.1.0
 * Last Updated: 2025-11-21
 *
 * Displays history of all feeding sessions with filtering options.
 * ============================================================================
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import { Restaurant as FeedIcon } from '@mui/icons-material';

import { bioflocAPI } from '../api';

export default function BioflocFeedingHistory() {
  const [filters, setFilters] = useState({
    tank_id: null,
    batch_id: null,
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Last 30 days
    end_date: new Date().toISOString().split('T')[0],
  });

  // Fetch feeding sessions
  const { data, isLoading, error } = useQuery(
    ['bioflocFeedingSessions', filters],
    () => bioflocAPI.getFeedingSessions({
      tank_id: filters.tank_id,
      batch_id: filters.batch_id,
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

  // Fetch batches for filter
  const { data: batchesData } = useQuery('bioflocBatchesAll', () =>
    bioflocAPI.getBatches({ limit: 100 })
  );

  const tanks = tanksData?.tanks || [];
  const batches = batchesData?.batches || [];
  const sessions = data?.feedings || [];

  const handleFilterChange = (field, value) => {
    setFilters({ ...filters, [field]: value });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load feeding history: {error.message}</Alert>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <FeedIcon color="primary" />
        <Typography variant="h5" fontWeight="bold">
          Feeding History
        </Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Complete history of all feeding sessions
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
            Filters
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
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
            <Grid item xs={12} md={3}>
              <Autocomplete
                options={batches}
                getOptionLabel={(option) => `${option.batch_code} (${option.species})`}
                value={batches.find(b => b.id === filters.batch_id) || null}
                onChange={(e, value) => handleFilterChange('batch_id', value?.id || null)}
                renderInput={(params) => (
                  <TextField {...params} label="Filter by Batch" size="small" />
                )}
              />
            </Grid>
            <Grid item xs={12} md={3}>
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
            <Grid item xs={12} md={3}>
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

      {/* Results summary */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="body2">
          Found <strong>{sessions.length}</strong> feeding sessions
        </Typography>
      </Paper>

      {/* Feeding sessions table */}
      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Time</TableCell>
                  <TableCell>Session</TableCell>
                  <TableCell>Tank</TableCell>
                  <TableCell>Batch</TableCell>
                  <TableCell>Feed Items</TableCell>
                  <TableCell align="right">Total Feed (kg)</TableCell>
                  <TableCell>Notes</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sessions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No feeding sessions found for the selected filters
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  sessions.map((session) => (
                    <TableRow key={session.id} hover>
                      <TableCell>{new Date(session.feeding_date).toLocaleDateString()}</TableCell>
                      <TableCell>{session.feed_time}</TableCell>
                      <TableCell>
                        <Chip label={`#${session.session_number}`} size="small" color="primary" variant="outlined" />
                      </TableCell>
                      <TableCell>{session.tank_code}</TableCell>
                      <TableCell>{session.batch_code || '-'}</TableCell>
                      <TableCell>
                        {Array.isArray(session.feed_items) && session.feed_items.length > 0 ? (
                          <Box>
                            {session.feed_items.map((item, idx) => (
                              <Typography key={idx} variant="caption" display="block">
                                • {item.sku}: {item.quantity_kg} kg
                              </Typography>
                            ))}
                          </Box>
                        ) : (
                          <Typography variant="caption">-</Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Typography fontWeight="bold">
                          {session.total_feed_kg || 0}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" noWrap sx={{ maxWidth: 150, display: 'block' }}>
                          {session.notes || '-'}
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

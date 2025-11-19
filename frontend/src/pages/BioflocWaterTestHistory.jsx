/**
 * ============================================================================
 * Biofloc Water Test History Page
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 *
 * Displays history of all water quality tests with filtering options.
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
import { Opacity as WaterIcon, Warning as WarningIcon } from '@mui/icons-material';

import { bioflocAPI } from '../api';

export default function BioflocWaterTestHistory() {
  const [filters, setFilters] = useState({
    tank_id: null,
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Last 30 days
    end_date: new Date().toISOString().split('T')[0],
  });

  // Fetch water tests
  const { data, isLoading, error } = useQuery(
    ['bioflocWaterTests', filters],
    () => bioflocAPI.getWaterTests({
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
  const tests = data?.water_tests || [];

  const handleFilterChange = (field, value) => {
    setFilters({ ...filters, [field]: value });
  };

  // Helper to determine if parameter is within acceptable range
  const isParameterOk = (param, value) => {
    if (!value) return null;
    const ranges = {
      dissolved_oxygen_mgl: { min: 5, max: 100 }, // Below 5 is concerning
      ph: { min: 6.5, max: 8.5 },
      ammonia_nh3_mgl: { min: 0, max: 0.5 }, // Above 0.5 is concerning
      nitrite_no2_mgl: { min: 0, max: 1 }, // Above 1 is concerning
    };

    if (!ranges[param]) return null;
    const val = parseFloat(value);
    if (val < ranges[param].min || val > ranges[param].max) {
      return 'warning';
    }
    return 'ok';
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load water test history: {error.message}</Alert>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <WaterIcon color="info" />
        <Typography variant="h5" fontWeight="bold">
          Water Test History
        </Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Complete history of all water quality tests
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

      {/* Results summary */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="body2">
          Found <strong>{tests.length}</strong> water quality tests
        </Typography>
      </Paper>

      {/* Water tests table */}
      <Card>
        <CardContent>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Date/Time</TableCell>
                  <TableCell>Tank</TableCell>
                  <TableCell>Batch</TableCell>
                  <TableCell>Temp (°C)</TableCell>
                  <TableCell>pH</TableCell>
                  <TableCell>DO (mg/L)</TableCell>
                  <TableCell>NH3 (mg/L)</TableCell>
                  <TableCell>NO2 (mg/L)</TableCell>
                  <TableCell>NO3 (mg/L)</TableCell>
                  <TableCell>Floc Vol</TableCell>
                  <TableCell>Notes</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tests.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={11} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No water tests found for the selected filters
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  tests.map((test) => {
                    const doStatus = isParameterOk('dissolved_oxygen_mgl', test.dissolved_oxygen_mgl);
                    const phStatus = isParameterOk('ph', test.ph);
                    const nh3Status = isParameterOk('ammonia_nh3_mgl', test.ammonia_nh3_mgl);
                    const no2Status = isParameterOk('nitrite_no2_mgl', test.nitrite_no2_mgl);

                    return (
                      <TableRow key={test.id} hover>
                        <TableCell>
                          <Typography variant="caption" display="block">
                            {new Date(test.test_date).toLocaleDateString()}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {test.test_time}
                          </Typography>
                        </TableCell>
                        <TableCell>{test.tank_code}</TableCell>
                        <TableCell>{test.batch_code || '-'}</TableCell>
                        <TableCell>
                          {test.temperature_c ? `${test.temperature_c}°C` : '-'}
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            {test.ph || '-'}
                            {phStatus === 'warning' && <WarningIcon fontSize="small" color="warning" />}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            {test.dissolved_oxygen_mgl || '-'}
                            {doStatus === 'warning' && <WarningIcon fontSize="small" color="error" />}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            {test.ammonia_nh3_mgl || '-'}
                            {nh3Status === 'warning' && <WarningIcon fontSize="small" color="error" />}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            {test.nitrite_no2_mgl || '-'}
                            {no2Status === 'warning' && <WarningIcon fontSize="small" color="warning" />}
                          </Box>
                        </TableCell>
                        <TableCell>{test.nitrate_no3_mgl || '-'}</TableCell>
                        <TableCell>
                          {test.floc_volume_mll ? `${test.floc_volume_mll} ml/L` : '-'}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" noWrap sx={{ maxWidth: 100, display: 'block' }}>
                            {test.notes || '-'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Legend */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="caption" fontWeight="bold" gutterBottom>
          Alert Indicators:
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
          <Typography variant="caption">
            <WarningIcon fontSize="small" color="error" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
            DO &lt; 5 mg/L or NH3 &gt; 0.5 mg/L (Critical)
          </Typography>
          <Typography variant="caption">
            <WarningIcon fontSize="small" color="warning" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
            pH outside 6.5-8.5 or NO2 &gt; 1 mg/L (Warning)
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
}

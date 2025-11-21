/**
 * ============================================================================
 * Biofloc Operational Forms - Mortality (Multi-Batch Support)
 * ============================================================================
 * Version: 2.1.0
 * Last Updated: 2025-11-21
 *
 * Form for recording mortality events with multi-batch tank support.
 *
 * CHANGES in v2.0.0:
 * - Tank-based selection (instead of batch-based)
 * - Multi-batch support with allocation modes:
 *   - Auto-split: Proportional allocation by population
 *   - Manual split: User specifies mortality per batch
 * ============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  Autocomplete,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormLabel,
  Paper,
  Divider,
} from '@mui/material';
import { Save as SaveIcon, Warning as WarningIcon } from '@mui/icons-material';

import { bioflocAPI } from '../api';

const MORTALITY_CAUSES = [
  'disease',
  'stress',
  'unknown',
  'predation',
  'handling',
  'water_quality',
  'starvation',
  'other',
];

export default function MortalityForm({ onSuccess }) {
  const queryClient = useQueryClient();
  const [tank, setTank] = useState(null);
  const [tankBatches, setTankBatches] = useState([]);
  const [allocationMode, setAllocationMode] = useState('auto'); // 'auto' or 'manual'

  const [formData, setFormData] = useState({
    mortality_date: new Date().toISOString().split('T')[0],
    total_count: '',
    cause: '',
    avg_weight_g: '',
    notes: '',
  });

  // Manual allocation: array of {batch_id, count}
  const [manualAllocations, setManualAllocations] = useState([]);

  // Fetch tanks
  const { data: tanksData, isLoading: tanksLoading } = useQuery(
    'bioflocTanksAll',
    () => bioflocAPI.getTanks({ limit: 100 })
  );

  // Fetch batches when tank changes
  useEffect(() => {
    if (tank?.id) {
      // Fetch batch assignments for this tank
      bioflocAPI.getBatches({ limit: 100 }).then(response => {
        const batchesInTank = response.batches.filter(b =>
          b.current_tank_id === tank.id && b.status === 'active'
        );
        setTankBatches(batchesInTank);

        // Initialize manual allocations
        setManualAllocations(
          batchesInTank.map(b => ({ batch_id: b.id, batch_code: b.batch_code, count: '' }))
        );
      });
    } else {
      setTankBatches([]);
      setManualAllocations([]);
    }
  }, [tank]);

  const tanks = tanksData?.tanks || [];

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleTankChange = (event, value) => {
    setTank(value);
  };

  const handleManualAllocationChange = (batchId, value) => {
    setManualAllocations(prev =>
      prev.map(a => a.batch_id === batchId ? { ...a, count: value } : a)
    );
  };

  // Calculate auto-split allocations
  const getAutoAllocations = () => {
    if (!formData.total_count || tankBatches.length === 0) return [];

    const totalCount = parseInt(formData.total_count);
    const totalPopulation = tankBatches.reduce((sum, b) => sum + (b.current_count || 0), 0);

    if (totalPopulation === 0) return [];

    return tankBatches.map(batch => ({
      batch_id: batch.id,
      batch_code: batch.batch_code,
      count: Math.round((batch.current_count / totalPopulation) * totalCount),
      current_count: batch.current_count,
    }));
  };

  // Validate manual allocations
  const validateManualAllocations = () => {
    const totalAllocated = manualAllocations.reduce((sum, a) => sum + (parseInt(a.count) || 0), 0);
    return totalAllocated === parseInt(formData.total_count);
  };

  const handleSubmit = async () => {
    if (!tank) {
      alert('Please select a tank');
      return;
    }

    if (!formData.total_count || parseInt(formData.total_count) <= 0) {
      alert('Please enter total mortality count');
      return;
    }

    if (tankBatches.length === 0) {
      alert('No active batches in this tank');
      return;
    }

    // Determine allocations
    let allocations = [];
    if (allocationMode === 'auto') {
      allocations = getAutoAllocations();
    } else {
      // Manual mode
      if (!validateManualAllocations()) {
        alert(`Total allocated (${manualAllocations.reduce((sum, a) => sum + (parseInt(a.count) || 0), 0)}) must equal total mortality (${formData.total_count})`);
        return;
      }
      allocations = manualAllocations
        .filter(a => parseInt(a.count) > 0)
        .map(a => {
          const batch = tankBatches.find(b => b.id === a.batch_id);
          return {
            batch_id: a.batch_id,
            batch_code: a.batch_code,
            count: parseInt(a.count),
            current_count: batch?.current_count,
          };
        });
    }

    // Submit mortality for each batch
    try {
      for (const allocation of allocations) {
        const payload = {
          batch_id: allocation.batch_id,
          tank_id: tank.id,
          mortality_date: formData.mortality_date,
          count: allocation.count,
        };

        if (formData.cause) payload.cause = formData.cause;
        if (formData.avg_weight_g) payload.avg_weight_g = parseFloat(formData.avg_weight_g);
        if (formData.notes) payload.notes = formData.notes;

        await bioflocAPI.recordMortality(payload);
      }

      // Success
      queryClient.invalidateQueries('bioflocMortalities');
      queryClient.invalidateQueries('bioflocBatches');
      queryClient.invalidateQueries('bioflocDashboard');
      if (onSuccess) onSuccess();

      // Reset form
      setTank(null);
      setTankBatches([]);
      setFormData({
        mortality_date: new Date().toISOString().split('T')[0],
        total_count: '',
        cause: '',
        avg_weight_g: '',
        notes: '',
      });
      alert('Mortality recorded successfully for all batches');
    } catch (error) {
      alert('Failed to record mortality: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (tanksLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const autoAllocations = allocationMode === 'auto' ? getAutoAllocations() : [];
  const totalPopulation = tankBatches.reduce((sum, b) => sum + (b.current_count || 0), 0);

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <WarningIcon color="warning" />
          <Typography variant="h6" fontWeight="bold">
            Record Mortality Event
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Record fish deaths. Supports tanks with multiple batches.
        </Typography>

        <Grid container spacing={2}>
          {/* Tank Selection */}
          <Grid item xs={12}>
            <Autocomplete
              options={tanks}
              getOptionLabel={(option) =>
                `${option.tank_code} - ${option.batch_code || 'No batch'} (${option.status})`
              }
              value={tank}
              onChange={handleTankChange}
              renderInput={(params) => (
                <TextField {...params} label="Select Tank" required />
              )}
            />
          </Grid>

          {/* Show tank batches info */}
          {tankBatches.length > 0 && (
            <Grid item xs={12}>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'info.50' }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  Tank Contains {tankBatches.length} Batch(es):
                </Typography>
                {tankBatches.map((batch, idx) => (
                  <Typography key={batch.id} variant="body2">
                    • {batch.batch_code}: {batch.current_count?.toLocaleString()} fish @ {batch.current_avg_weight_g}g avg
                  </Typography>
                ))}
                <Typography variant="body2" fontWeight="bold" sx={{ mt: 1 }}>
                  Total: {totalPopulation.toLocaleString()} fish
                </Typography>
              </Paper>
            </Grid>
          )}

          {tankBatches.length === 0 && tank && (
            <Grid item xs={12}>
              <Alert severity="warning">
                No active batches in this tank. Please select a different tank.
              </Alert>
            </Grid>
          )}

          {tankBatches.length > 0 && (
            <>
              <Grid item xs={12}>
                <Divider />
              </Grid>

              {/* Mortality Date */}
              <Grid item xs={12} md={6}>
                <TextField
                  label="Mortality Date"
                  type="date"
                  value={formData.mortality_date}
                  onChange={handleChange('mortality_date')}
                  required
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              {/* Total Count */}
              <Grid item xs={12} md={6}>
                <TextField
                  label="Total Fish Died *"
                  type="number"
                  value={formData.total_count}
                  onChange={handleChange('total_count')}
                  required
                  fullWidth
                  inputProps={{ min: 1, max: totalPopulation }}
                  error={formData.total_count && parseInt(formData.total_count) > totalPopulation}
                  helperText={
                    formData.total_count && parseInt(formData.total_count) > totalPopulation
                      ? `Exceeds tank population (${totalPopulation})`
                      : ""
                  }
                />
              </Grid>

              {/* Allocation Mode (only if multiple batches) */}
              {tankBatches.length > 1 && (
                <>
                  <Grid item xs={12}>
                    <Divider sx={{ my: 1 }} />
                    <FormControl component="fieldset">
                      <FormLabel component="legend">
                        How to allocate mortality across {tankBatches.length} batches?
                      </FormLabel>
                      <RadioGroup
                        value={allocationMode}
                        onChange={(e) => setAllocationMode(e.target.value)}
                        row
                      >
                        <FormControlLabel
                          value="auto"
                          control={<Radio />}
                          label="Auto-split (proportional by population)"
                        />
                        <FormControlLabel
                          value="manual"
                          control={<Radio />}
                          label="Manual split (I know which batch died)"
                        />
                      </RadioGroup>
                    </FormControl>
                  </Grid>

                  {/* Show allocation preview */}
                  <Grid item xs={12}>
                    {allocationMode === 'auto' && formData.total_count && (
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                          Auto-Split Preview:
                        </Typography>
                        {autoAllocations.map((alloc, idx) => (
                          <Typography key={idx} variant="body2">
                            • {alloc.batch_code}: {alloc.count} fish ({((alloc.count / parseInt(formData.total_count)) * 100).toFixed(1)}%)
                          </Typography>
                        ))}
                      </Paper>
                    )}

                    {allocationMode === 'manual' && (
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                          Manual Allocation (Total must = {formData.total_count || 0}):
                        </Typography>
                        <Grid container spacing={2} sx={{ mt: 1 }}>
                          {manualAllocations.map((alloc, idx) => (
                            <Grid item xs={12} md={6} key={alloc.batch_id}>
                              <TextField
                                label={`${alloc.batch_code} - Deaths`}
                                type="number"
                                value={alloc.count}
                                onChange={(e) => handleManualAllocationChange(alloc.batch_id, e.target.value)}
                                fullWidth
                                size="small"
                                inputProps={{ min: 0 }}
                              />
                            </Grid>
                          ))}
                        </Grid>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          Total allocated: {manualAllocations.reduce((sum, a) => sum + (parseInt(a.count) || 0), 0)} / {formData.total_count || 0}
                        </Typography>
                      </Paper>
                    )}
                  </Grid>
                </>
              )}

              <Grid item xs={12}>
                <Divider />
              </Grid>

              {/* Cause */}
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Cause of Death</InputLabel>
                  <Select
                    value={formData.cause}
                    onChange={handleChange('cause')}
                    label="Cause of Death"
                  >
                    <MenuItem value="">Unknown</MenuItem>
                    {MORTALITY_CAUSES.map((cause) => (
                      <MenuItem key={cause} value={cause}>
                        {cause.replace('_', ' ').toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Average Weight */}
              <Grid item xs={12} md={6}>
                <TextField
                  label="Average Weight (grams)"
                  type="number"
                  value={formData.avg_weight_g}
                  onChange={handleChange('avg_weight_g')}
                  fullWidth
                  inputProps={{ step: "0.01" }}
                  helperText="Optional: for biomass loss calculation"
                />
              </Grid>

              {/* Notes */}
              <Grid item xs={12}>
                <TextField
                  label="Notes"
                  value={formData.notes}
                  onChange={handleChange('notes')}
                  multiline
                  rows={3}
                  fullWidth
                  placeholder="Describe symptoms, circumstances, or any relevant observations"
                />
              </Grid>

              {/* Submit Button */}
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  fullWidth
                  size="large"
                  color="warning"
                  startIcon={<SaveIcon />}
                  onClick={handleSubmit}
                  disabled={!formData.total_count || tankBatches.length === 0}
                >
                  Record Mortality
                </Button>
              </Grid>
            </>
          )}
        </Grid>
      </CardContent>
    </Card>
  );
}

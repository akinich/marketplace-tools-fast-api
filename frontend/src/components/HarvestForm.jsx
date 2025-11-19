/**
 * ============================================================================
 * Biofloc Operational Forms - Harvest (Multi-Batch Support)
 * ============================================================================
 * Version: 2.0.0
 * Last Updated: 2025-11-19
 *
 * Form for recording harvest operations with multi-batch tank support.
 *
 * CHANGES in v2.0.0:
 * - Tank-based selection (instead of batch-based)
 * - Multi-batch support with allocation modes:
 *   - Smart allocation: Based on harvested avg weight matching
 *   - Auto-split: Proportional allocation by population
 * ============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';
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
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormLabel,
} from '@mui/material';
import {
  Save as SaveIcon,
  LocalShipping as HarvestIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';

export default function HarvestForm({ onSuccess }) {
  const queryClient = useQueryClient();
  const [tank, setTank] = useState(null);
  const [tankBatches, setTankBatches] = useState([]);
  const [allocationMode, setAllocationMode] = useState('smart'); // 'smart' or 'auto'

  const [formData, setFormData] = useState({
    harvest_date: new Date().toISOString().split('T')[0],
    harvest_type: 'partial',
    total_fish_count: '',
    total_weight_kg: '',
    buyer_name: '',
    price_per_kg: '',
    notes: '',
  });

  // Manual allocation: array of {batch_id, fish_count}
  const [manualAllocations, setManualAllocations] = useState([]);

  // Fetch tanks
  const { data: tanksData, isLoading: tanksLoading } = useQuery(
    'bioflocTanksAll',
    () => bioflocAPI.getTanks({ limit: 100 })
  );

  // Fetch batches when tank changes
  useEffect(() => {
    if (tank?.id) {
      bioflocAPI.getBatches({ limit: 100 }).then(response => {
        const batchesInTank = response.batches.filter(b =>
          b.current_tank_id === tank.id && b.status === 'active'
        );
        setTankBatches(batchesInTank);

        // Initialize manual allocations
        setManualAllocations(
          batchesInTank.map(b => ({
            batch_id: b.id,
            batch_code: b.batch_code,
            avg_weight: b.current_avg_weight_g,
            fish_count: ''
          }))
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
      prev.map(a => a.batch_id === batchId ? { ...a, fish_count: value } : a)
    );
  };

  // Calculate harvested average weight
  const harvestedAvgWeight = formData.total_fish_count && formData.total_weight_kg
    ? ((parseFloat(formData.total_weight_kg) * 1000) / parseInt(formData.total_fish_count))
    : null;

  // Calculate smart allocation based on weight matching
  const getSmartAllocations = () => {
    if (!formData.total_fish_count || !harvestedAvgWeight || tankBatches.length === 0) return [];

    // Find batch with closest average weight
    const batchesWithDistance = tankBatches.map(batch => ({
      ...batch,
      weightDistance: Math.abs((batch.current_avg_weight_g || 0) - harvestedAvgWeight)
    }));

    // Sort by closest weight
    batchesWithDistance.sort((a, b) => a.weightDistance - b.weightDistance);

    // Allocate most to closest batch, some to others
    const totalCount = parseInt(formData.total_fish_count);

    // Suggest: 90% from closest, 10% distributed to others
    const allocations = batchesWithDistance.map((batch, idx) => {
      let suggested = 0;
      if (idx === 0) {
        // Closest batch gets majority
        suggested = Math.round(totalCount * 0.9);
      } else {
        // Others split remaining 10%
        suggested = Math.round((totalCount * 0.1) / (batchesWithDistance.length - 1));
      }

      return {
        batch_id: batch.id,
        batch_code: batch.batch_code,
        fish_count: suggested,
        avg_weight: batch.current_avg_weight_g,
        current_count: batch.current_count,
      };
    });

    // Adjust to exact total
    const currentTotal = allocations.reduce((sum, a) => sum + a.fish_count, 0);
    if (currentTotal !== totalCount) {
      allocations[0].fish_count += (totalCount - currentTotal);
    }

    return allocations;
  };

  // Calculate auto-split allocations
  const getAutoAllocations = () => {
    if (!formData.total_fish_count || tankBatches.length === 0) return [];

    const totalCount = parseInt(formData.total_fish_count);
    const totalPopulation = tankBatches.reduce((sum, b) => sum + (b.current_count || 0), 0);

    if (totalPopulation === 0) return [];

    return tankBatches.map(batch => ({
      batch_id: batch.id,
      batch_code: batch.batch_code,
      fish_count: Math.round((batch.current_count / totalPopulation) * totalCount),
      current_count: batch.current_count,
      avg_weight: batch.current_avg_weight_g,
    }));
  };

  // Validate manual allocations
  const validateManualAllocations = () => {
    const totalAllocated = manualAllocations.reduce((sum, a) => sum + (parseInt(a.fish_count) || 0), 0);
    return totalAllocated === parseInt(formData.total_fish_count);
  };

  const handleSubmit = async () => {
    if (!tank) {
      alert('Please select a tank');
      return;
    }

    if (!formData.total_fish_count || !formData.total_weight_kg) {
      alert('Please enter total fish count and weight');
      return;
    }

    if (tankBatches.length === 0) {
      alert('No active batches in this tank');
      return;
    }

    // Determine allocations
    let allocations = [];
    if (tankBatches.length === 1) {
      // Single batch - simple
      allocations = [{
        batch_id: tankBatches[0].id,
        batch_code: tankBatches[0].batch_code,
        fish_count: parseInt(formData.total_fish_count),
      }];
    } else {
      // Multi-batch
      if (allocationMode === 'smart') {
        allocations = manualAllocations
          .filter(a => parseInt(a.fish_count) > 0)
          .map(a => ({
            batch_id: a.batch_id,
            batch_code: a.batch_code,
            fish_count: parseInt(a.fish_count),
          }));

        if (!validateManualAllocations()) {
          alert(`Total allocated (${manualAllocations.reduce((sum, a) => sum + (parseInt(a.fish_count) || 0), 0)}) must equal total harvest (${formData.total_fish_count})`);
          return;
        }
      } else {
        // Auto mode
        allocations = getAutoAllocations();
      }
    }

    // Submit harvest for each batch
    try {
      for (const allocation of allocations) {
        // Calculate weight for this batch proportionally
        const batchWeight = (allocation.fish_count / parseInt(formData.total_fish_count)) * parseFloat(formData.total_weight_kg);

        const payload = {
          batch_id: allocation.batch_id,
          tank_id: tank.id,
          harvest_date: formData.harvest_date,
          harvest_type: formData.harvest_type,
          fish_count: allocation.fish_count,
          total_weight_kg: batchWeight,
        };

        if (formData.buyer_name) payload.buyer_name = formData.buyer_name;
        if (formData.price_per_kg) payload.price_per_kg = parseFloat(formData.price_per_kg);
        if (formData.notes) payload.notes = formData.notes;

        await bioflocAPI.recordHarvest(payload);
      }

      // Success
      queryClient.invalidateQueries('bioflocHarvests');
      queryClient.invalidateQueries('bioflocBatches');
      queryClient.invalidateQueries('bioflocDashboard');
      if (onSuccess) onSuccess();

      // Reset form
      setTank(null);
      setTankBatches([]);
      setFormData({
        harvest_date: new Date().toISOString().split('T')[0],
        harvest_type: 'partial',
        total_fish_count: '',
        total_weight_kg: '',
        buyer_name: '',
        price_per_kg: '',
        notes: '',
      });
      alert('Harvest recorded successfully for all batches');
    } catch (error) {
      alert('Failed to record harvest: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Sync manual allocations with smart suggestions when mode or data changes
  useEffect(() => {
    if (allocationMode === 'smart' && tankBatches.length > 1) {
      const smart = getSmartAllocations();
      setManualAllocations(prev =>
        prev.map(a => {
          const smartAlloc = smart.find(s => s.batch_id === a.batch_id);
          return smartAlloc ? { ...a, fish_count: smartAlloc.fish_count } : a;
        })
      );
    }
  }, [allocationMode, formData.total_fish_count, formData.total_weight_kg]);

  if (tanksLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const autoAllocations = allocationMode === 'auto' ? getAutoAllocations() : [];
  const smartAllocations = allocationMode === 'smart' ? manualAllocations.filter(a => a.fish_count > 0) : [];
  const totalPopulation = tankBatches.reduce((sum, b) => sum + (b.current_count || 0), 0);

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <HarvestIcon color="secondary" />
          <Typography variant="h6" fontWeight="bold">
            Record Harvest
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Record harvest from tank. Supports tanks with multiple batches.
        </Typography>

        {formData.harvest_type === 'complete' && (
          <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2 }}>
            Complete harvest will finalize the batch and calculate final performance metrics (FCR, SGR, cost/kg).
          </Alert>
        )}

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
                {tankBatches.map((batch) => (
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

              {/* Harvest Date & Type */}
              <Grid item xs={12} md={6}>
                <TextField
                  label="Harvest Date"
                  type="date"
                  value={formData.harvest_date}
                  onChange={handleChange('harvest_date')}
                  required
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>Harvest Type</InputLabel>
                  <Select
                    value={formData.harvest_type}
                    onChange={handleChange('harvest_type')}
                    label="Harvest Type"
                  >
                    <MenuItem value="partial">Partial Harvest</MenuItem>
                    <MenuItem value="complete">Complete Harvest (Finalize Batch)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Total Count & Weight */}
              <Grid item xs={12} md={4}>
                <TextField
                  label="Total Fish Count *"
                  type="number"
                  value={formData.total_fish_count}
                  onChange={handleChange('total_fish_count')}
                  required
                  fullWidth
                  inputProps={{ min: 1, max: totalPopulation }}
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <TextField
                  label="Total Weight (kg) *"
                  type="number"
                  value={formData.total_weight_kg}
                  onChange={handleChange('total_weight_kg')}
                  required
                  fullWidth
                  inputProps={{ step: "0.1", min: 0 }}
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <TextField
                  label="Average Weight (g)"
                  value={harvestedAvgWeight ? harvestedAvgWeight.toFixed(1) : ''}
                  fullWidth
                  disabled
                  helperText="Calculated automatically"
                />
              </Grid>

              {/* Allocation Mode (only if multiple batches) */}
              {tankBatches.length > 1 && (
                <>
                  <Grid item xs={12}>
                    <Divider sx={{ my: 1 }} />
                    <FormControl component="fieldset">
                      <FormLabel component="legend">
                        How to allocate harvest across {tankBatches.length} batches?
                      </FormLabel>
                      <RadioGroup
                        value={allocationMode}
                        onChange={(e) => setAllocationMode(e.target.value)}
                        row
                      >
                        <FormControlLabel
                          value="smart"
                          control={<Radio />}
                          label="Smart allocation (based on harvested weight)"
                        />
                        <FormControlLabel
                          value="auto"
                          control={<Radio />}
                          label="Auto-split (proportional by population)"
                        />
                      </RadioGroup>
                    </FormControl>
                  </Grid>

                  {/* Show allocation */}
                  <Grid item xs={12}>
                    {allocationMode === 'smart' && harvestedAvgWeight && (
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                          Smart Allocation (Harvested avg: {harvestedAvgWeight.toFixed(1)}g):
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                          Adjust if needed. Total must = {formData.total_fish_count || 0}
                        </Typography>
                        <Grid container spacing={2}>
                          {manualAllocations.map((alloc, idx) => (
                            <Grid item xs={12} md={6} key={alloc.batch_id}>
                              <TextField
                                label={`${alloc.batch_code} (${alloc.avg_weight}g avg) - Fish Count`}
                                type="number"
                                value={alloc.fish_count}
                                onChange={(e) => handleManualAllocationChange(alloc.batch_id, e.target.value)}
                                fullWidth
                                size="small"
                                inputProps={{ min: 0 }}
                              />
                            </Grid>
                          ))}
                        </Grid>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          Total allocated: {manualAllocations.reduce((sum, a) => sum + (parseInt(a.fish_count) || 0), 0)} / {formData.total_fish_count || 0}
                        </Typography>
                      </Paper>
                    )}

                    {allocationMode === 'auto' && formData.total_fish_count && (
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                          Auto-Split Preview:
                        </Typography>
                        {autoAllocations.map((alloc, idx) => (
                          <Typography key={idx} variant="body2">
                            • {alloc.batch_code}: {alloc.fish_count} fish ({((alloc.fish_count / parseInt(formData.total_fish_count)) * 100).toFixed(1)}%)
                          </Typography>
                        ))}
                      </Paper>
                    )}
                  </Grid>
                </>
              )}

              <Grid item xs={12}>
                <Divider />
              </Grid>

              {/* Buyer & Pricing */}
              <Grid item xs={12} md={6}>
                <TextField
                  label="Buyer Name"
                  value={formData.buyer_name}
                  onChange={handleChange('buyer_name')}
                  fullWidth
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  label="Price per kg (₹)"
                  type="number"
                  value={formData.price_per_kg}
                  onChange={handleChange('price_per_kg')}
                  fullWidth
                  inputProps={{ step: "0.01", min: 0 }}
                />
              </Grid>

              {/* Notes */}
              <Grid item xs={12}>
                <TextField
                  label="Notes"
                  value={formData.notes}
                  onChange={handleChange('notes')}
                  multiline
                  rows={2}
                  fullWidth
                  placeholder="Any observations or remarks"
                />
              </Grid>

              {/* Submit Button */}
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  color="secondary"
                  fullWidth
                  size="large"
                  startIcon={<SaveIcon />}
                  onClick={handleSubmit}
                  disabled={!formData.total_fish_count || !formData.total_weight_kg || tankBatches.length === 0}
                >
                  Record Harvest
                </Button>
              </Grid>
            </>
          )}
        </Grid>
      </CardContent>
    </Card>
  );
}

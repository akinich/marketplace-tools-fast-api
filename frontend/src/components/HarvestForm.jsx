/**
 * ============================================================================
 * Biofloc Operational Forms - Harvest Recording
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-18
 *
 * Form for recording harvest operations (partial or complete).
 * ============================================================================
 */

import React, { useState } from 'react';
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
} from '@mui/material';
import {
  Save as SaveIcon,
  LocalShipping as HarvestIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';

export default function HarvestForm({ onSuccess }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    batch_id: null,
    harvest_date: new Date().toISOString().split('T')[0],
    harvest_type: 'partial',
    fish_count: '',
    total_weight_kg: '',
    buyer_name: '',
    price_per_kg: '',
    // Grading (optional)
    grade_a_count: '',
    grade_a_weight_kg: '',
    grade_b_count: '',
    grade_b_weight_kg: '',
    grade_c_count: '',
    grade_c_weight_kg: '',
    reject_count: '',
    reject_weight_kg: '',
    notes: '',
  });

  // Fetch active batches only
  const { data: batchesData, isLoading: batchesLoading } = useQuery(
    'bioflocBatchesActive',
    () => bioflocAPI.getBatches({ status: 'active', limit: 100 })
  );

  // Submit mutation
  const mutation = useMutation(
    (data) => bioflocAPI.recordHarvest(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bioflocHarvests');
        queryClient.invalidateQueries('bioflocBatches');
        queryClient.invalidateQueries('bioflocDashboard');
        if (onSuccess) onSuccess();
        // Reset form
        setFormData({
          batch_id: null,
          harvest_date: new Date().toISOString().split('T')[0],
          harvest_type: 'partial',
          fish_count: '',
          total_weight_kg: '',
          buyer_name: '',
          price_per_kg: '',
          grade_a_count: '',
          grade_a_weight_kg: '',
          grade_b_count: '',
          grade_b_weight_kg: '',
          grade_c_count: '',
          grade_c_weight_kg: '',
          reject_count: '',
          reject_weight_kg: '',
          notes: '',
        });
      },
    }
  );

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleBatchChange = (event, value) => {
    setFormData({ ...formData, batch_id: value?.id || null });
  };

  const handleSubmit = () => {
    if (!formData.batch_id) {
      alert('Please select a batch');
      return;
    }

    if (!formData.fish_count || !formData.total_weight_kg) {
      alert('Please enter fish count and total weight');
      return;
    }

    // Build payload with only non-empty values
    const payload = {
      batch_id: formData.batch_id,
      harvest_date: formData.harvest_date,
      harvest_type: formData.harvest_type,
      fish_count: parseInt(formData.fish_count),
      total_weight_kg: parseFloat(formData.total_weight_kg),
    };

    // Add optional parameters
    if (formData.buyer_name) payload.buyer_name = formData.buyer_name;
    if (formData.price_per_kg) payload.price_per_kg = parseFloat(formData.price_per_kg);

    // Grading
    if (formData.grade_a_count) payload.grade_a_count = parseInt(formData.grade_a_count);
    if (formData.grade_a_weight_kg) payload.grade_a_weight_kg = parseFloat(formData.grade_a_weight_kg);
    if (formData.grade_b_count) payload.grade_b_count = parseInt(formData.grade_b_count);
    if (formData.grade_b_weight_kg) payload.grade_b_weight_kg = parseFloat(formData.grade_b_weight_kg);
    if (formData.grade_c_count) payload.grade_c_count = parseInt(formData.grade_c_count);
    if (formData.grade_c_weight_kg) payload.grade_c_weight_kg = parseFloat(formData.grade_c_weight_kg);
    if (formData.reject_count) payload.reject_count = parseInt(formData.reject_count);
    if (formData.reject_weight_kg) payload.reject_weight_kg = parseFloat(formData.reject_weight_kg);

    if (formData.notes) payload.notes = formData.notes;

    mutation.mutate(payload);
  };

  const batches = batchesData?.batches || [];
  const avgWeightG = formData.fish_count && formData.total_weight_kg
    ? ((parseFloat(formData.total_weight_kg) * 1000) / parseInt(formData.fish_count)).toFixed(1)
    : null;

  if (batchesLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

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
          Record partial or complete harvest from a batch. Complete harvests will finalize the batch.
        </Typography>

        {mutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to record harvest: {mutation.error.message}
          </Alert>
        )}

        {mutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Harvest recorded successfully!
          </Alert>
        )}

        {formData.harvest_type === 'complete' && (
          <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2 }}>
            Complete harvest will finalize the batch and calculate final performance metrics (FCR, SGR, cost/kg).
          </Alert>
        )}

        <Grid container spacing={2}>
          {/* Batch Selection */}
          <Grid item xs={12}>
            <Autocomplete
              options={batches}
              getOptionLabel={(option) =>
                `${option.batch_code} - ${option.species} (${option.current_count?.toLocaleString()} fish, Tank: ${option.current_tank_code || 'N/A'})`
              }
              onChange={handleBatchChange}
              renderInput={(params) => (
                <TextField {...params} label="Select Batch" required />
              )}
            />
          </Grid>

          {/* Harvest Type & Date */}
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

          {/* Basic Harvest Data */}
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }}>
              <Typography variant="caption" color="text.secondary">
                HARVEST DETAILS
              </Typography>
            </Divider>
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Fish Count"
              type="number"
              value={formData.fish_count}
              onChange={handleChange('fish_count')}
              required
              fullWidth
              inputProps={{ min: 1 }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Total Weight (kg)"
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
              value={avgWeightG || ''}
              fullWidth
              disabled
              helperText="Calculated automatically"
            />
          </Grid>

          {/* Buyer & Pricing */}
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }}>
              <Typography variant="caption" color="text.secondary">
                BUYER & PRICING
              </Typography>
            </Divider>
          </Grid>

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

          {/* Grading (Optional) */}
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }}>
              <Typography variant="caption" color="text.secondary">
                GRADING (OPTIONAL)
              </Typography>
            </Divider>
            <Typography variant="caption" color="text.secondary">
              Break down harvest by grade. Total should match fish count and weight above.
            </Typography>
          </Grid>

          {/* Grade A */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Grade A - Count"
              type="number"
              value={formData.grade_a_count}
              onChange={handleChange('grade_a_count')}
              fullWidth
              inputProps={{ min: 0 }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Grade A - Weight (kg)"
              type="number"
              value={formData.grade_a_weight_kg}
              onChange={handleChange('grade_a_weight_kg')}
              fullWidth
              inputProps={{ step: "0.1", min: 0 }}
            />
          </Grid>

          {/* Grade B */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Grade B - Count"
              type="number"
              value={formData.grade_b_count}
              onChange={handleChange('grade_b_count')}
              fullWidth
              inputProps={{ min: 0 }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Grade B - Weight (kg)"
              type="number"
              value={formData.grade_b_weight_kg}
              onChange={handleChange('grade_b_weight_kg')}
              fullWidth
              inputProps={{ step: "0.1", min: 0 }}
            />
          </Grid>

          {/* Grade C */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Grade C - Count"
              type="number"
              value={formData.grade_c_count}
              onChange={handleChange('grade_c_count')}
              fullWidth
              inputProps={{ min: 0 }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Grade C - Weight (kg)"
              type="number"
              value={formData.grade_c_weight_kg}
              onChange={handleChange('grade_c_weight_kg')}
              fullWidth
              inputProps={{ step: "0.1", min: 0 }}
            />
          </Grid>

          {/* Reject */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Reject - Count"
              type="number"
              value={formData.reject_count}
              onChange={handleChange('reject_count')}
              fullWidth
              inputProps={{ min: 0 }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Reject - Weight (kg)"
              type="number"
              value={formData.reject_weight_kg}
              onChange={handleChange('reject_weight_kg')}
              fullWidth
              inputProps={{ step: "0.1", min: 0 }}
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
              disabled={mutation.isLoading}
            >
              {mutation.isLoading ? 'Recording...' : 'Record Harvest'}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

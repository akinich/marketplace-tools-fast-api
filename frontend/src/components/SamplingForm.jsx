/**
 * ============================================================================
 * Biofloc Operational Forms - Sampling
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-18
 *
 * Form for recording fish sampling and growth measurements.
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
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';

import { bioflocAPI } from '../api';

export default function SamplingForm({ onSuccess }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    batch_id: null,
    tank_id: null,
    sample_date: new Date().toISOString().split('T')[0],
    sample_size: '',
    avg_weight_g: '',
    min_weight_g: '',
    max_weight_g: '',
    std_deviation_g: '',
    avg_length_cm: '',
    min_length_cm: '',
    max_length_cm: '',
    notes: '',
  });

  // Fetch active batches
  const { data: batchesData, isLoading: batchesLoading } = useQuery(
    'bioflocBatchesActive',
    () => bioflocAPI.getBatches({ status: 'active' })
  );

  // Submit mutation
  const mutation = useMutation(
    (data) => bioflocAPI.recordSampling(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bioflocSamplings');
        queryClient.invalidateQueries('bioflocBatches');
        if (onSuccess) onSuccess();
        // Reset form
        setFormData({
          batch_id: null,
          tank_id: null,
          sample_date: new Date().toISOString().split('T')[0],
          sample_size: '',
          avg_weight_g: '',
          min_weight_g: '',
          max_weight_g: '',
          std_deviation_g: '',
          avg_length_cm: '',
          min_length_cm: '',
          max_length_cm: '',
          notes: '',
        });
      },
    }
  );

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleBatchChange = (event, value) => {
    setFormData({
      ...formData,
      batch_id: value?.id || null,
      tank_id: value?.current_tank_id || null,
    });
  };

  const handleSubmit = () => {
    if (!formData.batch_id || !formData.sample_size || !formData.avg_weight_g) {
      alert('Please fill in all required fields');
      return;
    }

    mutation.mutate({
      batch_id: formData.batch_id,
      tank_id: formData.tank_id,
      sample_date: formData.sample_date,
      sample_size: parseInt(formData.sample_size),
      avg_weight_g: parseFloat(formData.avg_weight_g),
      min_weight_g: formData.min_weight_g ? parseFloat(formData.min_weight_g) : undefined,
      max_weight_g: formData.max_weight_g ? parseFloat(formData.max_weight_g) : undefined,
      std_deviation_g: formData.std_deviation_g ? parseFloat(formData.std_deviation_g) : undefined,
      avg_length_cm: formData.avg_length_cm ? parseFloat(formData.avg_length_cm) : undefined,
      min_length_cm: formData.min_length_cm ? parseFloat(formData.min_length_cm) : undefined,
      max_length_cm: formData.max_length_cm ? parseFloat(formData.max_length_cm) : undefined,
      notes: formData.notes || undefined,
    });
  };

  const batches = batchesData?.batches || [];

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
        <Typography variant="h6" gutterBottom fontWeight="bold">
          Record Fish Sampling
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Record growth measurements from fish sampling. This will update the batch's current average weight.
        </Typography>

        {mutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to record sampling: {mutation.error.message}
          </Alert>
        )}

        {mutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Sampling data recorded successfully!
          </Alert>
        )}

        <Grid container spacing={2}>
          {/* Batch Selection */}
          <Grid item xs={12}>
            <Autocomplete
              options={batches}
              getOptionLabel={(option) =>
                `${option.batch_code} - ${option.species} (Tank: ${option.current_tank_name || 'N/A'})`
              }
              onChange={handleBatchChange}
              renderInput={(params) => (
                <TextField {...params} label="Select Batch" required />
              )}
            />
          </Grid>

          {/* Sample Date */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Sample Date"
              type="date"
              value={formData.sample_date}
              onChange={handleChange('sample_date')}
              required
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Sample Size */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Sample Size (number of fish)"
              type="number"
              value={formData.sample_size}
              onChange={handleChange('sample_size')}
              required
              fullWidth
              helperText="How many fish were sampled"
            />
          </Grid>

          {/* Weight Measurements */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 1 }}>
              Weight Measurements (grams)
            </Typography>
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Average Weight *"
              type="number"
              value={formData.avg_weight_g}
              onChange={handleChange('avg_weight_g')}
              required
              fullWidth
              inputProps={{ step: "0.01" }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Minimum Weight"
              type="number"
              value={formData.min_weight_g}
              onChange={handleChange('min_weight_g')}
              fullWidth
              inputProps={{ step: "0.01" }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Maximum Weight"
              type="number"
              value={formData.max_weight_g}
              onChange={handleChange('max_weight_g')}
              fullWidth
              inputProps={{ step: "0.01" }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Standard Deviation"
              type="number"
              value={formData.std_deviation_g}
              onChange={handleChange('std_deviation_g')}
              fullWidth
              inputProps={{ step: "0.01" }}
            />
          </Grid>

          {/* Length Measurements */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 1 }}>
              Length Measurements (cm) - Optional
            </Typography>
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Average Length"
              type="number"
              value={formData.avg_length_cm}
              onChange={handleChange('avg_length_cm')}
              fullWidth
              inputProps={{ step: "0.1" }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Minimum Length"
              type="number"
              value={formData.min_length_cm}
              onChange={handleChange('min_length_cm')}
              fullWidth
              inputProps={{ step: "0.1" }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Maximum Length"
              type="number"
              value={formData.max_length_cm}
              onChange={handleChange('max_length_cm')}
              fullWidth
              inputProps={{ step: "0.1" }}
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
              placeholder="Any observations or notes"
            />
          </Grid>

          {/* Submit Button */}
          <Grid item xs={12}>
            <Button
              variant="contained"
              fullWidth
              size="large"
              startIcon={<SaveIcon />}
              onClick={handleSubmit}
              disabled={mutation.isLoading}
            >
              {mutation.isLoading ? 'Recording...' : 'Record Sampling Data'}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

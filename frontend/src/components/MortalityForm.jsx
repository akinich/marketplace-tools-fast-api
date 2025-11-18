/**
 * ============================================================================
 * Biofloc Operational Forms - Mortality
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-18
 *
 * Form for recording mortality events.
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
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
  const [formData, setFormData] = useState({
    batch_id: null,
    tank_id: null,
    mortality_date: new Date().toISOString().split('T')[0],
    count: '',
    cause: '',
    avg_weight_g: '',
    notes: '',
  });

  // Fetch active batches
  const { data: batchesData, isLoading: batchesLoading } = useQuery(
    'bioflocBatchesActive',
    () => bioflocAPI.getBatches({ status: 'active' })
  );

  // Submit mutation
  const mutation = useMutation(
    (data) => bioflocAPI.recordMortality(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bioflocMortalities');
        queryClient.invalidateQueries('bioflocBatches');
        queryClient.invalidateQueries('bioflocDashboard');
        if (onSuccess) onSuccess();
        // Reset form
        setFormData({
          batch_id: null,
          tank_id: null,
          mortality_date: new Date().toISOString().split('T')[0],
          count: '',
          cause: '',
          avg_weight_g: '',
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
    if (!formData.batch_id || !formData.count) {
      alert('Please fill in all required fields');
      return;
    }

    mutation.mutate({
      batch_id: formData.batch_id,
      tank_id: formData.tank_id,
      mortality_date: formData.mortality_date,
      count: parseInt(formData.count),
      cause: formData.cause || undefined,
      avg_weight_g: formData.avg_weight_g ? parseFloat(formData.avg_weight_g) : undefined,
      notes: formData.notes || undefined,
    });
  };

  const batches = batchesData?.batches || [];
  const selectedBatch = batches.find(b => b.id === formData.batch_id);

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
          <WarningIcon color="warning" />
          <Typography variant="h6" fontWeight="bold">
            Record Mortality Event
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Record fish deaths. This will automatically update the batch's current count and mortality percentage.
        </Typography>

        {mutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to record mortality: {mutation.error.message}
          </Alert>
        )}

        {mutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Mortality event recorded successfully!
          </Alert>
        )}

        <Grid container spacing={2}>
          {/* Batch Selection */}
          <Grid item xs={12}>
            <Autocomplete
              options={batches}
              getOptionLabel={(option) =>
                `${option.batch_code} - ${option.species} (Current: ${option.current_count?.toLocaleString()} fish)`
              }
              onChange={handleBatchChange}
              renderInput={(params) => (
                <TextField {...params} label="Select Batch" required />
              )}
            />
          </Grid>

          {/* Show batch info */}
          {selectedBatch && (
            <Grid item xs={12}>
              <Alert severity="info">
                <strong>{selectedBatch.batch_code}</strong><br/>
                Current count: {selectedBatch.current_count?.toLocaleString()} fish<br/>
                Total mortality so far: {selectedBatch.total_mortality} fish
                ({selectedBatch.mortality_percentage?.toFixed(1)}%)
              </Alert>
            </Grid>
          )}

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

          {/* Count */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Number of Fish Died *"
              type="number"
              value={formData.count}
              onChange={handleChange('count')}
              required
              fullWidth
              inputProps={{ min: 1 }}
              error={formData.count && selectedBatch && parseInt(formData.count) > selectedBatch.current_count}
              helperText={
                formData.count && selectedBatch && parseInt(formData.count) > selectedBatch.current_count
                  ? "Count exceeds current batch size!"
                  : ""
              }
            />
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
              disabled={mutation.isLoading}
            >
              {mutation.isLoading ? 'Recording...' : 'Record Mortality'}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

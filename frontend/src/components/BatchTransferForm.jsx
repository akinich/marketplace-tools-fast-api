/**
 * ============================================================================
 * Biofloc Operational Forms - Batch Transfer
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 *
 * Form for transferring a batch from one tank to another.
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
  Paper,
  Chip,
} from '@mui/material';
import {
  Save as SaveIcon,
  SwapHoriz as TransferIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';

export default function BatchTransferForm({ onSuccess }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    batch_id: null,
    new_tank_id: null,
    transfer_date: new Date().toISOString().split('T')[0],
    transfer_count: '',
    notes: '',
  });

  const [selectedBatch, setSelectedBatch] = useState(null);

  // Fetch active batches
  const { data: batchesData, isLoading: batchesLoading } = useQuery(
    'bioflocBatchesActive',
    () => bioflocAPI.getBatches({ status: 'active', limit: 100 })
  );

  // Fetch available tanks
  const { data: tanksData, isLoading: tanksLoading } = useQuery(
    'bioflocTanksAll',
    () => bioflocAPI.getTanks({ limit: 100 })
  );

  // Submit mutation
  const mutation = useMutation(
    ({ batchId, data }) => bioflocAPI.transferBatch(batchId, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bioflocBatches');
        queryClient.invalidateQueries('bioflocTanks');
        queryClient.invalidateQueries('bioflocDashboard');
        if (onSuccess) onSuccess();
        // Reset form
        setFormData({
          batch_id: null,
          new_tank_id: null,
          transfer_date: new Date().toISOString().split('T')[0],
          transfer_count: '',
          notes: '',
        });
        setSelectedBatch(null);
      },
    }
  );

  const batches = batchesData?.batches || [];
  const tanks = tanksData?.tanks || [];

  // Filter out current tank from destination options
  const availableTanks = selectedBatch
    ? tanks.filter(t => t.id !== selectedBatch.current_tank_id)
    : tanks;

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleBatchChange = (event, value) => {
    setFormData({
      ...formData,
      batch_id: value?.id || null,
      transfer_count: value?.current_count || '',
    });
    setSelectedBatch(value);
  };

  const handleTankChange = (event, value) => {
    setFormData({ ...formData, new_tank_id: value?.id || null });
  };

  const handleSubmit = () => {
    if (!formData.batch_id) {
      alert('Please select a batch to transfer');
      return;
    }

    if (!formData.new_tank_id) {
      alert('Please select a destination tank');
      return;
    }

    if (!formData.transfer_count || parseInt(formData.transfer_count) <= 0) {
      alert('Please enter a valid fish count');
      return;
    }

    const payload = {
      new_tank_id: formData.new_tank_id,
      transfer_date: formData.transfer_date,
      transfer_count: parseInt(formData.transfer_count),
    };

    if (formData.notes) {
      payload.notes = formData.notes;
    }

    mutation.mutate({ batchId: formData.batch_id, data: payload });
  };

  if (batchesLoading || tanksLoading) {
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
          <TransferIcon color="secondary" />
          <Typography variant="h6" fontWeight="bold">
            Transfer Batch Between Tanks
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Move a batch (or partial batch) from one tank to another. This updates tank assignments and creates a transfer record.
        </Typography>

        {mutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to transfer batch: {mutation.error.response?.data?.detail || mutation.error.message}
          </Alert>
        )}

        {mutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Batch transferred successfully!
          </Alert>
        )}

        <Grid container spacing={2}>
          {/* Batch Selection */}
          <Grid item xs={12}>
            <Autocomplete
              options={batches}
              getOptionLabel={(option) =>
                `${option.batch_code} - ${option.species} (${option.current_count?.toLocaleString()} fish in ${option.current_tank_code || 'N/A'})`
              }
              value={selectedBatch}
              onChange={handleBatchChange}
              renderInput={(params) => (
                <TextField {...params} label="Select Batch to Transfer" required />
              )}
            />
          </Grid>

          {/* Current batch info */}
          {selectedBatch && (
            <Grid item xs={12}>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'info.50' }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  Current Batch Info
                </Typography>
                <Grid container spacing={1}>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" color="text.secondary">
                      Current Tank
                    </Typography>
                    <Typography variant="body2">
                      {selectedBatch.current_tank_code || 'Unknown'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" color="text.secondary">
                      Current Count
                    </Typography>
                    <Typography variant="body2">
                      {selectedBatch.current_count?.toLocaleString()} fish
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" color="text.secondary">
                      Avg Weight
                    </Typography>
                    <Typography variant="body2">
                      {selectedBatch.current_avg_weight_g || 'N/A'} g
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          )}

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Destination Tank */}
          <Grid item xs={12}>
            <Autocomplete
              options={availableTanks}
              getOptionLabel={(option) =>
                `${option.tank_code} - ${option.capacity_liters}L (${option.status})`
              }
              onChange={handleTankChange}
              renderInput={(params) => (
                <TextField {...params} label="Destination Tank" required />
              )}
              disabled={!selectedBatch}
            />
          </Grid>

          {/* Transfer Details */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Transfer Date"
              type="date"
              value={formData.transfer_date}
              onChange={handleChange('transfer_date')}
              required
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Fish Count to Transfer"
              type="number"
              value={formData.transfer_count}
              onChange={handleChange('transfer_count')}
              required
              fullWidth
              inputProps={{
                min: 1,
                max: selectedBatch?.current_count || undefined,
              }}
              helperText={
                selectedBatch
                  ? `Max: ${selectedBatch.current_count?.toLocaleString()} fish`
                  : 'Select a batch first'
              }
              disabled={!selectedBatch}
            />
          </Grid>

          {/* Notes */}
          <Grid item xs={12}>
            <TextField
              label="Transfer Notes"
              value={formData.notes}
              onChange={handleChange('notes')}
              multiline
              rows={2}
              fullWidth
              placeholder="Reason for transfer, observations, etc."
            />
          </Grid>

          {/* Transfer type indicator */}
          {selectedBatch && formData.transfer_count && (
            <Grid item xs={12}>
              <Alert
                severity={
                  parseInt(formData.transfer_count) === selectedBatch.current_count
                    ? 'info'
                    : 'warning'
                }
              >
                {parseInt(formData.transfer_count) === selectedBatch.current_count ? (
                  <Typography variant="body2">
                    <strong>Complete Transfer:</strong> Entire batch will be moved to new tank
                  </Typography>
                ) : (
                  <Typography variant="body2">
                    <strong>Partial Transfer:</strong> {formData.transfer_count} fish will be moved,{' '}
                    {selectedBatch.current_count - parseInt(formData.transfer_count)} will remain in current tank
                  </Typography>
                )}
              </Alert>
            </Grid>
          )}

          {/* Submit Button */}
          <Grid item xs={12}>
            <Button
              variant="contained"
              color="secondary"
              fullWidth
              size="large"
              startIcon={<SaveIcon />}
              onClick={handleSubmit}
              disabled={mutation.isLoading || !selectedBatch}
            >
              {mutation.isLoading ? 'Transferring...' : 'Transfer Batch'}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

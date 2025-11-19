/**
 * ============================================================================
 * Biofloc Operational Forms - Batch Transfer (with Grading Support)
 * ============================================================================
 * Version: 2.0.0
 * Last Updated: 2025-11-19
 *
 * Form for transferring batches between tanks with two modes:
 * - Normal Transfer: Move entire batch from Tank A to Tank B
 * - Graded Transfer: Separate batch by size, create child batches, distribute to tanks
 *
 * GRADING LOGIC (Option B with Historical Data):
 * - Creates child batches (e.g., Batch-001-A, Batch-001-B, Batch-001-C)
 * - Inherits proportional feed costs based on biomass at grading
 * - Copies original stocking date to child batches
 * - Sets initial weight = weight at grading for new batches
 * - Tracks parent-child relationship
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
  Paper,
  IconButton,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormLabel,
  FormControl,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Save as SaveIcon,
  SwapHoriz as TransferIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';

export default function BatchTransferForm({ onSuccess }) {
  const queryClient = useQueryClient();

  const [transferMode, setTransferMode] = useState('normal'); // 'normal' or 'graded'
  const [sourceBatch, setSourceBatch] = useState(null);
  const [transferDate, setTransferDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');

  // Normal transfer
  const [destinationTank, setDestinationTank] = useState(null);

  // Graded transfer
  const [sizeGroups, setSizeGroups] = useState([
    { size_label: 'A', fish_count: '', avg_weight_g: '', destination_tank: null },
    { size_label: 'B', fish_count: '', avg_weight_g: '', destination_tank: null },
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Fetch batches
  const { data: batchesData, isLoading: batchesLoading } = useQuery(
    'bioflocBatchesAll',
    () => bioflocAPI.getBatches({ limit: 100 })
  );

  // Fetch tanks
  const { data: tanksData, isLoading: tanksLoading } = useQuery(
    'bioflocTanksAll',
    () => bioflocAPI.getTanks({ limit: 100 })
  );

  const batches = batchesData?.batches || [];
  const tanks = tanksData?.tanks || [];
  const activeBatches = batches.filter(b => b.status === 'active');

  // Handlers for size groups
  const addSizeGroup = () => {
    if (sizeGroups.length < 3) {
      const nextLabel = String.fromCharCode(65 + sizeGroups.length); // A, B, C
      setSizeGroups([
        ...sizeGroups,
        { size_label: nextLabel, fish_count: '', avg_weight_g: '', destination_tank: null }
      ]);
    }
  };

  const removeSizeGroup = (index) => {
    if (sizeGroups.length > 2) {
      setSizeGroups(sizeGroups.filter((_, i) => i !== index));
    }
  };

  const handleSizeGroupChange = (index, field, value) => {
    const newGroups = [...sizeGroups];
    newGroups[index][field] = value;
    setSizeGroups(newGroups);
  };

  // Validation helpers
  const getTotalGradedFish = () => {
    return sizeGroups.reduce((sum, group) => sum + (parseInt(group.fish_count) || 0), 0);
  };

  const validateGradedTransfer = () => {
    const totalGraded = getTotalGradedFish();
    const sourceFishCount = sourceBatch?.current_count || 0;

    if (totalGraded !== sourceFishCount) {
      return `Total graded fish (${totalGraded}) must equal source batch count (${sourceFishCount})`;
    }

    for (let i = 0; i < sizeGroups.length; i++) {
      const group = sizeGroups[i];
      if (!group.fish_count || parseInt(group.fish_count) <= 0) {
        return `Size ${group.size_label}: Invalid fish count`;
      }
      if (!group.avg_weight_g || parseFloat(group.avg_weight_g) <= 0) {
        return `Size ${group.size_label}: Invalid average weight`;
      }
      if (!group.destination_tank) {
        return `Size ${group.size_label}: No destination tank selected`;
      }
    }

    return null;
  };

  // Submit handlers
  const handleNormalTransfer = async () => {
    if (!sourceBatch) {
      alert('Please select a source batch');
      return;
    }

    if (!destinationTank) {
      alert('Please select a destination tank');
      return;
    }

    if (sourceBatch.current_tank_id === destinationTank.id) {
      alert('Source and destination tanks cannot be the same');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const payload = {
        batch_id: sourceBatch.id,
        from_tank_id: sourceBatch.current_tank_id,
        to_tank_id: destinationTank.id,
        transfer_date: transferDate,
        fish_count: sourceBatch.current_count,
        notes: notes || undefined,
      };

      await bioflocAPI.transferBatch(payload);

      // Success
      queryClient.invalidateQueries('bioflocBatches');
      queryClient.invalidateQueries('bioflocTanks');
      queryClient.invalidateQueries('bioflocDashboard');
      if (onSuccess) onSuccess();

      // Reset form
      setSourceBatch(null);
      setDestinationTank(null);
      setNotes('');
      alert('Batch transferred successfully!');
    } catch (error) {
      setSubmitError(error.response?.data?.detail || error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGradedTransfer = async () => {
    if (!sourceBatch) {
      alert('Please select a source batch');
      return;
    }

    const validationError = validateGradedTransfer();
    if (validationError) {
      alert(validationError);
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Build grading payload
      const gradingPayload = {
        source_batch_id: sourceBatch.id,
        source_tank_id: sourceBatch.current_tank_id,
        grading_date: transferDate,
        size_groups: sizeGroups.map(group => ({
          size_label: group.size_label,
          fish_count: parseInt(group.fish_count),
          avg_weight_g: parseFloat(group.avg_weight_g),
          destination_tank_id: group.destination_tank.id,
        })),
        notes: notes || undefined,
      };

      // Call backend API for graded transfer
      await bioflocAPI.recordGrading(gradingPayload);

      // Success
      queryClient.invalidateQueries('bioflocBatches');
      queryClient.invalidateQueries('bioflocTanks');
      queryClient.invalidateQueries('bioflocDashboard');
      if (onSuccess) onSuccess();

      // Reset form
      setSourceBatch(null);
      setSizeGroups([
        { size_label: 'A', fish_count: '', avg_weight_g: '', destination_tank: null },
        { size_label: 'B', fish_count: '', avg_weight_g: '', destination_tank: null },
      ]);
      setNotes('');
      alert('Graded transfer completed successfully! New batches created.');
    } catch (error) {
      setSubmitError(error.response?.data?.detail || error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = () => {
    if (transferMode === 'normal') {
      handleNormalTransfer();
    } else {
      handleGradedTransfer();
    }
  };

  if (batchesLoading || tanksLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const currentTank = sourceBatch
    ? tanks.find(t => t.id === sourceBatch.current_tank_id)
    : null;

  return (
    <Box>
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <TransferIcon color="primary" />
            <Typography variant="h6" fontWeight="bold">
              Batch Transfer & Grading
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Transfer batches between tanks or perform graded transfer with size separation.
          </Typography>

          {submitError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {submitError}
            </Alert>
          )}

          <Grid container spacing={2}>
            {/* Transfer Mode Selection */}
            <Grid item xs={12}>
              <FormControl component="fieldset">
                <FormLabel component="legend">Transfer Type</FormLabel>
                <RadioGroup
                  value={transferMode}
                  onChange={(e) => setTransferMode(e.target.value)}
                  row
                >
                  <FormControlLabel
                    value="normal"
                    control={<Radio />}
                    label="Normal Transfer (Tank to Tank)"
                  />
                  <FormControlLabel
                    value="graded"
                    control={<Radio />}
                    label="Graded Transfer (Size Separation)"
                  />
                </RadioGroup>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Divider />
            </Grid>

            {/* Transfer Date */}
            <Grid item xs={12} md={6}>
              <TextField
                label="Transfer Date"
                type="date"
                value={transferDate}
                onChange={(e) => setTransferDate(e.target.value)}
                required
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            {/* Source Batch Selection */}
            <Grid item xs={12} md={6}>
              <Autocomplete
                options={activeBatches}
                getOptionLabel={(option) =>
                  `${option.batch_code} - ${option.current_count} fish @ ${option.current_avg_weight_g}g (Tank: ${option.current_tank_code || 'N/A'})`
                }
                value={sourceBatch}
                onChange={(e, value) => setSourceBatch(value)}
                renderInput={(params) => (
                  <TextField {...params} label="Source Batch *" required />
                )}
              />
            </Grid>

            {/* Show current tank info */}
            {sourceBatch && currentTank && (
              <Grid item xs={12}>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'info.50' }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    Source Batch: {sourceBatch.batch_code}
                  </Typography>
                  <Typography variant="body2">
                    Current Tank: {currentTank.tank_code}
                  </Typography>
                  <Typography variant="body2">
                    Population: {sourceBatch.current_count?.toLocaleString()} fish
                  </Typography>
                  <Typography variant="body2">
                    Average Weight: {sourceBatch.current_avg_weight_g}g
                  </Typography>
                  <Typography variant="body2">
                    Total Biomass: {((sourceBatch.current_count * sourceBatch.current_avg_weight_g) / 1000).toFixed(2)} kg
                  </Typography>
                </Paper>
              </Grid>
            )}

            <Grid item xs={12}>
              <Divider />
            </Grid>

            {/* NORMAL TRANSFER MODE */}
            {transferMode === 'normal' && (
              <Grid item xs={12}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                    Destination Tank
                  </Typography>
                  <Autocomplete
                    options={tanks.filter(t => t.id !== sourceBatch?.current_tank_id)}
                    getOptionLabel={(option) =>
                      `${option.tank_code} - ${option.batch_code || 'Empty'} (${option.status})`
                    }
                    value={destinationTank}
                    onChange={(e, value) => setDestinationTank(value)}
                    renderInput={(params) => (
                      <TextField {...params} label="Select Destination Tank *" required />
                    )}
                  />
                  {sourceBatch && destinationTank && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      {sourceBatch.current_count} fish will be moved from {currentTank?.tank_code} to {destinationTank.tank_code}
                    </Alert>
                  )}
                </Paper>
              </Grid>
            )}

            {/* GRADED TRANSFER MODE */}
            {transferMode === 'graded' && sourceBatch && (
              <Grid item xs={12}>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'warning.50' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="subtitle2" fontWeight="bold">
                      Size Groups ({sizeGroups.length}/3)
                    </Typography>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<AddIcon />}
                      onClick={addSizeGroup}
                      disabled={sizeGroups.length >= 3}
                    >
                      Add Size Group
                    </Button>
                  </Box>

                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="body2" fontWeight="bold">
                      Grading creates NEW child batches (e.g., {sourceBatch.batch_code}-A, {sourceBatch.batch_code}-B)
                    </Typography>
                    <Typography variant="caption">
                      • Historical feed costs will be allocated proportionally based on biomass<br />
                      • Original stocking date will be inherited<br />
                      • Total fish across all groups must equal {sourceBatch.current_count}
                    </Typography>
                  </Alert>

                  {/* Size Groups Table */}
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Size</TableCell>
                        <TableCell>Fish Count</TableCell>
                        <TableCell>Avg Weight (g)</TableCell>
                        <TableCell>Biomass (kg)</TableCell>
                        <TableCell>Destination Tank</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {sizeGroups.map((group, index) => {
                        const biomass = (parseInt(group.fish_count) || 0) * (parseFloat(group.avg_weight_g) || 0) / 1000;
                        return (
                          <TableRow key={index}>
                            <TableCell>
                              <Chip label={group.size_label} color="primary" size="small" />
                            </TableCell>
                            <TableCell>
                              <TextField
                                type="number"
                                value={group.fish_count}
                                onChange={(e) => handleSizeGroupChange(index, 'fish_count', e.target.value)}
                                size="small"
                                sx={{ width: 100 }}
                                inputProps={{ min: 1 }}
                                required
                              />
                            </TableCell>
                            <TableCell>
                              <TextField
                                type="number"
                                value={group.avg_weight_g}
                                onChange={(e) => handleSizeGroupChange(index, 'avg_weight_g', e.target.value)}
                                size="small"
                                sx={{ width: 100 }}
                                inputProps={{ step: "0.01", min: 0 }}
                                required
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontWeight="bold">
                                {biomass.toFixed(2)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Autocomplete
                                options={tanks}
                                getOptionLabel={(option) =>
                                  `${option.tank_code} - ${option.batch_code || 'Empty'}`
                                }
                                value={group.destination_tank}
                                onChange={(e, value) => handleSizeGroupChange(index, 'destination_tank', value)}
                                renderInput={(params) => (
                                  <TextField {...params} size="small" required sx={{ width: 200 }} />
                                )}
                              />
                            </TableCell>
                            <TableCell>
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => removeSizeGroup(index)}
                                disabled={sizeGroups.length <= 2}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                      {/* Total row */}
                      <TableRow sx={{ bgcolor: 'grey.100' }}>
                        <TableCell><strong>TOTAL</strong></TableCell>
                        <TableCell>
                          <strong>{getTotalGradedFish()}</strong>
                          {getTotalGradedFish() !== sourceBatch.current_count && (
                            <Chip
                              label="Mismatch!"
                              color="error"
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </TableCell>
                        <TableCell colSpan={4}>
                          <Typography variant="caption" color="text.secondary">
                            Must equal source batch: {sourceBatch.current_count} fish
                          </Typography>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </Paper>
              </Grid>
            )}

            {/* Notes */}
            <Grid item xs={12}>
              <TextField
                label="Notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                multiline
                rows={3}
                fullWidth
                placeholder="Optional: Add any relevant notes about this transfer/grading"
              />
            </Grid>

            {/* Submit Button */}
            <Grid item xs={12}>
              <Button
                variant="contained"
                fullWidth
                size="large"
                color="primary"
                startIcon={<SaveIcon />}
                onClick={handleSubmit}
                disabled={isSubmitting || !sourceBatch}
              >
                {isSubmitting
                  ? 'Processing...'
                  : transferMode === 'normal'
                  ? 'Transfer Batch'
                  : 'Complete Graded Transfer & Create New Batches'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}

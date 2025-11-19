/**
 * ============================================================================
 * Biofloc Operational Forms - Multi-Tank Inputs
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 *
 * Form for recording tank inputs (chemicals, probiotics, carbon sources, etc.)
 * Supports multiple tanks in one session.
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
  IconButton,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Save as SaveIcon,
  Science as InputIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';
import { inventoryAPI } from '../api';

const INPUT_TYPES = [
  { value: 'chemical', label: 'Chemical' },
  { value: 'probiotic', label: 'Probiotic' },
  { value: 'carbon_source', label: 'Carbon Source' },
  { value: 'mineral', label: 'Mineral' },
  { value: 'other', label: 'Other' },
];

const COMMON_REASONS = [
  'pH Adjustment',
  'Ammonia Control',
  'Nitrite Control',
  'Floc Boost',
  'Disease Prevention',
  'Disease Treatment',
  'Alkalinity Adjustment',
  'Oxygen Supplement',
  'Other',
];

export default function TankInputsForm({ onSuccess }) {
  const queryClient = useQueryClient();

  // Session-level data (shared)
  const [sessionData, setSessionData] = useState({
    input_date: new Date().toISOString().split('T')[0],
    input_time: new Date().toTimeString().slice(0, 5),
    input_type: 'chemical',
    item_sku: '',
    item_name: '',
    unit: 'ml',
    reason: '',
  });

  // Tank entries (array of tanks receiving input)
  const [tankEntries, setTankEntries] = useState([
    {
      tank_id: null,
      tank_obj: null,
      quantity: '',
      notes: '',
    }
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResults, setSubmitResults] = useState({ success: [], errors: [] });

  // Fetch tanks
  const { data: tanksData, isLoading: tanksLoading } = useQuery(
    'bioflocTanksAll',
    () => bioflocAPI.getTanks({ limit: 100 })
  );

  // Fetch inventory items for autocomplete (optional SKU)
  // Make this optional - if inventory module not available, just skip
  const { data: inventoryData } = useQuery(
    'inventoryItemsAll',
    () => inventoryAPI.getItems({ is_active: true, limit: 200 }),
    {
      retry: false,
      onError: (error) => {
        // Silently fail - inventory integration is optional
        console.log('Inventory integration not available, SKU autocomplete disabled');
      }
    }
  );

  const tanks = tanksData?.tanks || [];
  const inventoryItems = inventoryData?.items || [];

  // Session-level handlers
  const handleSessionChange = (field) => (event) => {
    setSessionData({ ...sessionData, [field]: event.target.value });
  };

  const handleInventoryItemSelect = (value) => {
    if (value) {
      setSessionData({
        ...sessionData,
        item_sku: value.sku || '',
        item_name: value.item_name || '',
        unit: value.unit || 'ml',
      });
    }
  };

  // Tank entry handlers
  const addTankEntry = () => {
    setTankEntries([
      ...tankEntries,
      {
        tank_id: null,
        tank_obj: null,
        quantity: '',
        notes: '',
      }
    ]);
  };

  const removeTankEntry = (index) => {
    if (tankEntries.length > 1) {
      setTankEntries(tankEntries.filter((_, i) => i !== index));
    }
  };

  const handleTankChange = (index, value) => {
    const newEntries = [...tankEntries];
    newEntries[index].tank_id = value?.id || null;
    newEntries[index].tank_obj = value;
    setTankEntries(newEntries);
  };

  const handleQuantityChange = (index, value) => {
    const newEntries = [...tankEntries];
    newEntries[index].quantity = value;
    setTankEntries(newEntries);
  };

  const handleNotesChange = (index, value) => {
    const newEntries = [...tankEntries];
    newEntries[index].notes = value;
    setTankEntries(newEntries);
  };

  // Submit handler
  const handleSubmit = async () => {
    setSubmitResults({ success: [], errors: [] });
    setIsSubmitting(true);

    const successfulSubmissions = [];
    const failedSubmissions = [];

    try {
      // Validate session data
      if (!sessionData.item_name) {
        alert('Please enter an item name');
        setIsSubmitting(false);
        return;
      }

      // Submit each tank's input
      for (let i = 0; i < tankEntries.length; i++) {
        const entry = tankEntries[i];

        if (!entry.tank_id) {
          failedSubmissions.push({
            tank: `Tank ${i + 1}`,
            error: 'No tank selected'
          });
          continue;
        }

        if (!entry.quantity || parseFloat(entry.quantity) <= 0) {
          failedSubmissions.push({
            tank: entry.tank_obj?.tank_code || `Tank ${i + 1}`,
            error: 'Invalid quantity'
          });
          continue;
        }

        // Build payload
        const payload = {
          tank_id: entry.tank_id,
          input_date: sessionData.input_date,
          input_time: sessionData.input_time,
          input_type: sessionData.input_type,
          item_name: sessionData.item_name,
          quantity: parseFloat(entry.quantity),
          unit: sessionData.unit,
        };

        if (sessionData.item_sku) payload.item_sku = sessionData.item_sku;
        if (sessionData.reason) payload.reason = sessionData.reason;
        if (entry.notes) payload.notes = entry.notes;

        try {
          await bioflocAPI.recordTankInput(payload);
          successfulSubmissions.push(entry.tank_obj?.tank_code || `Tank ${i + 1}`);
        } catch (error) {
          failedSubmissions.push({
            tank: entry.tank_obj?.tank_code || `Tank ${i + 1}`,
            error: error.response?.data?.detail || error.message
          });
        }
      }

      // Update results
      setSubmitResults({
        success: successfulSubmissions,
        errors: failedSubmissions
      });

      // If all succeeded, reset form
      if (failedSubmissions.length === 0) {
        queryClient.invalidateQueries('bioflocTankInputs');
        queryClient.invalidateQueries('bioflocDashboard');
        if (onSuccess) onSuccess();

        // Reset form
        setSessionData({
          input_date: new Date().toISOString().split('T')[0],
          input_time: new Date().toTimeString().slice(0, 5),
          input_type: 'chemical',
          item_sku: '',
          item_name: '',
          unit: 'ml',
          reason: '',
        });
        setTankEntries([
          {
            tank_id: null,
            tank_obj: null,
            quantity: '',
            notes: '',
          }
        ]);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Calculate total quantity
  const getTotalQuantity = () => {
    return tankEntries.reduce((sum, entry) => {
      return sum + (parseFloat(entry.quantity) || 0);
    }, 0).toFixed(2);
  };

  if (tanksLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <InputIcon color="success" />
            <Typography variant="h6" fontWeight="bold">
              Multi-Tank Input Recording
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Record chemical, probiotic, or other inputs for multiple tanks in one session.
          </Typography>

          {/* Session-level data */}
          <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'success.50' }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              Input Details (Applied to All Tanks)
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Input Date"
                  type="date"
                  value={sessionData.input_date}
                  onChange={handleSessionChange('input_date')}
                  required
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Input Time"
                  type="time"
                  value={sessionData.input_time}
                  onChange={handleSessionChange('input_time')}
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth size="small" required>
                  <InputLabel>Input Type</InputLabel>
                  <Select
                    value={sessionData.input_type}
                    onChange={handleSessionChange('input_type')}
                    label="Input Type"
                  >
                    {INPUT_TYPES.map(type => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <Autocomplete
                  options={COMMON_REASONS}
                  freeSolo
                  value={sessionData.reason}
                  onChange={(e, value) => setSessionData({ ...sessionData, reason: value || '' })}
                  renderInput={(params) => (
                    <TextField {...params} label="Reason" size="small" />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Autocomplete
                  options={inventoryItems}
                  getOptionLabel={(option) =>
                    `${option.item_name} (${option.sku || 'No SKU'})`
                  }
                  onChange={(e, value) => handleInventoryItemSelect(value)}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Select from Inventory (Optional)"
                      size="small"
                      helperText="Or enter manually below"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Item SKU (Optional)"
                  value={sessionData.item_sku}
                  onChange={handleSessionChange('item_sku')}
                  fullWidth
                  size="small"
                  placeholder="e.g., CHEM-001"
                />
              </Grid>
              <Grid item xs={12} md={8}>
                <TextField
                  label="Item Name"
                  value={sessionData.item_name}
                  onChange={handleSessionChange('item_name')}
                  required
                  fullWidth
                  size="small"
                  placeholder="e.g., Calcium Hypochlorite, Probiotics Mix, Molasses"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  label="Unit"
                  value={sessionData.unit}
                  onChange={handleSessionChange('unit')}
                  required
                  fullWidth
                  size="small"
                  placeholder="ml, g, kg, L"
                />
              </Grid>
            </Grid>
          </Paper>

          {/* Results display */}
          {submitResults.success.length > 0 && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Successfully recorded inputs for: {submitResults.success.join(', ')}
            </Alert>
          )}
          {submitResults.errors.length > 0 && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="bold">Errors:</Typography>
              {submitResults.errors.map((err, idx) => (
                <Typography key={idx} variant="body2">
                  • {err.tank}: {err.error}
                </Typography>
              ))}
            </Alert>
          )}

          {/* Tank entries */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">
                Tanks Receiving Input ({tankEntries.length})
              </Typography>
              <Button
                size="small"
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={addTankEntry}
              >
                Add Tank
              </Button>
            </Box>

            {tankEntries.map((entry, tankIndex) => (
              <Paper key={tankIndex} variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    Tank #{tankIndex + 1}
                  </Typography>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => removeTankEntry(tankIndex)}
                    disabled={tankEntries.length === 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Autocomplete
                      options={tanks}
                      getOptionLabel={(option) =>
                        `${option.tank_code} - ${option.batch_code || 'No batch'} (${option.status})`
                      }
                      value={entry.tank_obj}
                      onChange={(e, value) => handleTankChange(tankIndex, value)}
                      renderInput={(params) => (
                        <TextField {...params} label="Select Tank" required size="small" />
                      )}
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      label={`Quantity (${sessionData.unit})`}
                      type="number"
                      value={entry.quantity}
                      onChange={(e) => handleQuantityChange(tankIndex, e.target.value)}
                      required
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.1", min: 0 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      label="Tank-specific Notes"
                      value={entry.notes}
                      onChange={(e) => handleNotesChange(tankIndex, e.target.value)}
                      fullWidth
                      size="small"
                      placeholder="Optional"
                    />
                  </Grid>
                </Grid>
              </Paper>
            ))}

            {/* Total display */}
            <Paper sx={{ p: 2, bgcolor: 'info.50' }}>
              <Typography variant="body2">
                <strong>Total {sessionData.item_name || 'Input'}:</strong> {getTotalQuantity()} {sessionData.unit} across {tankEntries.length} tank(s)
              </Typography>
            </Paper>
          </Box>

          {/* Submit button */}
          <Button
            variant="contained"
            color="success"
            fullWidth
            size="large"
            startIcon={<SaveIcon />}
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Recording Inputs...' : `Record Input for ${tankEntries.length} Tank(s)`}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}

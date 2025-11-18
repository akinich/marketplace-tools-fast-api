/**
 * ============================================================================
 * Biofloc Operational Forms - Water Quality Test
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-18
 *
 * Form for recording water quality test parameters.
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
} from '@mui/material';
import { Save as SaveIcon, Opacity as WaterIcon } from '@mui/icons-material';

import { bioflocAPI } from '../api';

export default function WaterTestForm({ onSuccess }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    tank_id: null,
    test_date: new Date().toISOString().split('T')[0],
    test_time: new Date().toTimeString().slice(0, 5),
    temperature_c: '',
    ph: '',
    dissolved_oxygen_mgl: '',
    salinity_ppt: '',
    ammonia_nh3_mgl: '',
    nitrite_no2_mgl: '',
    nitrate_no3_mgl: '',
    alkalinity_mgl: '',
    hardness_mgl: '',
    turbidity_ntu: '',
    tds_mgl: '',
    floc_volume_mll: '',
    notes: '',
  });

  // Fetch tanks
  const { data: tanksData, isLoading: tanksLoading } = useQuery(
    'bioflocTanksAll',
    () => bioflocAPI.getTanks({ limit: 100 })
  );

  // Submit mutation
  const mutation = useMutation(
    (data) => bioflocAPI.recordWaterTest(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bioflocWaterTests');
        queryClient.invalidateQueries('bioflocDashboard');
        if (onSuccess) onSuccess();
        // Reset form
        setFormData({
          tank_id: null,
          test_date: new Date().toISOString().split('T')[0],
          test_time: new Date().toTimeString().slice(0, 5),
          temperature_c: '',
          ph: '',
          dissolved_oxygen_mgl: '',
          salinity_ppt: '',
          ammonia_nh3_mgl: '',
          nitrite_no2_mgl: '',
          nitrate_no3_mgl: '',
          alkalinity_mgl: '',
          hardness_mgl: '',
          turbidity_ntu: '',
          tds_mgl: '',
          floc_volume_mll: '',
          notes: '',
        });
      },
    }
  );

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleTankChange = (event, value) => {
    setFormData({ ...formData, tank_id: value?.id || null });
  };

  const handleSubmit = () => {
    if (!formData.tank_id) {
      alert('Please select a tank');
      return;
    }

    // Build payload with only non-empty values
    const payload = {
      tank_id: formData.tank_id,
      test_date: formData.test_date,
      test_time: formData.test_time || undefined,
    };

    // Add optional parameters
    if (formData.temperature_c) payload.temperature_c = parseFloat(formData.temperature_c);
    if (formData.ph) payload.ph = parseFloat(formData.ph);
    if (formData.dissolved_oxygen_mgl) payload.dissolved_oxygen_mgl = parseFloat(formData.dissolved_oxygen_mgl);
    if (formData.salinity_ppt) payload.salinity_ppt = parseFloat(formData.salinity_ppt);
    if (formData.ammonia_nh3_mgl) payload.ammonia_nh3_mgl = parseFloat(formData.ammonia_nh3_mgl);
    if (formData.nitrite_no2_mgl) payload.nitrite_no2_mgl = parseFloat(formData.nitrite_no2_mgl);
    if (formData.nitrate_no3_mgl) payload.nitrate_no3_mgl = parseFloat(formData.nitrate_no3_mgl);
    if (formData.alkalinity_mgl) payload.alkalinity_mgl = parseFloat(formData.alkalinity_mgl);
    if (formData.hardness_mgl) payload.hardness_mgl = parseFloat(formData.hardness_mgl);
    if (formData.turbidity_ntu) payload.turbidity_ntu = parseFloat(formData.turbidity_ntu);
    if (formData.tds_mgl) payload.tds_mgl = parseFloat(formData.tds_mgl);
    if (formData.floc_volume_mll) payload.floc_volume_mll = parseFloat(formData.floc_volume_mll);
    if (formData.notes) payload.notes = formData.notes;

    mutation.mutate(payload);
  };

  const tanks = tanksData?.tanks || [];

  if (tanksLoading) {
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
          <WaterIcon color="primary" />
          <Typography variant="h6" fontWeight="bold">
            Record Water Quality Test
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Record water quality parameters. All measurements are optional - enter only what you tested.
        </Typography>

        {mutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to record water test: {mutation.error.message}
          </Alert>
        )}

        {mutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Water test recorded successfully!
          </Alert>
        )}

        <Grid container spacing={2}>
          {/* Tank Selection */}
          <Grid item xs={12}>
            <Autocomplete
              options={tanks}
              getOptionLabel={(option) =>
                `${option.tank_name} (${option.tank_code})${option.current_batch_code ? ` - Batch: ${option.current_batch_code}` : ''}`
              }
              onChange={handleTankChange}
              renderInput={(params) => (
                <TextField {...params} label="Select Tank" required />
              )}
            />
          </Grid>

          {/* Date & Time */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Test Date"
              type="date"
              value={formData.test_date}
              onChange={handleChange('test_date')}
              required
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Test Time"
              type="time"
              value={formData.test_time}
              onChange={handleChange('test_time')}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Core Parameters */}
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }}>
              <Typography variant="caption" color="text.secondary">
                CORE PARAMETERS
              </Typography>
            </Divider>
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              label="Temperature (°C)"
              type="number"
              value={formData.temperature_c}
              onChange={handleChange('temperature_c')}
              fullWidth
              inputProps={{ step: "0.1" }}
            />
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              label="pH"
              type="number"
              value={formData.ph}
              onChange={handleChange('ph')}
              fullWidth
              inputProps={{ step: "0.1", min: 0, max: 14 }}
            />
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              label="Dissolved Oxygen (mg/L)"
              type="number"
              value={formData.dissolved_oxygen_mgl}
              onChange={handleChange('dissolved_oxygen_mgl')}
              fullWidth
              inputProps={{ step: "0.1" }}
            />
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              label="Salinity (ppt)"
              type="number"
              value={formData.salinity_ppt}
              onChange={handleChange('salinity_ppt')}
              fullWidth
              inputProps={{ step: "0.1" }}
            />
          </Grid>

          {/* Nitrogen Cycle */}
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }}>
              <Typography variant="caption" color="text.secondary">
                NITROGEN CYCLE
              </Typography>
            </Divider>
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Ammonia NH3 (mg/L)"
              type="number"
              value={formData.ammonia_nh3_mgl}
              onChange={handleChange('ammonia_nh3_mgl')}
              fullWidth
              inputProps={{ step: "0.01" }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Nitrite NO2 (mg/L)"
              type="number"
              value={formData.nitrite_no2_mgl}
              onChange={handleChange('nitrite_no2_mgl')}
              fullWidth
              inputProps={{ step: "0.01" }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Nitrate NO3 (mg/L)"
              type="number"
              value={formData.nitrate_no3_mgl}
              onChange={handleChange('nitrate_no3_mgl')}
              fullWidth
              inputProps={{ step: "0.01" }}
            />
          </Grid>

          {/* Other Parameters */}
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }}>
              <Typography variant="caption" color="text.secondary">
                OTHER PARAMETERS
              </Typography>
            </Divider>
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Alkalinity (mg/L)"
              type="number"
              value={formData.alkalinity_mgl}
              onChange={handleChange('alkalinity_mgl')}
              fullWidth
              inputProps={{ step: "1" }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Hardness (mg/L)"
              type="number"
              value={formData.hardness_mgl}
              onChange={handleChange('hardness_mgl')}
              fullWidth
              inputProps={{ step: "1" }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Turbidity (NTU)"
              type="number"
              value={formData.turbidity_ntu}
              onChange={handleChange('turbidity_ntu')}
              fullWidth
              inputProps={{ step: "0.1" }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="TDS - Total Dissolved Solids (mg/L)"
              type="number"
              value={formData.tds_mgl}
              onChange={handleChange('tds_mgl')}
              fullWidth
              inputProps={{ step: "1" }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Floc Volume (ml/L)"
              type="number"
              value={formData.floc_volume_mll}
              onChange={handleChange('floc_volume_mll')}
              fullWidth
              inputProps={{ step: "0.1" }}
              helperText="Imhoff cone measurement"
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
              fullWidth
              size="large"
              startIcon={<SaveIcon />}
              onClick={handleSubmit}
              disabled={mutation.isLoading}
            >
              {mutation.isLoading ? 'Recording...' : 'Record Water Test'}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

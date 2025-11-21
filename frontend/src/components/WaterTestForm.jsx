/**
 * ============================================================================
 * Biofloc Operational Forms - Multi-Tank Water Quality Test
 * ============================================================================
 * Version: 2.1.0
 * Last Updated: 2025-11-21
 *
 * Form for recording water quality test parameters.
 * Supports multiple tanks in one test session.
 *
 * CHANGES in v2.0.0:
 * - Added multi-tank support: record water tests for multiple tanks at once
 * - Test date and time shared across all tanks
 * - Each tank has individual parameter readings
 * ============================================================================
 */

import React, { useState } from 'react';
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
  Divider,
  Paper,
  IconButton,
  Chip,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import WaterIcon from '@mui/icons-material/Opacity';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

import { bioflocAPI } from '../api';

export default function WaterTestForm({ onSuccess }) {
  const queryClient = useQueryClient();

  // Session-level data (shared)
  const [sessionData, setSessionData] = useState({
    test_date: new Date().toISOString().split('T')[0],
    test_time: new Date().toTimeString().slice(0, 5),
  });

  // Tank test entries (array of tanks being tested)
  const [tankEntries, setTankEntries] = useState([
    {
      tank_id: null,
      tank_obj: null,
      parameters: {
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
      }
    }
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResults, setSubmitResults] = useState({ success: [], errors: [] });

  // Fetch tanks
  const { data: tanksData, isLoading: tanksLoading } = useQuery(
    'bioflocTanksAll',
    () => bioflocAPI.getTanks({ limit: 100 })
  );

  const tanks = tanksData?.tanks || [];

  // Session-level handlers
  const handleSessionChange = (field) => (event) => {
    setSessionData({ ...sessionData, [field]: event.target.value });
  };

  // Tank entry handlers
  const addTankEntry = () => {
    setTankEntries([
      ...tankEntries,
      {
        tank_id: null,
        tank_obj: null,
        parameters: {
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
        }
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

  const handleParameterChange = (tankIndex, field, value) => {
    const newEntries = [...tankEntries];
    newEntries[tankIndex].parameters[field] = value;
    setTankEntries(newEntries);
  };

  // Submit handler
  const handleSubmit = async () => {
    setSubmitResults({ success: [], errors: [] });
    setIsSubmitting(true);

    const successfulSubmissions = [];
    const failedSubmissions = [];

    try {
      // Submit each tank's water test
      for (let i = 0; i < tankEntries.length; i++) {
        const entry = tankEntries[i];

        if (!entry.tank_id) {
          failedSubmissions.push({
            tank: `Tank ${i + 1}`,
            error: 'No tank selected'
          });
          continue;
        }

        // Build payload (only include non-empty parameters)
        const payload = {
          tank_id: entry.tank_id,
          test_date: sessionData.test_date,
          test_time: sessionData.test_time,
        };

        // Add parameters if provided
        Object.keys(entry.parameters).forEach(key => {
          if (entry.parameters[key] !== '') {
            payload[key] = key === 'notes' ? entry.parameters[key] : parseFloat(entry.parameters[key]);
          }
        });

        try {
          await bioflocAPI.recordWaterTest(payload);
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
        queryClient.invalidateQueries('bioflocWaterTests');
        queryClient.invalidateQueries('bioflocDashboard');
        if (onSuccess) onSuccess();

        // Reset form
        setSessionData({
          test_date: new Date().toISOString().split('T')[0],
          test_time: new Date().toTimeString().slice(0, 5),
        });
        setTankEntries([
          {
            tank_id: null,
            tank_obj: null,
            parameters: {
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
            }
          }
        ]);
      }
    } finally {
      setIsSubmitting(false);
    }
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
            <WaterIcon color="info" />
            <Typography variant="h6" fontWeight="bold">
              Multi-Tank Water Quality Test
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Record water quality parameters for multiple tanks in one test session.
          </Typography>

          {/* Session-level data */}
          <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'info.50' }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              Test Session Details (Applied to All Tanks)
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Test Date"
                  type="date"
                  value={sessionData.test_date}
                  onChange={handleSessionChange('test_date')}
                  required
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Test Time"
                  type="time"
                  value={sessionData.test_time}
                  onChange={handleSessionChange('test_time')}
                  required
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
            </Grid>
          </Paper>

          {/* Results display */}
          {submitResults.success.length > 0 && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Successfully recorded water tests for: {submitResults.success.join(', ')}
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
                Tanks Being Tested ({tankEntries.length})
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

                {/* Tank selection */}
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12}>
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
                </Grid>

                {/* Water quality parameters */}
                <Divider sx={{ my: 2 }}>
                  <Chip label="Core Parameters" size="small" />
                </Divider>

                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Temperature (°C)"
                      type="number"
                      value={entry.parameters.temperature_c}
                      onChange={(e) => handleParameterChange(tankIndex, 'temperature_c', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.1" }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="pH"
                      type="number"
                      value={entry.parameters.ph}
                      onChange={(e) => handleParameterChange(tankIndex, 'ph', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.1", min: 0, max: 14 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Dissolved Oxygen (mg/L)"
                      type="number"
                      value={entry.parameters.dissolved_oxygen_mgl}
                      onChange={(e) => handleParameterChange(tankIndex, 'dissolved_oxygen_mgl', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.1", min: 0 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Salinity (ppt)"
                      type="number"
                      value={entry.parameters.salinity_ppt}
                      onChange={(e) => handleParameterChange(tankIndex, 'salinity_ppt', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.1", min: 0 }}
                    />
                  </Grid>
                </Grid>

                <Divider sx={{ my: 2 }}>
                  <Chip label="Nitrogen Cycle" size="small" />
                </Divider>

                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Ammonia NH3 (mg/L)"
                      type="number"
                      value={entry.parameters.ammonia_nh3_mgl}
                      onChange={(e) => handleParameterChange(tankIndex, 'ammonia_nh3_mgl', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.01", min: 0 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Nitrite NO2 (mg/L)"
                      type="number"
                      value={entry.parameters.nitrite_no2_mgl}
                      onChange={(e) => handleParameterChange(tankIndex, 'nitrite_no2_mgl', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.01", min: 0 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Nitrate NO3 (mg/L)"
                      type="number"
                      value={entry.parameters.nitrate_no3_mgl}
                      onChange={(e) => handleParameterChange(tankIndex, 'nitrate_no3_mgl', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.1", min: 0 }}
                    />
                  </Grid>
                </Grid>

                <Divider sx={{ my: 2 }}>
                  <Chip label="Other Parameters" size="small" />
                </Divider>

                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Alkalinity (mg/L)"
                      type="number"
                      value={entry.parameters.alkalinity_mgl}
                      onChange={(e) => handleParameterChange(tankIndex, 'alkalinity_mgl', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "1", min: 0 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Hardness (mg/L)"
                      type="number"
                      value={entry.parameters.hardness_mgl}
                      onChange={(e) => handleParameterChange(tankIndex, 'hardness_mgl', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "1", min: 0 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Turbidity (NTU)"
                      type="number"
                      value={entry.parameters.turbidity_ntu}
                      onChange={(e) => handleParameterChange(tankIndex, 'turbidity_ntu', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.1", min: 0 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="TDS (mg/L)"
                      type="number"
                      value={entry.parameters.tds_mgl}
                      onChange={(e) => handleParameterChange(tankIndex, 'tds_mgl', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "1", min: 0 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Floc Volume (ml/L)"
                      type="number"
                      value={entry.parameters.floc_volume_mll}
                      onChange={(e) => handleParameterChange(tankIndex, 'floc_volume_mll', e.target.value)}
                      fullWidth
                      size="small"
                      inputProps={{ step: "0.1", min: 0 }}
                      helperText="Biofloc specific"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Notes"
                      value={entry.parameters.notes}
                      onChange={(e) => handleParameterChange(tankIndex, 'notes', e.target.value)}
                      fullWidth
                      size="small"
                      placeholder="Tank-specific notes"
                    />
                  </Grid>
                </Grid>
              </Paper>
            ))}
          </Box>

          {/* Submit button */}
          <Button
            variant="contained"
            color="info"
            fullWidth
            size="large"
            startIcon={<SaveIcon />}
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Recording Tests...' : `Record Water Tests for ${tankEntries.length} Tank(s)`}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}

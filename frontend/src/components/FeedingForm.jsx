/**
 * ============================================================================
 * Biofloc Operational Forms - Multi-Tank Feeding Session
 * ============================================================================
 * Version: 2.1.0
 * Last Updated: 2025-11-19
 *
 * Changelog:
 * ----------
 * v2.1.0 (2025-11-19):
 *   - CRITICAL FIX: Changed dropdown to show item_name first instead of SKU
 *   - Fixed onChange to send item_name as fallback if SKU is not set
 *   - Display format now: "Item Name - SKU: XXX (stock available)"
 *
 * v2.0.0 (2025-11-19):
 *   - Added multi-tank support: record feeding for multiple tanks in one session
 *   - Each tank can have different feed items and quantities
 *   - Session-level data (date, time, session number) shared across all tanks
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
  IconButton,
  Autocomplete,
  Divider,
  CircularProgress,
  Paper,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Restaurant as FeedIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';
import { inventoryAPI } from '../api';

export default function FeedingForm({ onSuccess }) {
  const queryClient = useQueryClient();

  // Session-level data (shared across all tanks)
  const [sessionData, setSessionData] = useState({
    feeding_date: new Date().toISOString().split('T')[0],
    session_number: 1,
    feed_time: new Date().toTimeString().slice(0, 5),
    notes: '',
  });

  // Tank feeding entries (array of tanks being fed)
  const [tankEntries, setTankEntries] = useState([
    {
      tank_id: null,
      tank_obj: null,
      feedItems: [{ sku: '', quantity_kg: '', notes: '' }]
    }
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResults, setSubmitResults] = useState({ success: [], errors: [] });

  // Fetch tanks with active batches
  const { data: tanksData, isLoading: tanksLoading } = useQuery(
    'bioflocTanksActive',
    () => bioflocAPI.getTanks({ status: 'in_use' })
  );

  // Fetch inventory items (Fish Feed category) - optional integration
  const { data: inventoryData, isLoading: inventoryLoading } = useQuery(
    'inventoryFeedItems',
    () => inventoryAPI.getItems({ category: 'Fish Feed', is_active: true }),
    {
      retry: false,
      onError: (error) => {
        // Silently fail - inventory integration is optional
        console.log('Inventory integration not available, feed item autocomplete disabled');
      }
    }
  );

  const tanks = tanksData?.tanks || [];
  const feedSkus = inventoryData?.items || [];

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
        feedItems: [{ sku: '', quantity_kg: '', notes: '' }]
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

  // Feed item handlers
  const addFeedItem = (tankIndex) => {
    const newEntries = [...tankEntries];
    newEntries[tankIndex].feedItems.push({ sku: '', quantity_kg: '', notes: '' });
    setTankEntries(newEntries);
  };

  const removeFeedItem = (tankIndex, itemIndex) => {
    const newEntries = [...tankEntries];
    if (newEntries[tankIndex].feedItems.length > 1) {
      newEntries[tankIndex].feedItems = newEntries[tankIndex].feedItems.filter((_, i) => i !== itemIndex);
      setTankEntries(newEntries);
    }
  };

  const handleFeedItemChange = (tankIndex, itemIndex, field, value) => {
    const newEntries = [...tankEntries];
    newEntries[tankIndex].feedItems[itemIndex][field] = value;
    setTankEntries(newEntries);
  };

  // Submit handler
  const handleSubmit = async () => {
    setSubmitResults({ success: [], errors: [] });
    setIsSubmitting(true);

    const successfulSubmissions = [];
    const failedSubmissions = [];

    try {
      // Submit each tank's feeding session
      for (let i = 0; i < tankEntries.length; i++) {
        const entry = tankEntries[i];

        if (!entry.tank_id) {
          failedSubmissions.push({
            tank: `Tank ${i + 1}`,
            error: 'No tank selected'
          });
          continue;
        }

        // Filter valid feed items
        const validItems = entry.feedItems.filter(
          item => item.sku && item.quantity_kg && parseFloat(item.quantity_kg) > 0
        );

        if (validItems.length === 0) {
          failedSubmissions.push({
            tank: entry.tank_obj?.tank_code || `Tank ${i + 1}`,
            error: 'No valid feed items'
          });
          continue;
        }

        // Build payload
        const payload = {
          tank_id: entry.tank_id,
          feeding_date: sessionData.feeding_date,
          session_number: parseInt(sessionData.session_number),
          feed_time: sessionData.feed_time,
          feed_items: validItems.map(item => ({
            sku: item.sku,
            quantity_kg: parseFloat(item.quantity_kg),
            notes: item.notes || undefined,
          })),
          notes: sessionData.notes || undefined,
        };

        try {
          await bioflocAPI.recordFeeding(payload);
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
        queryClient.invalidateQueries('bioflocFeedingSessions');
        queryClient.invalidateQueries('bioflocBatches');
        queryClient.invalidateQueries('bioflocDashboard');
        if (onSuccess) onSuccess();

        // Reset form
        setSessionData({
          feeding_date: new Date().toISOString().split('T')[0],
          session_number: 1,
          feed_time: new Date().toTimeString().slice(0, 5),
          notes: '',
        });
        setTankEntries([
          {
            tank_id: null,
            tank_obj: null,
            feedItems: [{ sku: '', quantity_kg: '', notes: '' }]
          }
        ]);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Calculate total feed for a tank
  const getTankTotalFeed = (tankIndex) => {
    return tankEntries[tankIndex].feedItems.reduce((sum, item) => {
      return sum + (parseFloat(item.quantity_kg) || 0);
    }, 0).toFixed(2);
  };

  if (tanksLoading || inventoryLoading) {
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
            <FeedIcon color="primary" />
            <Typography variant="h6" fontWeight="bold">
              Multi-Tank Feeding Session
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Record feeding for multiple tanks in one session. Session details (date, time) will be applied to all tanks.
          </Typography>

          {/* Session-level data */}
          <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'primary.50' }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              Session Details (Applied to All Tanks)
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Feeding Date"
                  type="date"
                  value={sessionData.feeding_date}
                  onChange={handleSessionChange('feeding_date')}
                  required
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Session Number"
                  type="number"
                  value={sessionData.session_number}
                  onChange={handleSessionChange('session_number')}
                  required
                  fullWidth
                  size="small"
                  inputProps={{ min: 1 }}
                  helperText="1=Morning, 2=Afternoon, etc."
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Feed Time"
                  type="time"
                  value={sessionData.feed_time}
                  onChange={handleSessionChange('feed_time')}
                  required
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Session Notes"
                  value={sessionData.notes}
                  onChange={handleSessionChange('notes')}
                  fullWidth
                  size="small"
                  placeholder="Optional notes for entire session"
                />
              </Grid>
            </Grid>
          </Paper>

          {/* Results display */}
          {submitResults.success.length > 0 && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Successfully recorded feeding for: {submitResults.success.join(', ')}
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
                Tanks Being Fed ({tankEntries.length})
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
                        `${option.tank_code} - ${option.batch_code || 'No batch'} (${option.current_batch_count?.toLocaleString() || 0} fish)`
                      }
                      value={entry.tank_obj}
                      onChange={(e, value) => handleTankChange(tankIndex, value)}
                      renderInput={(params) => (
                        <TextField {...params} label="Select Tank" required size="small" />
                      )}
                    />
                  </Grid>
                </Grid>

                {/* Feed items for this tank */}
                <Divider sx={{ my: 2 }}>
                  <Chip label="Feed Items" size="small" />
                </Divider>

                {entry.feedItems.map((item, itemIndex) => (
                  <Grid container spacing={2} key={itemIndex} sx={{ mb: 2 }}>
                    <Grid item xs={12} md={5}>
                      <Autocomplete
                        options={feedSkus}
                        getOptionLabel={(option) =>
                          `${option.item_name} - SKU: ${option.sku || 'N/A'} (${option.current_qty} ${option.unit} available)`
                        }
                        value={feedSkus.find(f => f.sku === item.sku || f.item_name === item.sku) || null}
                        onChange={(e, value) =>
                          handleFeedItemChange(tankIndex, itemIndex, 'sku', value?.sku || value?.item_name || '')
                        }
                        renderInput={(params) => (
                          <TextField {...params} label="Feed Item" required size="small" />
                        )}
                      />
                    </Grid>
                    <Grid item xs={12} md={2}>
                      <TextField
                        label="Quantity (kg)"
                        type="number"
                        value={item.quantity_kg}
                        onChange={(e) =>
                          handleFeedItemChange(tankIndex, itemIndex, 'quantity_kg', e.target.value)
                        }
                        required
                        fullWidth
                        size="small"
                        inputProps={{ step: "0.1", min: 0 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        label="Notes"
                        value={item.notes}
                        onChange={(e) =>
                          handleFeedItemChange(tankIndex, itemIndex, 'notes', e.target.value)
                        }
                        fullWidth
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={12} md={1}>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => removeFeedItem(tankIndex, itemIndex)}
                        disabled={entry.feedItems.length === 1}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Grid>
                  </Grid>
                ))}

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                  <Button
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={() => addFeedItem(tankIndex)}
                  >
                    Add Feed Item
                  </Button>
                  <Chip
                    label={`Total: ${getTankTotalFeed(tankIndex)} kg`}
                    color="primary"
                    variant="outlined"
                  />
                </Box>
              </Paper>
            ))}
          </Box>

          {/* Submit button */}
          <Button
            variant="contained"
            color="primary"
            fullWidth
            size="large"
            startIcon={<SaveIcon />}
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Recording Feeding...' : `Record Feeding for ${tankEntries.length} Tank(s)`}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}

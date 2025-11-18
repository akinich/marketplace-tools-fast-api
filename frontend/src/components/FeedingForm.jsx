/**
 * ============================================================================
 * Biofloc Operational Forms - Feeding Session
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-18
 *
 * Form for recording feeding sessions with inventory integration.
 * Supports multiple feed items per session.
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';
import { inventoryAPI } from '../api';

export default function FeedingForm({ onSuccess }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    tank_id: null,
    feeding_date: new Date().toISOString().split('T')[0],
    session_number: 1,
    feed_time: new Date().toTimeString().slice(0, 5),
    notes: '',
  });

  const [feedItems, setFeedItems] = useState([
    { sku: '', quantity_kg: '', notes: '' }
  ]);

  // Fetch tanks with active batches
  const { data: tanksData, isLoading: tanksLoading } = useQuery(
    'bioflocTanksActive',
    () => bioflocAPI.getTanks({ status: 'in_use' })
  );

  // Fetch inventory items (feed category)
  const { data: inventoryData, isLoading: inventoryLoading } = useQuery(
    'inventoryFeedItems',
    () => inventoryAPI.getItems({ category: 'Feed', is_active: true })
  );

  // Submit mutation
  const mutation = useMutation(
    (data) => bioflocAPI.recordFeeding(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bioflocFeedingSessions');
        queryClient.invalidateQueries('bioflocBatches');
        if (onSuccess) onSuccess();
        // Reset form
        setFormData({
          tank_id: null,
          feeding_date: new Date().toISOString().split('T')[0],
          session_number: 1,
          feed_time: new Date().toTimeString().slice(0, 5),
          notes: '',
        });
        setFeedItems([{ sku: '', quantity_kg: '', notes: '' }]);
      },
    }
  );

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleTankChange = (event, value) => {
    setFormData({ ...formData, tank_id: value?.id || null });
  };

  const handleFeedItemChange = (index, field, value) => {
    const newItems = [...feedItems];
    newItems[index][field] = value;
    setFeedItems(newItems);
  };

  const addFeedItem = () => {
    setFeedItems([...feedItems, { sku: '', quantity_kg: '', notes: '' }]);
  };

  const removeFeedItem = (index) => {
    if (feedItems.length > 1) {
      const newItems = feedItems.filter((_, i) => i !== index);
      setFeedItems(newItems);
    }
  };

  const handleSubmit = () => {
    // Validate
    if (!formData.tank_id) {
      alert('Please select a tank');
      return;
    }

    const validItems = feedItems.filter(item => item.sku && item.quantity_kg > 0);
    if (validItems.length === 0) {
      alert('Please add at least one feed item');
      return;
    }

    // Submit
    mutation.mutate({
      ...formData,
      feed_items: validItems.map(item => ({
        sku: item.sku,
        quantity_kg: parseFloat(item.quantity_kg),
        notes: item.notes || undefined,
      })),
    });
  };

  const tanks = tanksData?.tanks || [];
  const feedOptions = inventoryData?.items || [];

  const totalFeed = feedItems.reduce((sum, item) =>
    sum + (parseFloat(item.quantity_kg) || 0), 0
  );

  if (tanksLoading || inventoryLoading) {
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
          Record Feeding Session
        </Typography>

        {mutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to record feeding: {mutation.error.message}
          </Alert>
        )}

        {mutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Feeding session recorded successfully!
          </Alert>
        )}

        <Grid container spacing={2}>
          {/* Tank Selection */}
          <Grid item xs={12} md={6}>
            <Autocomplete
              options={tanks}
              getOptionLabel={(option) => `${option.tank_name} (${option.tank_code}) - Batch: ${option.current_batch_code || 'None'}`}
              onChange={handleTankChange}
              renderInput={(params) => (
                <TextField {...params} label="Select Tank" required />
              )}
            />
          </Grid>

          {/* Date */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Feeding Date"
              type="date"
              value={formData.feeding_date}
              onChange={handleChange('feeding_date')}
              required
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Session Number */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Session Number"
              type="number"
              value={formData.session_number}
              onChange={handleChange('session_number')}
              required
              fullWidth
              helperText="e.g., 1 for first feeding of the day"
            />
          </Grid>

          {/* Feed Time */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Feed Time"
              type="time"
              value={formData.feed_time}
              onChange={handleChange('feed_time')}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Feed Items Section */}
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">
                Feed Items
              </Typography>
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={addFeedItem}
                variant="outlined"
              >
                Add Item
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Feed Type (SKU)</TableCell>
                    <TableCell>Quantity (kg)</TableCell>
                    <TableCell>Notes</TableCell>
                    <TableCell width={50}></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {feedItems.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Autocomplete
                          options={feedOptions}
                          getOptionLabel={(option) => `${option.item_name} (${option.sku}) - Available: ${option.current_qty} ${option.unit}`}
                          onChange={(e, value) => handleFeedItemChange(index, 'sku', value?.sku || '')}
                          renderInput={(params) => (
                            <TextField {...params} size="small" placeholder="Select feed" />
                          )}
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          type="number"
                          value={item.quantity_kg}
                          onChange={(e) => handleFeedItemChange(index, 'quantity_kg', e.target.value)}
                          size="small"
                          inputProps={{ step: "0.01", min: "0" }}
                          fullWidth
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          value={item.notes}
                          onChange={(e) => handleFeedItemChange(index, 'notes', e.target.value)}
                          size="small"
                          fullWidth
                          placeholder="Optional notes"
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => removeFeedItem(index)}
                          disabled={feedItems.length === 1}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Box sx={{ mt: 2, textAlign: 'right' }}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Feed: <strong>{totalFeed.toFixed(2)} kg</strong>
              </Typography>
            </Box>
          </Grid>

          {/* Notes */}
          <Grid item xs={12}>
            <TextField
              label="Session Notes"
              value={formData.notes}
              onChange={handleChange('notes')}
              multiline
              rows={2}
              fullWidth
              placeholder="Any additional notes about this feeding session"
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
              {mutation.isLoading ? 'Recording...' : 'Record Feeding Session'}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

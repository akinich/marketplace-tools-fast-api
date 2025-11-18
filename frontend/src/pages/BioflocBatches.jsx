/**
 * ============================================================================
 * Biofloc Batches Management Page
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-18
 *
 * Batch management page with lifecycle tracking and performance metrics.
 * ============================================================================
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  CheckCircle as ActiveIcon,
  Done as CompletedIcon,
  Cancel as TerminatedIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';

// Batch Card Component
const BatchCard = ({ batch, onView }) => {
  const statusColor = {
    active: '#4caf50',
    harvested: '#2196f3',
    terminated: '#f44336',
  }[batch.status] || '#9e9e9e';

  const statusIcon = {
    active: <ActiveIcon />,
    harvested: <CompletedIcon />,
    terminated: <TerminatedIcon />,
  }[batch.status] || <ActiveIcon />;

  const survivalRate = batch.survival_rate || (batch.current_count / batch.initial_count * 100);
  const cycleDays = batch.cycle_duration_days ||
    Math.floor((new Date() - new Date(batch.stocking_date)) / (1000 * 60 * 60 * 24));

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" fontWeight="bold">
              {batch.batch_code}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {batch.species}
            </Typography>
          </Box>
          <Chip
            icon={statusIcon}
            label={batch.status.toUpperCase()}
            size="small"
            sx={{
              backgroundColor: statusColor,
              color: 'white',
              fontWeight: 'bold',
            }}
          />
        </Box>

        {/* Key Metrics */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 2 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">Fish Count</Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2">
                {batch.current_count?.toLocaleString()} / {batch.initial_count?.toLocaleString()}
              </Typography>
              <Typography variant="body2" fontWeight="bold" color={survivalRate > 90 ? 'success.main' : survivalRate > 70 ? 'warning.main' : 'error.main'}>
                {survivalRate.toFixed(1)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={Math.min(survivalRate, 100)}
              sx={{
                mt: 0.5,
                height: 6,
                borderRadius: 3,
                backgroundColor: '#e0e0e0',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: survivalRate > 90 ? '#4caf50' : survivalRate > 70 ? '#ff9800' : '#f44336',
                },
              }}
            />
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">Cycle Days:</Typography>
            <Typography variant="body2" fontWeight="bold">{cycleDays}</Typography>
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">Avg Weight:</Typography>
            <Typography variant="body2" fontWeight="bold">
              {batch.current_avg_weight_g?.toFixed(2) || batch.initial_avg_weight_g?.toFixed(2)} g
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">Total Biomass:</Typography>
            <Typography variant="body2" fontWeight="bold">
              {batch.current_total_biomass_kg?.toFixed(1) || batch.initial_total_biomass_kg?.toFixed(1)} kg
            </Typography>
          </Box>

          {batch.fcr && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">FCR:</Typography>
              <Chip label={batch.fcr.toFixed(2)} size="small" color={batch.fcr < 1.5 ? 'success' : 'warning'} />
            </Box>
          )}

          {batch.current_tank_name && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">Tank:</Typography>
              <Chip label={batch.current_tank_name} size="small" variant="outlined" />
            </Box>
          )}
        </Box>
      </CardContent>
      <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
        <Button size="small" startIcon={<ViewIcon />} onClick={() => onView(batch)}>
          View Details
        </Button>
      </CardActions>
    </Card>
  );
};

// Batch Form Dialog
const BatchFormDialog = ({ open, onClose, onSave, tanks }) => {
  const [formData, setFormData] = useState({
    batch_code: '',
    species: '',
    source: '',
    stocking_date: new Date().toISOString().split('T')[0],
    initial_count: '',
    initial_avg_weight_g: '',
    tank_id: '',
    notes: '',
  });

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleSubmit = () => {
    onSave(formData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Batch</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField
            label="Batch Code"
            value={formData.batch_code}
            onChange={handleChange('batch_code')}
            required
            fullWidth
            helperText="Unique identifier (e.g., B2025001)"
          />
          <TextField
            label="Species"
            value={formData.species}
            onChange={handleChange('species')}
            required
            fullWidth
            placeholder="e.g., Nile Tilapia, Catfish"
          />
          <TextField
            label="Source"
            value={formData.source}
            onChange={handleChange('source')}
            fullWidth
            placeholder="Hatchery or supplier name"
          />
          <TextField
            label="Stocking Date"
            type="date"
            value={formData.stocking_date}
            onChange={handleChange('stocking_date')}
            required
            fullWidth
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="Initial Fish Count"
            type="number"
            value={formData.initial_count}
            onChange={handleChange('initial_count')}
            required
            fullWidth
          />
          <TextField
            label="Initial Average Weight (grams)"
            type="number"
            value={formData.initial_avg_weight_g}
            onChange={handleChange('initial_avg_weight_g')}
            required
            fullWidth
            inputProps={{ step: "0.01" }}
          />
          <FormControl fullWidth required>
            <InputLabel>Initial Tank Assignment</InputLabel>
            <Select
              value={formData.tank_id}
              onChange={handleChange('tank_id')}
              label="Initial Tank Assignment"
            >
              {tanks?.filter(t => t.status === 'available').map((tank) => (
                <MenuItem key={tank.id} value={tank.id}>
                  {tank.tank_name} ({tank.tank_code}) - {tank.capacity_liters}L
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="Notes"
            value={formData.notes}
            onChange={handleChange('notes')}
            multiline
            rows={3}
            fullWidth
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained">
          Create Batch
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Main Component
export default function BioflocBatches() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('active');

  // Fetch batches
  const { data, isLoading, error } = useQuery(
    ['bioflocBatches', statusFilter],
    () => bioflocAPI.getBatches({ status: statusFilter, limit: 100 }),
    {
      refetchInterval: 30000,
    }
  );

  // Fetch available tanks for batch creation
  const { data: tanksData } = useQuery(
    'bioflocTanksAvailable',
    () => bioflocAPI.getTanks({ status: 'available' })
  );

  // Create mutation
  const createMutation = useMutation(
    (batchData) => bioflocAPI.createBatch(batchData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bioflocBatches');
        queryClient.invalidateQueries('bioflocTanks');
        setDialogOpen(false);
      },
    }
  );

  const handleCreate = () => {
    setDialogOpen(true);
  };

  const handleSave = (batchData) => {
    createMutation.mutate(batchData);
  };

  const handleView = (batch) => {
    navigate(`/biofloc/batches/${batch.id}`);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load batches: {error.message}
      </Alert>
    );
  }

  const batches = data?.batches || [];

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Batch Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Track fish batches from stocking to harvest
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          New Batch
        </Button>
      </Box>

      {/* Filters */}
      <Box sx={{ mb: 3 }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Status Filter</InputLabel>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            label="Status Filter"
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="harvested">Harvested</MenuItem>
            <MenuItem value="terminated">Terminated</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Statistics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">Total Batches</Typography>
              <Typography variant="h4" fontWeight="bold">{batches.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">Total Fish</Typography>
              <Typography variant="h4" fontWeight="bold">
                {batches.reduce((sum, b) => sum + (b.current_count || 0), 0).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">Total Biomass</Typography>
              <Typography variant="h4" fontWeight="bold">
                {batches.reduce((sum, b) => sum + (b.current_total_biomass_kg || 0), 0).toFixed(1)} kg
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">Avg Survival</Typography>
              <Typography variant="h4" fontWeight="bold" color="success.main">
                {batches.length > 0
                  ? (batches.reduce((sum, b) => sum + (b.current_count / b.initial_count * 100), 0) / batches.length).toFixed(1)
                  : 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Batch Grid */}
      <Grid container spacing={3}>
        {batches.map((batch) => (
          <Grid item xs={12} sm={6} md={4} key={batch.id}>
            <BatchCard
              batch={batch}
              onView={handleView}
            />
          </Grid>
        ))}
      </Grid>

      {batches.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No {statusFilter} batches found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {statusFilter === 'active'
              ? 'Create your first batch to start tracking fish production'
              : 'Change the filter to see other batches'}
          </Typography>
          {statusFilter === 'active' && (
            <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
              Create First Batch
            </Button>
          )}
        </Box>
      )}

      {/* Batch Form Dialog */}
      <BatchFormDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={handleSave}
        tanks={tanksData?.tanks || []}
      />
    </Box>
  );
}

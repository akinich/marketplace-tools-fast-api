/**
 * ============================================================================
 * Biofloc Tanks Management Page
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-18
 *
 * Tank management page with list, create, edit, and detail views.
 * ============================================================================
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
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
  Edit as EditIcon,
  Delete as DeleteIcon,
  Pool as TankIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon,
  Build as MaintenanceIcon,
} from '@mui/icons-material';

import { bioflocAPI } from '../api';

// Tank Card Component
const TankCard = ({ tank, onEdit, onDelete }) => {
  const statusColor = {
    available: '#4caf50',
    in_use: '#2196f3',
    maintenance: '#ff9800',
    decommissioned: '#f44336',
  }[tank.status] || '#9e9e9e';

  const statusIcon = {
    available: <ActiveIcon />,
    in_use: <TankIcon />,
    maintenance: <MaintenanceIcon />,
    decommissioned: <InactiveIcon />,
  }[tank.status] || <TankIcon />;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" fontWeight="bold">
              {tank.tank_name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Code: {tank.tank_code}
            </Typography>
          </Box>
          <Chip
            icon={statusIcon}
            label={tank.status.replace('_', ' ').toUpperCase()}
            size="small"
            sx={{
              backgroundColor: statusColor,
              color: 'white',
              fontWeight: 'bold',
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">Capacity:</Typography>
            <Typography variant="body2" fontWeight="bold">
              {tank.capacity_liters?.toLocaleString()} L
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">Type:</Typography>
            <Typography variant="body2">{tank.tank_type}</Typography>
          </Box>
          {tank.location && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">Location:</Typography>
              <Typography variant="body2">{tank.location}</Typography>
            </Box>
          )}
          {tank.current_batch_code && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">Current Batch:</Typography>
              <Chip label={tank.current_batch_code} size="small" color="primary" />
            </Box>
          )}
        </Box>
      </CardContent>
      <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
        <IconButton size="small" color="primary" onClick={() => onEdit(tank)}>
          <EditIcon />
        </IconButton>
        <IconButton size="small" color="error" onClick={() => onDelete(tank)}>
          <DeleteIcon />
        </IconButton>
      </CardActions>
    </Card>
  );
};

// Tank Form Dialog
const TankFormDialog = ({ open, onClose, tank, onSave, isSubmitting, error }) => {
  const [formData, setFormData] = useState(tank || {
    tank_name: '',
    tank_code: '',
    capacity_liters: '',
    location: '',
    tank_type: 'circular',
    status: 'available',
    notes: '',
  });
  const [validationErrors, setValidationErrors] = useState({});

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors({ ...validationErrors, [field]: null });
    }
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.tank_name?.trim()) {
      errors.tank_name = 'Tank name is required';
    }

    if (!formData.tank_code?.trim()) {
      errors.tank_code = 'Tank code is required';
    }

    if (!formData.capacity_liters || formData.capacity_liters <= 0) {
      errors.capacity_liters = 'Valid capacity is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = () => {
    if (!validateForm()) {
      return;
    }

    // Convert capacity to number and prepare data
    const submitData = {
      ...formData,
      capacity_liters: parseFloat(formData.capacity_liters),
    };

    onSave(submitData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{tank ? 'Edit Tank' : 'Create New Tank'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 1 }}>
              {error.response?.data?.detail || error.message || 'Failed to save tank'}
            </Alert>
          )}
          <TextField
            label="Tank Name"
            value={formData.tank_name}
            onChange={handleChange('tank_name')}
            required
            fullWidth
            error={!!validationErrors.tank_name}
            helperText={validationErrors.tank_name}
          />
          <TextField
            label="Tank Code"
            value={formData.tank_code}
            onChange={handleChange('tank_code')}
            required
            fullWidth
            disabled={!!tank}
            error={!!validationErrors.tank_code}
            helperText={validationErrors.tank_code || "Unique identifier (cannot be changed after creation)"}
          />
          <TextField
            label="Capacity (Liters)"
            type="number"
            value={formData.capacity_liters}
            onChange={handleChange('capacity_liters')}
            required
            fullWidth
            error={!!validationErrors.capacity_liters}
            helperText={validationErrors.capacity_liters}
          />
          <TextField
            label="Location"
            value={formData.location}
            onChange={handleChange('location')}
            fullWidth
          />
          <FormControl fullWidth>
            <InputLabel>Tank Type</InputLabel>
            <Select
              value={formData.tank_type}
              onChange={handleChange('tank_type')}
              label="Tank Type"
            >
              <MenuItem value="circular">Circular</MenuItem>
              <MenuItem value="rectangular">Rectangular</MenuItem>
              <MenuItem value="raceway">Raceway</MenuItem>
            </Select>
          </FormControl>
          {tank && (
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                onChange={handleChange('status')}
                label="Status"
              >
                <MenuItem value="available">Available</MenuItem>
                <MenuItem value="in_use">In Use</MenuItem>
                <MenuItem value="maintenance">Maintenance</MenuItem>
                <MenuItem value="decommissioned">Decommissioned</MenuItem>
              </Select>
            </FormControl>
          )}
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
        <Button onClick={onClose} disabled={isSubmitting}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <CircularProgress size={20} sx={{ mr: 1 }} />
              {tank ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            tank ? 'Update' : 'Create'
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Main Component
export default function BioflocTanks() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTank, setSelectedTank] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // grid or table

  // Fetch tanks
  const { data, isLoading, error } = useQuery(
    'bioflocTanks',
    () => bioflocAPI.getTanks({ limit: 100 }),
    {
      refetchInterval: 30000,
    }
  );

  // Create/Update mutation
  const saveMutation = useMutation(
    (tankData) => {
      if (selectedTank) {
        return bioflocAPI.updateTank(selectedTank.id, tankData);
      } else {
        return bioflocAPI.createTank(tankData);
      }
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bioflocTanks');
        setDialogOpen(false);
        setSelectedTank(null);
      },
      onError: (error) => {
        console.error('Failed to save tank:', error);
        // Error will be displayed in the dialog
      },
    }
  );

  // Delete mutation
  const deleteMutation = useMutation(
    (tankId) => bioflocAPI.deleteTank(tankId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bioflocTanks');
      },
    }
  );

  const handleCreate = () => {
    setSelectedTank(null);
    setDialogOpen(true);
  };

  const handleEdit = (tank) => {
    setSelectedTank(tank);
    setDialogOpen(true);
  };

  const handleDelete = (tank) => {
    if (window.confirm(`Are you sure you want to delete tank "${tank.tank_name}"?`)) {
      deleteMutation.mutate(tank.id);
    }
  };

  const handleSave = (tankData) => {
    saveMutation.mutate(tankData);
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
        Failed to load tanks: {error.message}
      </Alert>
    );
  }

  const tanks = data?.tanks || [];

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Tank Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your aquaculture tanks and their assignments
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          New Tank
        </Button>
      </Box>

      {/* Statistics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">Total Tanks</Typography>
              <Typography variant="h4" fontWeight="bold">{tanks.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">Available</Typography>
              <Typography variant="h4" fontWeight="bold" color="success.main">
                {tanks.filter(t => t.status === 'available').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">In Use</Typography>
              <Typography variant="h4" fontWeight="bold" color="primary.main">
                {tanks.filter(t => t.status === 'in_use').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">Maintenance</Typography>
              <Typography variant="h4" fontWeight="bold" color="warning.main">
                {tanks.filter(t => t.status === 'maintenance').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tank Grid */}
      <Grid container spacing={3}>
        {tanks.map((tank) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={tank.id}>
            <TankCard
              tank={tank}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          </Grid>
        ))}
      </Grid>

      {tanks.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <TankIcon sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No tanks yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first tank to get started with biofloc management
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
            Create First Tank
          </Button>
        </Box>
      )}

      {/* Tank Form Dialog */}
      <TankFormDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setSelectedTank(null);
          saveMutation.reset(); // Clear any errors
        }}
        tank={selectedTank}
        onSave={handleSave}
        isSubmitting={saveMutation.isLoading}
        error={saveMutation.error}
      />
    </Box>
  );
}

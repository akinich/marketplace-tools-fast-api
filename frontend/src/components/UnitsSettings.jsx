/**
 * Units of Measurement Settings
 * Version: 1.1.0
 * Last Updated: 2025-11-22
 *
 * Changelog:
 * ----------
 * v1.1.0 (2025-11-22):
 *   - Added both Deactivate and Delete buttons for unused units
 *   - Admin can now choose between deactivating or permanently deleting units with no items
 *   - Units in use still show only Deactivate button (cannot delete)
 *
 * v1.0.0 (2025-11-22):
 *   - Initial release - manage standardized units for inventory items
 *   - Full CRUD operations with smart delete logic
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ToggleOff as DeactivateIcon,
  ToggleOn as ActivateIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useSnackbar } from 'notistack';
import { unitsAPI } from '../api';

// Unit categories for dropdown
const UNIT_CATEGORIES = [
  'weight',
  'volume',
  'count',
  'length',
  'area',
  'other',
];

// Create/Edit Unit Dialog
function UnitDialog({ open, onClose, unit = null }) {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const isEdit = !!unit;

  const [formData, setFormData] = useState({
    unit_name: unit?.unit_name || '',
    abbreviation: unit?.abbreviation || '',
    category: unit?.category || '',
  });

  const [errors, setErrors] = useState({});

  const mutation = useMutation(
    (data) => {
      if (isEdit) {
        return unitsAPI.updateUnit(unit.id, data);
      } else {
        return unitsAPI.createUnit(data);
      }
    },
    {
      onSuccess: () => {
        enqueueSnackbar(
          `Unit ${isEdit ? 'updated' : 'created'} successfully`,
          { variant: 'success' }
        );
        queryClient.invalidateQueries('units');
        onClose();
      },
      onError: (error) => {
        enqueueSnackbar(
          error.response?.data?.detail || `Failed to ${isEdit ? 'update' : 'create'} unit`,
          { variant: 'error' }
        );
      },
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validation
    const newErrors = {};
    if (!formData.unit_name.trim()) {
      newErrors.unit_name = 'Unit name is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    mutation.mutate({
      unit_name: formData.unit_name.trim(),
      abbreviation: formData.abbreviation.trim() || null,
      category: formData.category || null,
    });
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{isEdit ? 'Edit Unit' : 'Create New Unit'}</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Unit Name"
              required
              fullWidth
              value={formData.unit_name}
              onChange={(e) => setFormData({ ...formData, unit_name: e.target.value })}
              error={!!errors.unit_name}
              helperText={errors.unit_name || 'Full name (e.g., Kilogram, Liter)'}
            />

            <TextField
              label="Abbreviation"
              fullWidth
              value={formData.abbreviation}
              onChange={(e) => setFormData({ ...formData, abbreviation: e.target.value })}
              helperText="Short form (e.g., kg, L)"
              inputProps={{ maxLength: 10 }}
            />

            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                label="Category"
              >
                <MenuItem value="">
                  <em>None</em>
                </MenuItem>
                {UNIT_CATEGORIES.map((cat) => (
                  <MenuItem key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={mutation.isLoading}
          >
            {mutation.isLoading ? 'Saving...' : isEdit ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

export default function UnitsSettings() {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState(null);

  // Fetch units
  const { data: unitsData, isLoading, error } = useQuery(
    'units',
    () => unitsAPI.getUnits({ include_inactive: true })
  );

  // Delete mutation
  const deleteMutation = useMutation(
    (unitId) => unitsAPI.deleteUnit(unitId),
    {
      onSuccess: () => {
        enqueueSnackbar('Unit deleted successfully', { variant: 'success' });
        queryClient.invalidateQueries('units');
      },
      onError: (error) => {
        enqueueSnackbar(
          error.response?.data?.detail || 'Failed to delete unit',
          { variant: 'error' }
        );
      },
    }
  );

  // Deactivate mutation
  const deactivateMutation = useMutation(
    (unitId) => unitsAPI.deactivateUnit(unitId),
    {
      onSuccess: () => {
        enqueueSnackbar('Unit deactivated successfully', { variant: 'success' });
        queryClient.invalidateQueries('units');
      },
      onError: (error) => {
        enqueueSnackbar(
          error.response?.data?.detail || 'Failed to deactivate unit',
          { variant: 'error' }
        );
      },
    }
  );

  // Reactivate mutation
  const reactivateMutation = useMutation(
    (unitId) => unitsAPI.reactivateUnit(unitId),
    {
      onSuccess: () => {
        enqueueSnackbar('Unit reactivated successfully', { variant: 'success' });
        queryClient.invalidateQueries('units');
      },
      onError: (error) => {
        enqueueSnackbar(
          error.response?.data?.detail || 'Failed to reactivate unit',
          { variant: 'error' }
        );
      },
    }
  );

  const handleCreate = () => {
    setSelectedUnit(null);
    setDialogOpen(true);
  };

  const handleEdit = (unit) => {
    setSelectedUnit(unit);
    setDialogOpen(true);
  };

  const handleDelete = (unit) => {
    if (unit.item_count > 0) {
      enqueueSnackbar(
        `Cannot delete "${unit.unit_name}" - used by ${unit.item_count} item(s). Deactivate instead.`,
        { variant: 'warning' }
      );
      return;
    }

    if (window.confirm(`Are you sure you want to permanently delete "${unit.unit_name}"?`)) {
      deleteMutation.mutate(unit.id);
    }
  };

  const handleToggleActive = (unit) => {
    if (unit.is_active) {
      if (window.confirm(`Deactivate "${unit.unit_name}"? It will be hidden from dropdowns but items using it will remain unchanged.`)) {
        deactivateMutation.mutate(unit.id);
      }
    } else {
      reactivateMutation.mutate(unit.id);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load units: {error.message}
      </Alert>
    );
  }

  const units = unitsData?.units || [];
  const activeUnits = units.filter((u) => u.is_active);
  const inactiveUnits = units.filter((u) => !u.is_active);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Units of Measurement</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          Add Unit
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>Note:</strong> Units linked to items can only be deactivated, not deleted.
        Unused units can be permanently deleted.
      </Alert>

      {/* Active Units */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Active Units ({activeUnits.length})
      </Typography>

      <TableContainer component={Paper} sx={{ mb: 4 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Unit Name</TableCell>
              <TableCell>Abbreviation</TableCell>
              <TableCell>Category</TableCell>
              <TableCell align="center">Items Using</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {activeUnits.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No active units
                </TableCell>
              </TableRow>
            ) : (
              activeUnits.map((unit) => (
                <TableRow key={unit.id}>
                  <TableCell>{unit.unit_name}</TableCell>
                  <TableCell>{unit.abbreviation || '-'}</TableCell>
                  <TableCell>
                    {unit.category ? (
                      <Chip
                        label={unit.category}
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell align="center">
                    {unit.item_count > 0 ? (
                      <Chip label={unit.item_count} size="small" color="primary" />
                    ) : (
                      <Chip label="0" size="small" />
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <Chip label="Active" size="small" color="success" />
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => handleEdit(unit)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={unit.item_count > 0 ? "Deactivate (in use - cannot delete)" : "Deactivate"}>
                      <IconButton
                        size="small"
                        onClick={() => handleToggleActive(unit)}
                      >
                        <DeactivateIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {unit.item_count === 0 && (
                      <Tooltip title="Delete (permanent)">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(unit)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Inactive Units */}
      {inactiveUnits.length > 0 && (
        <>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Inactive Units ({inactiveUnits.length})
          </Typography>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Unit Name</TableCell>
                  <TableCell>Abbreviation</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell align="center">Items Using</TableCell>
                  <TableCell align="center">Status</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {inactiveUnits.map((unit) => (
                  <TableRow key={unit.id} sx={{ bgcolor: 'action.hover' }}>
                    <TableCell>{unit.unit_name}</TableCell>
                    <TableCell>{unit.abbreviation || '-'}</TableCell>
                    <TableCell>
                      {unit.category ? (
                        <Chip label={unit.category} size="small" variant="outlined" />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell align="center">
                      {unit.item_count > 0 ? (
                        <Chip label={unit.item_count} size="small" />
                      ) : (
                        <Chip label="0" size="small" />
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Inactive" size="small" />
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="Reactivate">
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => handleToggleActive(unit)}
                        >
                          <ActivateIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {unit.item_count === 0 && (
                        <Tooltip title="Delete (permanent)">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete(unit)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}

      {/* Dialog */}
      <UnitDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setSelectedUnit(null);
        }}
        unit={selectedUnit}
      />
    </Box>
  );
}

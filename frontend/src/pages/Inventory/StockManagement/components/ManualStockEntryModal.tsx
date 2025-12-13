/**
 * Manual Stock Entry Modal
 * Version: 1.0.0
 * Created: 2024-12-12
 *
 * Simple form for manual stock entry (temporary, for testing)
 */

import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Box,
    Typography,
    Autocomplete,
} from '@mui/material';
import { useSnackbar } from 'notistack';
import { inventoryAPI, ManualStockEntryRequest } from '../../../../api/inventory';
import { zohoItemAPI } from '../../../../api/zohoItem';
import batchTrackingAPI from '../../../../api/batchTracking';

interface Props {
    open: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

const ManualStockEntryModal: React.FC<Props> = ({ open, onClose, onSuccess }) => {
    const { enqueueSnackbar } = useSnackbar();

    const [loading, setLoading] = useState(false);
    const [items, setItems] = useState<any[]>([]);
    const [batches, setBatches] = useState<any[]>([]);
    const [formData, setFormData] = useState<ManualStockEntryRequest>({
        item_id: 0,
        batch_id: 0,
        location: 'packed_warehouse',
        quantity: 0,
        grade: '',
        shelf_life_days: 7,
    });

    // Location options
    const locations = [
        { value: 'receiving_area', label: 'Receiving Area' },
        { value: 'processing_area', label: 'Processing Area' },
        { value: 'packed_warehouse', label: 'Packed Warehouse' },
        { value: 'delivery_vehicles', label: 'Delivery Vehicles' },
        { value: 'quality_hold', label: 'Quality Hold' },
    ];

    // Load items and batches
    useEffect(() => {
        const loadDropdownData = async () => {
            try {
                const [itemsRes, batchesRes] = await Promise.all([
                    zohoItemAPI.getItems({ page: 1, limit: 1000 }),
                    batchTrackingAPI.getActiveBatches({ limit: 100 })
                ]);
                setItems(itemsRes || []);
                setBatches(batchesRes.batches || []);
            } catch (error) {
                console.error('Failed to load dropdown data:', error);
                enqueueSnackbar('Failed to load items/batches', { variant: 'error' });
            }
        };

        if (open) {
            loadDropdownData();
        }
    }, [open, enqueueSnackbar]);

    const handleSubmit = async () => {
        // Validation
        if (!formData.item_id) {
            enqueueSnackbar('Please select an item', { variant: 'warning' });
            return;
        }
        if (!formData.batch_id) {
            enqueueSnackbar('Please select a batch', { variant: 'warning' });
            return;
        }
        if (formData.quantity <= 0) {
            enqueueSnackbar('Quantity must be greater than 0', { variant: 'warning' });
            return;
        }

        setLoading(true);
        try {
            await inventoryAPI.addStock(formData);
            enqueueSnackbar('Stock added successfully', { variant: 'success' });
            onSuccess();
            handleClose();
        } catch (error: any) {
            console.error('Failed to add stock:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to add stock', {
                variant: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setFormData({
            item_id: 0,
            batch_id: 0,
            location: 'packed_warehouse',
            quantity: 0,
            grade: '',
            shelf_life_days: 7,
        });
        onClose();
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <DialogTitle>
                <Typography variant="h6">Add Stock Entry</Typography>
                <Typography variant="caption" color="text.secondary">
                    Manual stock entry for testing purposes
                </Typography>
            </DialogTitle>

            <DialogContent>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                    {/* Item Selection */}
                    <Autocomplete
                        options={items}
                        getOptionLabel={(option) => `${option.name} (${option.sku})`}
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                label="Item *"
                                placeholder="Search for item..."
                            />
                        )}
                        onChange={(_, value) => {
                            setFormData({ ...formData, item_id: value?.id || 0 });
                        }}
                        isOptionEqualToValue={(option, value) => option.id === value.id}
                    />

                    {/* Batch Selection */}
                    <Autocomplete
                        options={batches}
                        getOptionLabel={(option) => `${option.batch_number} - ${option.status}`}
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                label="Batch *"
                                placeholder="Search for batch..."
                            />
                        )}
                        onChange={(_, value) => {
                            setFormData({ ...formData, batch_id: value?.batch_id || 0 });
                        }}
                        isOptionEqualToValue={(option, value) => option.batch_id === value.batch_id}
                    />

                    {/* Location */}
                    <FormControl fullWidth>
                        <InputLabel>Location *</InputLabel>
                        <Select
                            value={formData.location}
                            label="Location *"
                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                        >
                            {locations.map((loc) => (
                                <MenuItem key={loc.value} value={loc.value}>
                                    {loc.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    {/* Quantity */}
                    <TextField
                        label="Quantity *"
                        type="number"
                        value={formData.quantity || ''}
                        onChange={(e) => setFormData({ ...formData, quantity: parseFloat(e.target.value) || 0 })}
                        inputProps={{ min: 0, step: 0.01 }}
                        fullWidth
                    />

                    {/* Grade */}
                    <FormControl fullWidth>
                        <InputLabel>Grade (Optional)</InputLabel>
                        <Select
                            value={formData.grade || ''}
                            label="Grade (Optional)"
                            onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                        >
                            <MenuItem value="">None</MenuItem>
                            <MenuItem value="A">Grade A</MenuItem>
                            <MenuItem value="B">Grade B</MenuItem>
                            <MenuItem value="C">Grade C</MenuItem>
                        </Select>
                    </FormControl>

                    {/* Shelf Life */}
                    <TextField
                        label="Shelf Life (Days)"
                        type="number"
                        value={formData.shelf_life_days || ''}
                        onChange={(e) => setFormData({ ...formData, shelf_life_days: parseInt(e.target.value) || 0 })}
                        inputProps={{ min: 0 }}
                        helperText="Number of days until expiry"
                        fullWidth
                    />
                </Box>
            </DialogContent>

            <DialogActions>
                <Button onClick={handleClose} disabled={loading}>
                    Cancel
                </Button>
                <Button
                    onClick={handleSubmit}
                    variant="contained"
                    disabled={loading}
                >
                    {loading ? 'Adding...' : 'Add Stock'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default ManualStockEntryModal;

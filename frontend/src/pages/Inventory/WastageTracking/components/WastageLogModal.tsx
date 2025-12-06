/**
 * ================================================================================
 * Wastage Log Modal Component
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Reusable modal for logging wastage events. Can be embedded in other modules
 * (GRN, Grading, Packing) with pre-filled batch and stage.
 * ================================================================================
 */

import { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    MenuItem,
    Box,
    CircularProgress,
    Autocomplete,
} from '@mui/material';
import { useSnackbar } from 'notistack';
import {
    wastageTrackingAPI,
    LogWastageRequest,
    WastageStage,
    CostAllocation,
    WastageCategory,
} from '../../../../api/wastageTracking';
import { batchTrackingAPI } from '../../../../api/batchTracking';
import PhotoUpload from './PhotoUpload';
import CostAllocationToggle from './CostAllocationToggle';

interface WastageLogModalProps {
    open: boolean;
    onClose: () => void;
    onSuccess: () => void;
    batchNumber?: string;
    stage?: WastageStage | string;
}

export default function WastageLogModal({
    open,
    onClose,
    onSuccess,
    batchNumber: initialBatchNumber,
    stage: initialStage,
}: WastageLogModalProps) {
    const { enqueueSnackbar } = useSnackbar();
    const [loading, setLoading] = useState(false);
    const [photos, setPhotos] = useState<File[]>([]);
    const [categories, setCategories] = useState<WastageCategory[]>([]);
    const [batches, setBatches] = useState<string[]>([]);
    const [loadingBatches, setLoadingBatches] = useState(false);

    const [formData, setFormData] = useState({
        batchNumber: initialBatchNumber || '',
        stage: initialStage || '',
        wastageType: '',
        itemName: '',
        quantity: '',
        unit: 'kg',
        costAllocation: '' as CostAllocation | '',
        estimatedCost: '',
        reason: '',
        notes: '',
        location: '',
    });

    // Load categories when stage changes
    useEffect(() => {
        if (formData.stage) {
            loadCategories(formData.stage);
        }
    }, [formData.stage]);

    // Load batches for autocomplete
    useEffect(() => {
        if (open) {
            loadBatches();
        }
    }, [open]);

    // Reset form when dialog opens/closes
    useEffect(() => {
        if (!open) {
            setFormData({
                batchNumber: initialBatchNumber || '',
                stage: initialStage || '',
                wastageType: '',
                itemName: '',
                quantity: '',
                unit: 'kg',
                costAllocation: '' as CostAllocation | '',
                estimatedCost: '',
                reason: '',
                notes: '',
                location: '',
            });
            setPhotos([]);
        }
    }, [open, initialBatchNumber, initialStage]);

    const loadCategories = async (stage: string) => {
        try {
            const response = await wastageTrackingAPI.getCategories(stage);
            setCategories(response.categories);
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    };

    const loadBatches = async () => {
        setLoadingBatches(true);
        try {
            const response = await batchTrackingAPI.getActiveBatches({ limit: 100 });
            setBatches(response.batches.map((b) => b.batch_number));
        } catch (error) {
            console.error('Failed to load batches:', error);
        } finally {
            setLoadingBatches(false);
        }
    };

    const handleSubmit = async () => {
        // Validation
        if (!formData.batchNumber) {
            enqueueSnackbar('Batch number is required', { variant: 'error' });
            return;
        }
        if (!formData.stage) {
            enqueueSnackbar('Stage is required', { variant: 'error' });
            return;
        }
        if (!formData.wastageType) {
            enqueueSnackbar('Wastage type is required', { variant: 'error' });
            return;
        }
        if (!formData.itemName) {
            enqueueSnackbar('Item name is required', { variant: 'error' });
            return;
        }
        if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
            enqueueSnackbar('Quantity must be greater than 0', { variant: 'error' });
            return;
        }
        if (!formData.costAllocation) {
            enqueueSnackbar('Cost allocation is required', { variant: 'error' });
            return;
        }
        if (photos.length === 0) {
            enqueueSnackbar('At least 1 photo is required', { variant: 'error' });
            return;
        }

        setLoading(true);
        try {
            const request: LogWastageRequest = {
                batch_number: formData.batchNumber,
                stage: formData.stage,
                wastage_type: formData.wastageType,
                item_name: formData.itemName,
                quantity: parseFloat(formData.quantity),
                unit: formData.unit,
                cost_allocation: formData.costAllocation,
                estimated_cost: formData.estimatedCost ? parseFloat(formData.estimatedCost) : undefined,
                reason: formData.reason || undefined,
                notes: formData.notes || undefined,
                location: formData.location || undefined,
            };

            await wastageTrackingAPI.logWastage(request, photos);

            enqueueSnackbar('Wastage logged successfully', { variant: 'success' });
            onSuccess();
            onClose();
        } catch (error: any) {
            enqueueSnackbar(
                error.response?.data?.detail || 'Failed to log wastage',
                { variant: 'error' }
            );
        } finally {
            setLoading(false);
        }
    };

    // Get filtered wastage types based on stage
    const getWastageTypes = () => {
        const uniqueTypes = [...new Set(categories.map((c) => c.wastage_type))];
        return uniqueTypes;
    };

    // Get filtered reasons based on stage and type
    const getReasons = () => {
        return categories
            .filter((c) => !formData.wastageType || c.wastage_type === formData.wastageType)
            .map((c) => c.reason);
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>Log Wastage Event</DialogTitle>
            <DialogContent>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                    {/* Batch Number */}
                    <Autocomplete
                        options={batches}
                        value={formData.batchNumber}
                        onChange={(_, newValue) => setFormData({ ...formData, batchNumber: newValue || '' })}
                        loading={loadingBatches}
                        disabled={!!initialBatchNumber}
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                label="Batch Number"
                                required
                                helperText={initialBatchNumber ? 'Pre-filled from context' : 'Select or type batch number'}
                            />
                        )}
                        freeSolo
                    />

                    {/* Stage */}
                    <TextField
                        select
                        label="Stage"
                        value={formData.stage}
                        onChange={(e) => setFormData({ ...formData, stage: e.target.value, wastageType: '', reason: '' })}
                        disabled={!!initialStage}
                        required
                        fullWidth
                        helperText={initialStage ? 'Pre-filled from context' : undefined}
                    >
                        <MenuItem value={WastageStage.RECEIVING}>Receiving</MenuItem>
                        <MenuItem value={WastageStage.GRADING}>Grading</MenuItem>
                        <MenuItem value={WastageStage.PACKING}>Packing</MenuItem>
                        <MenuItem value={WastageStage.COLD_STORAGE}>Cold Storage</MenuItem>
                        <MenuItem value={WastageStage.CUSTOMER}>Customer</MenuItem>
                    </TextField>

                    {/* Wastage Type */}
                    <TextField
                        select
                        label="Wastage Type"
                        value={formData.wastageType}
                        onChange={(e) => setFormData({ ...formData, wastageType: e.target.value, reason: '' })}
                        required
                        fullWidth
                        disabled={!formData.stage}
                    >
                        {getWastageTypes().map((type) => (
                            <MenuItem key={type} value={type}>
                                {type.replace('_', ' ').toUpperCase()}
                            </MenuItem>
                        ))}
                    </TextField>

                    {/* Item Name & Quantity */}
                    <Box sx={{ display: 'flex', gap: 2 }}>
                        <TextField
                            label="Item Name"
                            value={formData.itemName}
                            onChange={(e) => setFormData({ ...formData, itemName: e.target.value })}
                            required
                            fullWidth
                        />
                        <TextField
                            label="Quantity"
                            type="number"
                            value={formData.quantity}
                            onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                            required
                            sx={{ width: '150px' }}
                            inputProps={{ min: 0, step: 0.01 }}
                        />
                        <TextField
                            label="Unit"
                            value={formData.unit}
                            onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                            required
                            sx={{ width: '100px' }}
                        />
                    </Box>

                    {/* Cost Allocation */}
                    <CostAllocationToggle
                        value={formData.costAllocation}
                        onChange={(value) => setFormData({ ...formData, costAllocation: value })}
                        defaultStage={formData.stage as WastageStage}
                    />

                    {/* Estimated Cost */}
                    <TextField
                        label="Estimated Cost (INR)"
                        type="number"
                        value={formData.estimatedCost}
                        onChange={(e) => setFormData({ ...formData, estimatedCost: e.target.value })}
                        helperText="Optional - estimated cost impact"
                        fullWidth
                        inputProps={{ min: 0, step: 0.01 }}
                    />

                    {/* Reason */}
                    <Autocomplete
                        options={getReasons()}
                        value={formData.reason}
                        onChange={(_, newValue) => setFormData({ ...formData, reason: newValue || '' })}
                        disabled={!formData.stage}
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                label="Reason"
                                helperText="Select from predefined reasons or type custom"
                            />
                        )}
                        freeSolo
                    />

                    {/* Location */}
                    <TextField
                        label="Location"
                        value={formData.location}
                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                        helperText="e.g., receiving_area, cold_storage, vehicle"
                        fullWidth
                    />

                    {/* Notes */}
                    <TextField
                        label="Notes"
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        helperText="Additional details about the wastage"
                        fullWidth
                        multiline
                        rows={2}
                    />

                    {/* Photo Upload */}
                    <PhotoUpload
                        onPhotosChange={setPhotos}
                        maxPhotos={10}
                        required
                    />
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose} disabled={loading}>
                    Cancel
                </Button>
                <Button
                    onClick={handleSubmit}
                    variant="contained"
                    disabled={loading}
                    startIcon={loading && <CircularProgress size={20} />}
                >
                    {loading ? 'Logging...' : 'Log Wastage'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

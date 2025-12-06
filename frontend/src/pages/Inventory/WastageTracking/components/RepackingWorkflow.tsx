/**
 * ================================================================================
 * Repacking Workflow Component
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Dialog component for repacking damaged items into new batches.
 * Creates new batch with R suffix and logs repacking event.
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
    Box,
    Typography,
    Alert,
    CircularProgress,
} from '@mui/material';
import { useSnackbar } from 'notistack';
import { wastageTrackingAPI, RepackRequest } from '../../../../api/wastageTracking';
import PhotoUpload from './PhotoUpload';

interface RepackingWorkflowProps {
    open: boolean;
    onClose: () => void;
    onSuccess: (newBatchNumber: string) => void;
    parentBatch: string;
    wastageEventId?: number;
}

export default function RepackingWorkflow({
    open,
    onClose,
    onSuccess,
    parentBatch,
    wastageEventId,
}: RepackingWorkflowProps) {
    const { enqueueSnackbar } = useSnackbar();
    const [loading, setLoading] = useState(false);
    const [photos, setPhotos] = useState<File[]>([]);

    const [formData, setFormData] = useState({
        damagedQuantity: '',
        repackedQuantity: '',
        reason: '',
        notes: '',
    });

    const [errors, setErrors] = useState({
        damagedQuantity: '',
        repackedQuantity: '',
        reason: '',
    });

    // Calculate wastage in repacking
    const wastageInRepacking = formData.damagedQuantity && formData.repackedQuantity
        ? parseFloat(formData.damagedQuantity) - parseFloat(formData.repackedQuantity)
        : 0;

    // Preview new batch number
    const newBatchNumber = parentBatch ? `${parentBatch}R` : '';

    // Reset form when dialog opens/closes
    useEffect(() => {
        if (!open) {
            setFormData({
                damagedQuantity: '',
                repackedQuantity: '',
                reason: '',
                notes: '',
            });
            setPhotos([]);
            setErrors({
                damagedQuantity: '',
                repackedQuantity: '',
                reason: '',
            });
        }
    }, [open]);

    // Validate form
    const validate = (): boolean => {
        const newErrors = {
            damagedQuantity: '',
            repackedQuantity: '',
            reason: '',
        };

        if (!formData.damagedQuantity || parseFloat(formData.damagedQuantity) <= 0) {
            newErrors.damagedQuantity = 'Damaged quantity is required and must be greater than 0';
        }

        if (!formData.repackedQuantity || parseFloat(formData.repackedQuantity) <= 0) {
            newErrors.repackedQuantity = 'Repacked quantity is required and must be greater than 0';
        }

        if (parseFloat(formData.repackedQuantity) > parseFloat(formData.damagedQuantity)) {
            newErrors.repackedQuantity = 'Repacked quantity cannot exceed damaged quantity';
        }

        if (!formData.reason.trim()) {
            newErrors.reason = 'Reason is required';
        }

        if (photos.length === 0) {
            enqueueSnackbar('At least 1 photo is required', { variant: 'error' });
            setErrors(newErrors);
            return false;
        }

        setErrors(newErrors);
        return !Object.values(newErrors).some((error) => error !== '');
    };

    // Handle submit
    const handleSubmit = async () => {
        if (!validate()) return;

        setLoading(true);
        try {
            const request: RepackRequest = {
                parent_batch_number: parentBatch,
                wastage_event_id: wastageEventId,
                damaged_quantity: parseFloat(formData.damagedQuantity),
                repacked_quantity: parseFloat(formData.repackedQuantity),
                wastage_in_repacking: wastageInRepacking,
                reason: formData.reason,
                notes: formData.notes || undefined,
            };

            const response = await wastageTrackingAPI.initiateRepack(request, photos);

            enqueueSnackbar(
                `Repacking successful! New batch ${response.new_batch_number} created`,
                { variant: 'success' }
            );

            onSuccess(response.new_batch_number);
            onClose();
        } catch (error: any) {
            enqueueSnackbar(
                error.response?.data?.detail || 'Failed to initiate repacking',
                { variant: 'error' }
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>Repacking Workflow</DialogTitle>
            <DialogContent>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                    {/* Parent Batch Info */}
                    <Alert severity="info">
                        <Typography variant="body2">
                            <strong>Parent Batch:</strong> {parentBatch}
                        </Typography>
                        <Typography variant="body2">
                            <strong>New Batch:</strong> {newBatchNumber}
                        </Typography>
                    </Alert>

                    {/* Damaged Quantity */}
                    <TextField
                        label="Damaged Quantity (kg)"
                        type="number"
                        value={formData.damagedQuantity}
                        onChange={(e) => setFormData({ ...formData, damagedQuantity: e.target.value })}
                        error={!!errors.damagedQuantity}
                        helperText={errors.damagedQuantity}
                        required
                        fullWidth
                        inputProps={{ min: 0, step: 0.01 }}
                    />

                    {/* Repacked Quantity */}
                    <TextField
                        label="Repacked Quantity (kg)"
                        type="number"
                        value={formData.repackedQuantity}
                        onChange={(e) => setFormData({ ...formData, repackedQuantity: e.target.value })}
                        error={!!errors.repackedQuantity}
                        helperText={errors.repackedQuantity}
                        required
                        fullWidth
                        inputProps={{ min: 0, step: 0.01 }}
                    />

                    {/* Wastage Calculation */}
                    {wastageInRepacking > 0 && (
                        <Alert severity="warning">
                            <Typography variant="body2">
                                <strong>Wastage in Repacking:</strong> {wastageInRepacking.toFixed(2)} kg
                            </Typography>
                            <Typography variant="caption">
                                This is the additional wastage that occurred during the repacking process.
                            </Typography>
                        </Alert>
                    )}

                    {/* Reason */}
                    <TextField
                        label="Reason"
                        value={formData.reason}
                        onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                        error={!!errors.reason}
                        helperText={errors.reason || 'e.g., Cold storage condensation damage'}
                        required
                        fullWidth
                        multiline
                        rows={2}
                    />

                    {/* Notes */}
                    <TextField
                        label="Notes (Optional)"
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        helperText="Additional details about the repacking process"
                        fullWidth
                        multiline
                        rows={2}
                    />

                    {/* Photo Upload */}
                    <Box>
                        <Typography variant="subtitle2" gutterBottom>
                            Photos *
                        </Typography>
                        <PhotoUpload
                            onPhotosChange={setPhotos}
                            maxPhotos={5}
                            required
                        />
                    </Box>
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
                    {loading ? 'Processing...' : 'Initiate Repacking'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

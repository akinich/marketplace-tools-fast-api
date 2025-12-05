/**
 * Repacking Modal Component
 * Version: 1.0.0
 * Created: 2024-12-04
 *
 * Description:
 *   Dialog for creating repacked batches from damaged items
 *   - Parent batch number (read-only)
 *   - Reason, quantities, photos, notes
 *   - Creates new batch with "R" suffix
 */

import React, { useState } from 'react';
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
import {
    Save as SaveIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { batchTrackingAPI, RepackBatchRequest } from '../../api/batchTracking';

interface RepackingModalProps {
    open: boolean;
    onClose: () => void;
    batchNumber: string;
    onSuccess?: () => void;
}

export default function RepackingModal({ open, onClose, batchNumber, onSuccess }: RepackingModalProps) {
    const { enqueueSnackbar } = useSnackbar();

    const [reason, setReason] = useState('');
    const [damagedQuantity, setDamagedQuantity] = useState('');
    const [repackedQuantity, setRepackedQuantity] = useState('');
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);

    // Predict new batch number
    const newBatchNumber = `${batchNumber}R`;

    const handleSubmit = async () => {
        // Validation
        if (!reason.trim()) {
            enqueueSnackbar('Please provide a reason for repacking', { variant: 'warning' });
            return;
        }

        const damaged = parseFloat(damagedQuantity);
        const repacked = parseFloat(repackedQuantity);

        if (isNaN(damaged) || damaged <= 0) {
            enqueueSnackbar('Damaged quantity must be greater than 0', { variant: 'warning' });
            return;
        }

        if (isNaN(repacked) || repacked <= 0) {
            enqueueSnackbar('Repacked quantity must be greater than 0', { variant: 'warning' });
            return;
        }

        if (repacked > damaged) {
            enqueueSnackbar('Repacked quantity cannot exceed damaged quantity', { variant: 'warning' });
            return;
        }

        setLoading(true);
        try {
            const data: RepackBatchRequest = {
                reason: reason.trim(),
                damaged_quantity: damaged,
                repacked_quantity: repacked,
                notes: notes.trim() || undefined,
            };

            const response = await batchTrackingAPI.repackBatch(batchNumber, data);

            enqueueSnackbar(`Repacked batch ${response.new_batch_number} created successfully!`, { variant: 'success' });

            // Reset form
            setReason('');
            setDamagedQuantity('');
            setRepackedQuantity('');
            setNotes('');

            onClose();
            if (onSuccess) onSuccess();
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to create repacked batch', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        if (!loading) {
            setReason('');
            setDamagedQuantity('');
            setRepackedQuantity('');
            setNotes('');
            onClose();
        }
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <DialogTitle>Repack Batch</DialogTitle>
            <DialogContent>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                    <Alert severity="info">
                        Creating repacked batch from <strong>{batchNumber}</strong>
                        <br />
                        New batch number will be: <strong>{newBatchNumber}</strong>
                    </Alert>

                    <TextField
                        label="Reason for Repacking"
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        multiline
                        rows={2}
                        required
                        fullWidth
                        helperText="e.g., Cold storage damage, packaging defect"
                    />

                    <TextField
                        label="Damaged Quantity"
                        type="number"
                        value={damagedQuantity}
                        onChange={(e) => setDamagedQuantity(e.target.value)}
                        required
                        fullWidth
                        inputProps={{ min: 0, step: 0.01 }}
                        helperText="Total quantity damaged (kg/units)"
                    />

                    <TextField
                        label="Repacked Quantity"
                        type="number"
                        value={repackedQuantity}
                        onChange={(e) => setRepackedQuantity(e.target.value)}
                        required
                        fullWidth
                        inputProps={{ min: 0, step: 0.01 }}
                        helperText="Quantity salvaged and repacked (kg/units)"
                    />

                    <TextField
                        label="Additional Notes"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        multiline
                        rows={2}
                        fullWidth
                        helperText="Optional additional information"
                    />

                    <Alert severity="warning">
                        <Typography variant="body2">
                            <strong>Note:</strong> A batch can only be repacked once. Repacked batches get FIFO priority.
                        </Typography>
                    </Alert>
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
                    startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
                >
                    {loading ? 'Creating...' : 'Create Repacked Batch'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

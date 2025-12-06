import React, { useState } from 'react';
import {
    Dialog, DialogTitle, DialogContent, DialogActions,
    Button, Alert, CircularProgress
} from '@mui/material';
import { grnAPI, GRNResponse } from '../../../api/grn';

interface Props {
    open: boolean;
    onClose: () => void;
    poId: number;
    poNumber: string;
    onSuccess: (grn: GRNResponse) => void;
}

const GRNGenerationModal: React.FC<Props> = ({ open, onClose, poId, poNumber, onSuccess }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await grnAPI.generate(poId);
            onSuccess(response.data);
            onClose();
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to generate GRN');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Generate GRN</DialogTitle>
            <DialogContent>
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

                <p>
                    This will generate a new GRN for <strong>PO #{poNumber}</strong>
                </p>
                <p>
                    A unique <strong>Batch Number</strong> will be automatically assigned.
                </p>
                <p>
                    After generation, you can:
                </p>
                <ul>
                    <li>Print blank GRN template for on-site data capture</li>
                    <li>Enter receiving data (quantities, damage, photos)</li>
                    <li>Finalize GRN to update PO and log wastage</li>
                </ul>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose} disabled={loading}>
                    Cancel
                </Button>
                <Button
                    variant="contained"
                    onClick={handleGenerate}
                    disabled={loading}
                >
                    {loading ? <CircularProgress size={24} /> : 'Generate GRN'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default GRNGenerationModal;

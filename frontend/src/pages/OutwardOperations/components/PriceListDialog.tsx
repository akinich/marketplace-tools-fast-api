import { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Grid,
    FormControlLabel,
    Switch,
    CircularProgress,
} from '@mui/material';
import { useSnackbar } from 'notistack';
import priceListAPI, { PriceList, PriceListCreate, PriceListUpdate } from '../../../api/priceList';

interface PriceListDialogProps {
    open: boolean;
    priceList: PriceList | null;
    onClose: (refresh?: boolean) => void;
}

function PriceListDialog({ open, priceList, onClose }: PriceListDialogProps) {
    const { enqueueSnackbar } = useSnackbar();
    const [loading, setLoading] = useState(false);

    const [formData, setFormData] = useState({
        price_list_name: '',
        description: '',
        valid_from: '',
        valid_to: '',
        is_active: true,
    });

    // Reset form when dialog opens/closes
    useEffect(() => {
        if (open) {
            if (priceList) {
                // Edit mode
                setFormData({
                    price_list_name: priceList.price_list_name,
                    description: priceList.description || '',
                    valid_from: priceList.valid_from,
                    valid_to: priceList.valid_to || '',
                    is_active: priceList.is_active,
                });
            } else {
                // Create mode - set default valid_from to today
                const today = new Date().toISOString().split('T')[0];
                setFormData({
                    price_list_name: '',
                    description: '',
                    valid_from: today,
                    valid_to: '',
                    is_active: true,
                });
            }
        }
    }, [open, priceList]);

    const handleChange = (field: string, value: any) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async () => {
        // Validation
        if (!formData.price_list_name.trim()) {
            enqueueSnackbar('Price list name is required', { variant: 'error' });
            return;
        }

        if (!formData.valid_from) {
            enqueueSnackbar('Valid from date is required', { variant: 'error' });
            return;
        }

        if (formData.valid_to && formData.valid_to < formData.valid_from) {
            enqueueSnackbar('Valid to date must be after valid from date', { variant: 'error' });
            return;
        }

        setLoading(true);

        try {
            if (priceList) {
                // Update
                const updateData: PriceListUpdate = {};
                if (formData.price_list_name !== priceList.price_list_name) {
                    updateData.price_list_name = formData.price_list_name;
                }
                if (formData.description !== (priceList.description || '')) {
                    updateData.description = formData.description || undefined;
                }
                if (formData.valid_from !== priceList.valid_from) {
                    updateData.valid_from = formData.valid_from;
                }
                if (formData.valid_to !== (priceList.valid_to || '')) {
                    updateData.valid_to = formData.valid_to || undefined;
                }
                if (formData.is_active !== priceList.is_active) {
                    updateData.is_active = formData.is_active;
                }

                await priceListAPI.update(priceList.id, updateData);
                enqueueSnackbar('Price list updated successfully', { variant: 'success' });
            } else {
                // Create
                const createData: PriceListCreate = {
                    price_list_name: formData.price_list_name,
                    description: formData.description || undefined,
                    valid_from: formData.valid_from,
                    valid_to: formData.valid_to || undefined,
                    is_active: formData.is_active,
                };

                await priceListAPI.create(createData);
                enqueueSnackbar('Price list created successfully', { variant: 'success' });
            }

            onClose(true); // Refresh parent
        } catch (error: any) {
            enqueueSnackbar(
                error.response?.data?.detail || `Failed to ${priceList ? 'update' : 'create'} price list`,
                { variant: 'error' }
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={() => onClose()} maxWidth="md" fullWidth>
            <DialogTitle>
                {priceList ? '✏️ Edit Price List' : '➕ Create Price List'}
            </DialogTitle>
            <DialogContent>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            required
                            label="Price List Name"
                            value={formData.price_list_name}
                            onChange={(e) => handleChange('price_list_name', e.target.value)}
                            placeholder="e.g., Q1 2026 Pricing"
                        />
                    </Grid>

                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            multiline
                            rows={2}
                            label="Description"
                            value={formData.description}
                            onChange={(e) => handleChange('description', e.target.value)}
                            placeholder="Optional description"
                        />
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <TextField
                            fullWidth
                            required
                            type="date"
                            label="Valid From"
                            value={formData.valid_from}
                            onChange={(e) => handleChange('valid_from', e.target.value)}
                            InputLabelProps={{ shrink: true }}
                            placeholder="dd/mm/yyyy"
                            inputProps={{
                                style: { cursor: 'pointer' }
                            }}
                        />
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <TextField
                            fullWidth
                            type="date"
                            label="Valid To (Optional)"
                            value={formData.valid_to}
                            onChange={(e) => handleChange('valid_to', e.target.value)}
                            InputLabelProps={{ shrink: true }}
                            helperText="Leave empty for indefinite"
                            placeholder="dd/mm/yyyy"
                            inputProps={{
                                style: { cursor: 'pointer' }
                            }}
                        />
                    </Grid>

                    <Grid item xs={12}>
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={formData.is_active}
                                    onChange={(e) => handleChange('is_active', e.target.checked)}
                                />
                            }
                            label="Active"
                        />
                    </Grid>
                </Grid>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => onClose()} disabled={loading}>
                    Cancel
                </Button>
                <Button
                    onClick={handleSubmit}
                    variant="contained"
                    disabled={loading}
                    startIcon={loading && <CircularProgress size={20} />}
                >
                    {priceList ? 'Update' : 'Create'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default PriceListDialog;

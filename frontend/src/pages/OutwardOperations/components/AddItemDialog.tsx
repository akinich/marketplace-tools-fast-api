import { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Autocomplete,
    CircularProgress,
    Box,
} from '@mui/material';
import { useSnackbar } from 'notistack';
import priceListAPI from '../../../api/priceList';
import { zohoItemAPI } from '../../../api/zohoItem';

interface AddItemDialogProps {
    open: boolean;
    priceListId: number;
    onClose: (refresh?: boolean) => void;
}

function AddItemDialog({ open, priceListId, onClose }: AddItemDialogProps) {
    const { enqueueSnackbar } = useSnackbar();
    const [loading, setLoading] = useState(false);
    const [loadingItems, setLoadingItems] = useState(false);
    const [availableItems, setAvailableItems] = useState<any[]>([]);
    const [selectedItem, setSelectedItem] = useState<any>(null);
    const [price, setPrice] = useState<string>('');
    const [notes, setNotes] = useState<string>('');

    // Load available items when dialog opens
    useEffect(() => {
        if (open) {
            loadItems();
        } else {
            // Reset form when closing
            setSelectedItem(null);
            setPrice('');
            setNotes('');
        }
    }, [open]);

    const loadItems = async () => {
        setLoadingItems(true);
        try {
            const response = await zohoItemAPI.getItems();
            setAvailableItems(response.items || []);
        } catch (error: any) {
            enqueueSnackbar('Failed to load items', { variant: 'error' });
        } finally {
            setLoadingItems(false);
        }
    };

    const handleAdd = async () => {
        if (!selectedItem || !price || parseFloat(price) <= 0) {
            enqueueSnackbar('Please select an item and enter a valid price', { variant: 'error' });
            return;
        }

        setLoading(true);
        try {
            await priceListAPI.addOrUpdateItem(priceListId, {
                item_id: selectedItem.id,
                price: parseFloat(price),
                notes: notes || undefined,
            });
            enqueueSnackbar('Item added successfully', { variant: 'success' });
            onClose(true); // Close and refresh
        } catch (error: any) {
            enqueueSnackbar(
                error.response?.data?.detail || 'Failed to add item',
                { variant: 'error' }
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={() => onClose()} maxWidth="sm" fullWidth>
            <DialogTitle>➕ Add Item to Price List</DialogTitle>
            <DialogContent>
                {loadingItems ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                        <CircularProgress />
                    </Box>
                ) : (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
                        <Autocomplete
                            options={availableItems}
                            getOptionLabel={(option) => `${option.sku || option.id} - ${option.name}`}
                            value={selectedItem}
                            onChange={(_, value) => setSelectedItem(value)}
                            renderInput={(params) => (
                                <TextField
                                    {...params}
                                    label="Select Item *"
                                    required
                                />
                            )}
                            isOptionEqualToValue={(option, value) => option.id === value.id}
                        />

                        <TextField
                            label="Price (₹) *"
                            type="number"
                            value={price}
                            onChange={(e) => setPrice(e.target.value)}
                            inputProps={{ min: 0, step: 0.01 }}
                            required
                            fullWidth
                            helperText="Enter the price for this item in this price list"
                        />

                        <TextField
                            label="Notes (Optional)"
                            multiline
                            rows={2}
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            fullWidth
                            placeholder="Add any special notes for this pricing"
                        />
                    </Box>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={() => onClose()} disabled={loading}>
                    Cancel
                </Button>
                <Button
                    onClick={handleAdd}
                    variant="contained"
                    disabled={loading || loadingItems || !selectedItem || !price}
                >
                    {loading ? <CircularProgress size={24} /> : 'Add Item'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default AddItemDialog;

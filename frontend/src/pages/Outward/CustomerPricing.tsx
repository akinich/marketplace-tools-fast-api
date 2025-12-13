/**
 * Customer Pricing Management
 * Version: 1.0.0
 * Created: 2025-12-07
 *
 * Manage customer-specific item pricing
 */

import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Card,
    TextField,
    Autocomplete,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Alert,
    CircularProgress,
    Grid,
    Divider,
    IconButton,
} from '@mui/material';
import { Add as AddIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { salesOrdersAPI } from '../../api/salesOrders';
import { zohoCustomerAPI } from '../../api/zohoCustomer';
import { zohoItemAPI } from '../../api/zohoItem';
import { formatDate } from '../../utils/formatters';
import { CustomerPricing } from '../../types/SalesOrder';
import { getTodayISO } from '../../utils/dateUtils';

interface CustomerOption {
    id: number;
    name: string;
}

interface ItemOption {
    id: number;
    name: string;
}

const CustomerPricingPage: React.FC = () => {
    const { enqueueSnackbar } = useSnackbar();

    const [customers, setCustomers] = useState<CustomerOption[]>([]);
    const [items, setItems] = useState<ItemOption[]>([]);
    const [pricingList, setPricingList] = useState<CustomerPricing[]>([]);

    const [loading, setLoading] = useState(false);
    const [listLoading, setListLoading] = useState(false);

    // Form state
    const [selectedCustomer, setSelectedCustomer] = useState<CustomerOption | null>(null);
    const [selectedItem, setSelectedItem] = useState<ItemOption | null>(null);
    const [price, setPrice] = useState<string>('');
    const [effectiveFrom, setEffectiveFrom] = useState<string>(getTodayISO());
    const [effectiveTo, setEffectiveTo] = useState<string>('');
    const [notes, setNotes] = useState<string>('');

    // Load initial data
    useEffect(() => {
        const loadData = async () => {
            try {
                const [customersData, itemsData] = await Promise.all([
                    zohoCustomerAPI.getItems(),
                    zohoItemAPI.getItems(),
                ]);

                // Adjust depending on API response structure
                const customerList = customersData.customers || customersData.items || [];
                setCustomers(customerList.map((c: any) => ({ id: c.id, name: c.contact_name || c.name })));

                const itemList = itemsData.items || [];
                setItems(itemList.map((i: any) => ({ id: i.id, name: i.name })));
            } catch (error: any) {
                console.error('Failed to load data:', error);
                enqueueSnackbar('Failed to load customers and items', { variant: 'error' });
            }
        };

        loadData();
    }, [enqueueSnackbar]);

    // Load pricing history when customer/item selected
    useEffect(() => {
        if (!selectedCustomer) {
            setPricingList([]);
            return;
        }

        const loadPricing = async () => {
            setListLoading(true);
            try {
                // If item selected, filter by item, otherwise get all for customer
                const data = await salesOrdersAPI.getCustomerPricingHistory(
                    selectedCustomer.id,
                    selectedItem?.id
                );
                setPricingList(data);
            } catch (error: any) {
                console.error('Failed to load pricing:', error);
                setPricingList([]);
            } finally {
                setListLoading(false);
            }
        };

        loadPricing();
    }, [selectedCustomer, selectedItem, enqueueSnackbar]); // Reload when customer or item changes

    // Handle form submit
    const handleSubmit = async () => {
        if (!selectedCustomer || !selectedItem || !price || !effectiveFrom) {
            enqueueSnackbar('Please fill all required fields', { variant: 'error' });
            return;
        }

        if (parseFloat(price) <= 0) {
            enqueueSnackbar('Price must be greater than 0', { variant: 'error' });
            return;
        }

        setLoading(true);
        try {
            await salesOrdersAPI.setCustomerPrice({
                customer_id: selectedCustomer.id,
                item_id: selectedItem.id,
                price: parseFloat(price),
                effective_from: effectiveFrom,
                effective_to: effectiveTo || undefined,
                notes: notes || undefined
            });
            enqueueSnackbar('Price updated successfully', { variant: 'success' });

            // Reload list
            const data = await salesOrdersAPI.getCustomerPricingHistory(selectedCustomer.id, selectedItem.id);
            setPricingList(data);

            // Reset Form Values (keep selection)
            setPrice('');
            setNotes('');
            // effectiveFrom kept as is for convenience

        } catch (error: any) {
            console.error('Failed to update price:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to update price', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" component="h1" gutterBottom>
                Customer Pricing Management
            </Typography>

            <Grid container spacing={3}>
                {/* Add/Edit Pricing */}
                <Grid item xs={12} md={4}>
                    <Card sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Set Price
                        </Typography>
                        <Divider sx={{ mb: 2 }} />

                        <Autocomplete
                            options={customers}
                            getOptionLabel={(option) => option.name}
                            value={selectedCustomer}
                            onChange={(_, value) => setSelectedCustomer(value)}
                            renderInput={(params) => <TextField {...params} label="Select Customer *" required />}
                            sx={{ mb: 2 }}
                        />

                        <Autocomplete
                            options={items}
                            getOptionLabel={(option) => option.name}
                            value={selectedItem}
                            onChange={(_, value) => setSelectedItem(value)}
                            renderInput={(params) => <TextField {...params} label="Select Item *" required />}
                            sx={{ mb: 2 }}
                            disabled={!selectedCustomer}
                        />

                        <TextField
                            label="Price (₹) *"
                            type="number"
                            value={price}
                            onChange={(e) => setPrice(e.target.value)}
                            inputProps={{ min: 0, step: 0.01 }}
                            fullWidth
                            required
                            sx={{ mb: 2 }}
                            disabled={!selectedItem}
                        />

                        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                            <TextField
                                label="From Date *"
                                type="date"
                                value={effectiveFrom}
                                onChange={(e) => setEffectiveFrom(e.target.value)}
                                InputLabelProps={{ shrink: true }}
                                fullWidth
                                required
                            />
                            <TextField
                                label="To Date"
                                type="date"
                                value={effectiveTo}
                                onChange={(e) => setEffectiveTo(e.target.value)}
                                InputLabelProps={{ shrink: true }}
                                fullWidth
                                helperText="Optional"
                            />
                        </Box>

                        <TextField
                            label="Notes"
                            multiline
                            rows={2}
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            fullWidth
                            sx={{ mb: 3 }}
                        />

                        <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            onClick={handleSubmit}
                            disabled={loading || !selectedCustomer || !selectedItem}
                            fullWidth
                        >
                            {loading ? <CircularProgress size={24} /> : 'Set Price'}
                        </Button>
                    </Card>
                </Grid>

                {/* Price List */}
                <Grid item xs={12} md={8}>
                    <Card sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Typography variant="h6">
                                Pricing History {selectedCustomer && `- ${selectedCustomer.name}`}
                            </Typography>
                            {selectedCustomer && (
                                <IconButton onClick={async () => {
                                    setListLoading(true);
                                    const data = await salesOrdersAPI.getCustomerPricingHistory(selectedCustomer.id, selectedItem?.id);
                                    setPricingList(data);
                                    setListLoading(false);
                                }}>
                                    <RefreshIcon />
                                </IconButton>
                            )}
                        </Box>
                        <Divider sx={{ mb: 2 }} />

                        {listLoading ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                                <CircularProgress />
                            </Box>
                        ) : !selectedCustomer ? (
                            <Alert severity="info">Please select a customer to view their pricing.</Alert>
                        ) : pricingList.length === 0 ? (
                            <Alert severity="warning">No custom prices found.</Alert>
                        ) : (
                            <Box sx={{ overflowX: 'auto' }}>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Item</TableCell>
                                            <TableCell>Price</TableCell>
                                            <TableCell>Effective From</TableCell>
                                            <TableCell>Effective To</TableCell>
                                            <TableCell>Notes</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {pricingList.map((entry) => (
                                            <TableRow key={entry.id}>
                                                <TableCell>{entry.item_name}</TableCell>
                                                <TableCell>₹{Number(entry.price).toFixed(2)}</TableCell>
                                                <TableCell>{formatDate(entry.effective_from)}</TableCell>
                                                <TableCell>{entry.effective_to ? formatDate(entry.effective_to) : '-'}</TableCell>
                                                <TableCell>{entry.notes || '-'}</TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </Box>
                        )}
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default CustomerPricingPage;

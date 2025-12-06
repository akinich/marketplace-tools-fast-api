/**
 * Purchase Order Create/Edit Form
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Form for creating and editing purchase orders with 3-tier pricing
 */

import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Card,
    TextField,
    Autocomplete,
    IconButton,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Chip,
    Alert,
    Typography,
    CircularProgress,
} from '@mui/material';
import { Add, Delete, ArrowBack } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { purchaseOrdersAPI, POCreateRequest, ActivePriceResponse } from '../../../api/purchaseOrders';
import { zohoVendorAPI } from '../../../api/zohoVendor';
import { zohoItemAPI } from '../../../api/zohoItem';
import { validateDeliveryDate, checkDateGap, getTodayISO } from '../../../utils/dateUtils';

interface POItemRow {
    item_id: number | null;
    item_name: string;
    quantity: number;
    unit_price: number | null;
    price_source: 'vendor' | 'zoho' | 'manual' | null;
    total: number;
}

interface VendorOption {
    id: number;
    name: string;
}

interface ItemOption {
    id: number;
    name: string;
    rate?: number;
}

const POCreateForm: React.FC = () => {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();

    const [loading, setLoading] = useState(false);
    const [vendorId, setVendorId] = useState<number | null>(null);
    const [dispatchDate, setDispatchDate] = useState<string>(getTodayISO());
    const [deliveryDate, setDeliveryDate] = useState<string>(getTodayISO());
    const [items, setItems] = useState<POItemRow[]>([]);
    const [notes, setNotes] = useState('');
    const [vendors, setVendors] = useState<VendorOption[]>([]);
    const [availableItems, setAvailableItems] = useState<ItemOption[]>([]);
    const [activePrices, setActivePrices] = useState<ActivePriceResponse[]>([]);

    // Load vendors and items
    useEffect(() => {
        const loadData = async () => {
            try {
                const [vendorsData, itemsData] = await Promise.all([
                    zohoVendorAPI.getItems(),
                    zohoItemAPI.getItems(),
                ]);

                setVendors(vendorsData.vendors?.map((v: any) => ({ id: v.vendor_id, name: v.vendor_name })) || []);
                setAvailableItems(itemsData.items?.map((i: any) => ({ id: i.item_id, name: i.name, rate: i.rate })) || []);
            } catch (error: any) {
                console.error('Failed to load data:', error);
                enqueueSnackbar('Failed to load vendors and items', { variant: 'error' });
            }
        };

        loadData();
    }, [enqueueSnackbar]);

    // Load active prices when vendor or dispatch date changes
    useEffect(() => {
        const loadActivePrices = async () => {
            if (!vendorId || !dispatchDate) return;

            try {
                const prices = await purchaseOrdersAPI.getActivePrices(vendorId, dispatchDate);
                setActivePrices(prices);
            } catch (error: any) {
                console.error('Failed to load prices:', error);
                // Don't show error - prices are optional
            }
        };

        loadActivePrices();
    }, [vendorId, dispatchDate]);

    // Price source color mapping
    const getPriceSourceColor = (source: string): 'success' | 'info' | 'warning' => {
        const colors: Record<string, 'success' | 'info' | 'warning'> = {
            vendor: 'success',
            zoho: 'info',
            manual: 'warning',
        };
        return colors[source] || 'warning';
    };

    // Add item row
    const addItemRow = () => {
        setItems([
            ...items,
            {
                item_id: null,
                item_name: '',
                quantity: 0,
                unit_price: null,
                price_source: null,
                total: 0,
            },
        ]);
    };

    // Remove item row
    const removeItemRow = (index: number) => {
        setItems(items.filter((_, i) => i !== index));
    };

    // Handle item selection
    const handleItemSelect = (index: number, item: ItemOption | null) => {
        if (!item) return;

        const updatedItems = [...items];
        updatedItems[index].item_id = item.id;
        updatedItems[index].item_name = item.name;

        // Try to find vendor-specific price
        const vendorPrice = activePrices.find((p) => p.item_id === item.id && p.source === 'vendor');
        const zohoPrice = activePrices.find((p) => p.item_id === item.id && p.source === 'zoho');

        if (vendorPrice) {
            updatedItems[index].unit_price = vendorPrice.price;
            updatedItems[index].price_source = 'vendor';
        } else if (zohoPrice) {
            updatedItems[index].unit_price = zohoPrice.price;
            updatedItems[index].price_source = 'zoho';
        } else if (item.rate) {
            // Fallback to item's default rate
            updatedItems[index].unit_price = item.rate;
            updatedItems[index].price_source = 'zoho';
        } else {
            // No price found - require manual entry
            updatedItems[index].price_source = 'manual';
        }

        updateItemTotal(updatedItems, index);
        setItems(updatedItems);
    };

    // Handle quantity/price change
    const handleItemChange = (index: number, field: keyof POItemRow, value: any) => {
        const updatedItems = [...items];
        (updatedItems[index] as any)[field] = value;

        // If price manually edited, change source to manual
        if (field === 'unit_price') {
            updatedItems[index].price_source = 'manual';
        }

        updateItemTotal(updatedItems, index);
        setItems(updatedItems);
    };

    // Calculate item total
    const updateItemTotal = (items: POItemRow[], index: number) => {
        const item = items[index];
        item.total = (item.quantity || 0) * (item.unit_price || 0);
    };

    // Calculate grand total
    const calculateTotal = () => {
        return items.reduce((sum, item) => sum + item.total, 0);
    };

    // Validate form
    const validateForm = (): string | null => {
        if (!vendorId) return 'Please select a vendor';
        if (!dispatchDate) return 'Please select dispatch date';
        if (!deliveryDate) return 'Please select delivery date';
        if (items.length === 0) return 'Please add at least one item';

        for (const item of items) {
            if (!item.item_id) return 'Please select all items';
            if (item.quantity <= 0) return 'All quantities must be greater than 0';
            if (!item.unit_price || item.unit_price <= 0) return 'All prices must be greater than 0';
        }

        const dateError = validateDeliveryDate(dispatchDate, deliveryDate);
        if (dateError) return dateError;

        return null;
    };

    // Submit form
    const handleSubmit = async (sendToFarm: boolean = false) => {
        const validationError = validateForm();
        if (validationError) {
            enqueueSnackbar(validationError, { variant: 'error' });
            return;
        }

        setLoading(true);
        try {
            const poData: POCreateRequest = {
                vendor_id: vendorId!,
                dispatch_date: dispatchDate,
                delivery_date: deliveryDate,
                items: items.map((item) => ({
                    item_id: item.item_id!,
                    quantity: item.quantity,
                    unit_price: item.unit_price!,
                    notes: undefined,
                })),
                notes: notes || undefined,
            };

            const response = await purchaseOrdersAPI.create(poData);

            if (sendToFarm) {
                await purchaseOrdersAPI.send(response.id);
                enqueueSnackbar('PO created and sent to farm successfully', { variant: 'success' });
            } else {
                enqueueSnackbar('PO created successfully', { variant: 'success' });
            }

            navigate(`/inward/purchase-orders/${response.id}`);
        } catch (error: any) {
            console.error('Failed to create PO:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to create PO', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const dateValidationError = validateDeliveryDate(dispatchDate, deliveryDate);
    const dateGapWarning = checkDateGap(dispatchDate, deliveryDate);

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <IconButton onClick={() => navigate('/inward/purchase-orders')}>
                    <ArrowBack />
                </IconButton>
                <Typography variant="h4" component="h1">
                    Create Purchase Order
                </Typography>
            </Box>

            <Card sx={{ p: 3, mb: 3 }}>
                {/* Vendor Selection */}
                <Autocomplete
                    options={vendors}
                    getOptionLabel={(option) => option.name}
                    value={vendors.find((v) => v.id === vendorId) || null}
                    onChange={(_, value) => setVendorId(value?.id || null)}
                    renderInput={(params) => <TextField {...params} label="Vendor / Farm *" required />}
                    sx={{ mb: 2 }}
                />

                {/* Date Pickers */}
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <TextField
                        label="Dispatch / Billing Date *"
                        type="date"
                        value={dispatchDate}
                        onChange={(e) => setDispatchDate(e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        fullWidth
                        required
                    />
                    <TextField
                        label="Expected Delivery Date *"
                        type="date"
                        value={deliveryDate}
                        onChange={(e) => setDeliveryDate(e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        fullWidth
                        required
                        error={!!dateValidationError}
                        helperText={dateValidationError}
                    />
                </Box>

                {/* Date Validation Alert */}
                {dateGapWarning && (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        {dateGapWarning}
                    </Alert>
                )}

                {/* Items Table */}
                <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
                    Items
                </Typography>
                <Box sx={{ overflowX: 'auto' }}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Item *</TableCell>
                                <TableCell>Quantity *</TableCell>
                                <TableCell>Unit Price *</TableCell>
                                <TableCell>Source</TableCell>
                                <TableCell>Total</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {items.map((item, index) => (
                                <TableRow key={index}>
                                    <TableCell>
                                        <Autocomplete
                                            options={availableItems}
                                            getOptionLabel={(option) => option.name}
                                            onChange={(_, value) => handleItemSelect(index, value)}
                                            renderInput={(params) => <TextField {...params} size="small" />}
                                            sx={{ minWidth: 200 }}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            size="small"
                                            value={item.quantity || ''}
                                            onChange={(e) => handleItemChange(index, 'quantity', parseFloat(e.target.value) || 0)}
                                            inputProps={{ min: 0, step: 0.01 }}
                                            sx={{ width: 100 }}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            size="small"
                                            value={item.unit_price || ''}
                                            onChange={(e) => handleItemChange(index, 'unit_price', parseFloat(e.target.value) || 0)}
                                            inputProps={{ min: 0, step: 0.01 }}
                                            sx={{ width: 120 }}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        {item.price_source && (
                                            <Chip
                                                label={item.price_source.toUpperCase()}
                                                color={getPriceSourceColor(item.price_source)}
                                                size="small"
                                            />
                                        )}
                                    </TableCell>
                                    <TableCell>₹{item.total.toFixed(2)}</TableCell>
                                    <TableCell>
                                        <IconButton size="small" onClick={() => removeItemRow(index)} color="error">
                                            <Delete />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Box>

                <Button startIcon={<Add />} onClick={addItemRow} sx={{ mt: 2 }}>
                    Add Item
                </Button>

                {/* Total */}
                <Box sx={{ mt: 3, textAlign: 'right' }}>
                    <Typography variant="h5">Total: ₹{calculateTotal().toFixed(2)}</Typography>
                </Box>

                {/* Notes */}
                <TextField
                    label="Notes"
                    multiline
                    rows={3}
                    fullWidth
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    sx={{ mt: 2 }}
                />

                {/* Actions */}
                <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                    <Button variant="outlined" onClick={() => navigate('/inward/purchase-orders')}>
                        Cancel
                    </Button>
                    <Button
                        variant="outlined"
                        onClick={() => handleSubmit(false)}
                        disabled={loading}
                    >
                        {loading ? <CircularProgress size={24} /> : 'Save as Draft'}
                    </Button>
                    <Button
                        variant="contained"
                        onClick={() => handleSubmit(true)}
                        disabled={loading}
                    >
                        {loading ? <CircularProgress size={24} /> : 'Save & Send to Farm'}
                    </Button>
                </Box>
            </Card>
        </Box>
    );
};

export default POCreateForm;

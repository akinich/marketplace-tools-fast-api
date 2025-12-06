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

    const [poNumber, setPoNumber] = useState('');
    const [hsnMap, setHsnMap] = useState<Record<number, string>>({});

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
                // Fetch next PO number first
                try {
                    const nextPo = await purchaseOrdersAPI.getNextNumber();
                    setPoNumber(nextPo.po_number);
                } catch (error) {
                    console.error('Failed to fetch next PO number:', error);
                    enqueueSnackbar('Could not generate PO number automatically', { variant: 'warning' });
                }

                const [vendorsData, itemsData] = await Promise.all([
                    zohoVendorAPI.getItems(),
                    zohoItemAPI.getItems(),
                ]);

                if (!vendorsData.vendors || vendorsData.vendors.length === 0) {
                    console.warn('No vendors returned from API');
                    enqueueSnackbar('No vendors found. Please check Zoho sync.', { variant: 'warning' });
                }

                setVendors(vendorsData.vendors?.map((v: any) => ({ id: v.id, name: v.contact_name })) || []);

                // Map items and store HSN codes
                const validItems = itemsData.items || [];
                setAvailableItems(validItems.map((i: any) => ({ id: i.id, name: i.name, rate: i.rate })) || []);

                // Create HSN map for quick lookup
                const hsnMapping: Record<number, string> = {};
                validItems.forEach((i: any) => {
                    if (i.hsn_or_sac) {
                        hsnMapping[i.id] = i.hsn_or_sac;
                    }
                });
                setHsnMap(hsnMapping);

            } catch (error: any) {
                console.error('Failed to load data details:', error);
                const errorMsg = error.response?.data?.detail || 'Failed to load vendors and items';
                enqueueSnackbar(errorMsg, { variant: 'error' });
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

    // Filter items based on vendor pricing
    const filteredItems = vendorId && activePrices.length > 0
        ? availableItems.filter(item =>
            activePrices.some(price => price.item_id === item.id)
        )
        : availableItems;

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

        if (!poNumber) {
            enqueueSnackbar('PO Number is required', { variant: 'error' });
            return;
        }

        setLoading(true);
        try {
            const poData: POCreateRequest = {
                vendor_id: vendorId!,
                po_number: poNumber, // Add custom PO number
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
                enqueueSnackbar(`PO ${response.po_number} created and sent to farm`, { variant: 'success' });
            } else {
                enqueueSnackbar(`PO ${response.po_number} created successfully`, { variant: 'success' });
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
                {/* PO Number (Top Row) */}
                <Box sx={{ mb: 3 }}>
                    <TextField
                        label="PO Number *"
                        value={poNumber}
                        onChange={(e) => setPoNumber(e.target.value)}
                        placeholder="PO/YY[YY+1]/XXXX"
                        helperText="Auto-generated but editable (Format: PO/2526/0001)"
                        fullWidth
                        required
                    />
                </Box>

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

                {/* Item Filtering Info */}
                {vendorId && activePrices.length > 0 && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                        Only showing items with configured pricing for this vendor ({filteredItems.length} items available).
                    </Alert>
                )}
                {vendorId && activePrices.length === 0 && (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        No pricing configured for this vendor. Please configure pricing in Vendor Pricing Management before creating PO.
                    </Alert>
                )}

                <Box sx={{ overflowX: 'auto' }}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell width="5%">#</TableCell>
                                <TableCell width="30%">Item & Description *</TableCell>
                                <TableCell width="10%">HSN/SAC</TableCell>
                                <TableCell width="15%">Qty *</TableCell>
                                <TableCell width="15%">Rate *</TableCell>
                                <TableCell width="10%">Source</TableCell>
                                <TableCell width="15%">Amount</TableCell>
                                <TableCell width="5%">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {items.map((item, index) => (
                                <TableRow key={index}>
                                    <TableCell>{index + 1}</TableCell>
                                    <TableCell>
                                        <Autocomplete
                                            options={filteredItems}
                                            getOptionLabel={(option) => option.name}
                                            onChange={(_, value) => handleItemSelect(index, value)}
                                            renderInput={(params) => <TextField {...params} size="small" placeholder="Select Item" />}
                                            sx={{ minWidth: 200 }}
                                            disabled={!vendorId}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        {item.item_id ? (hsnMap[item.item_id] || '-') : '-'}
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

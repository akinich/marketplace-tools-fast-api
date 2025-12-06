/**
 * Vendor Pricing Manager (Admin Only)
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Manage vendor-specific item pricing with effective date ranges
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
    Chip,
    Grid,
    Divider,
} from '@mui/material';
import { Add as AddIcon, Warning as WarningIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { purchaseOrdersAPI, VendorPricingRequest, PriceHistoryResponse, VendorPricingSummary } from '../../../api/purchaseOrders';
import { zohoVendorAPI } from '../../../api/zohoVendor';
import { zohoItemAPI } from '../../../api/zohoItem';
import { formatDateForDisplay, getDaysUntil, getTodayISO } from '../../../utils/dateUtils';
import useAuthStore from '../../../store/authStore';

interface VendorOption {
    id: number;
    name: string;
}

interface ItemOption {
    id: number;
    name: string;
}

const VendorPricingManager: React.FC = () => {
    const { enqueueSnackbar } = useSnackbar();
    const { user } = useAuthStore();

    const [vendors, setVendors] = useState<VendorOption[]>([]);
    const [items, setItems] = useState<ItemOption[]>([]);
    const [priceHistory, setPriceHistory] = useState<PriceHistoryResponse[]>([]);
    const [vendorSummary, setVendorSummary] = useState<VendorPricingSummary[]>([]);
    const [loading, setLoading] = useState(false);
    const [summaryLoading, setSummaryLoading] = useState(false);

    // Form state
    const [selectedVendor, setSelectedVendor] = useState<VendorOption | null>(null);
    const [selectedItem, setSelectedItem] = useState<ItemOption | null>(null);
    const [price, setPrice] = useState<string>('');
    const [effectiveFrom, setEffectiveFrom] = useState<string>(getTodayISO());
    const [effectiveTo, setEffectiveTo] = useState<string>('');
    const [notes, setNotes] = useState('');

    // Filter state
    const [filterVendor, setFilterVendor] = useState<VendorOption | null>(null);
    const [filterItem, setFilterItem] = useState<ItemOption | null>(null);

    // Check if user is admin
    const isAdmin = user?.role === 'Admin';

    // Load vendors and items
    useEffect(() => {
        const loadData = async () => {
            try {
                const [vendorsData, itemsData] = await Promise.all([
                    zohoVendorAPI.getItems(),
                    zohoItemAPI.getItems(),
                ]);

                setVendors(vendorsData.vendors?.map((v: any) => ({ id: v.id, name: v.contact_name })) || []);
                setItems(itemsData.items?.map((i: any) => ({ id: i.id, name: i.name })) || []);
            } catch (error: any) {
                console.error('Failed to load data:', error);
                enqueueSnackbar('Failed to load vendors and items', { variant: 'error' });
            }
        };

        loadData();
    }, [enqueueSnackbar]);

    // Load vendor pricing summary
    useEffect(() => {
        const loadSummary = async () => {
            setSummaryLoading(true);
            try {
                const summary = await purchaseOrdersAPI.getVendorsWithPricing();
                setVendorSummary(summary);
            } catch (error: any) {
                console.error('Failed to load vendor summary:', error);
                // Don't show error toast, just fail silently
            } finally {
                setSummaryLoading(false);
            }
        };

        loadSummary();
    }, []);

    // Load price history when filter changes
    useEffect(() => {
        if (!filterVendor) return;

        const loadHistory = async () => {
            setLoading(true);
            try {
                const history = await purchaseOrdersAPI.getPriceHistory(
                    filterVendor.id,
                    filterItem?.id
                );
                setPriceHistory(history);
            } catch (error: any) {
                console.error('Failed to load price history:', error);
                enqueueSnackbar('Failed to load price history', { variant: 'error' });
            } finally {
                setLoading(false);
            }
        };

        loadHistory();
    }, [filterVendor, filterItem, enqueueSnackbar]);

    // Handle form submit
    const handleSubmit = async () => {
        if (!selectedVendor || !selectedItem || !price || !effectiveFrom) {
            enqueueSnackbar('Please fill all required fields', { variant: 'error' });
            return;
        }

        if (parseFloat(price) <= 0) {
            enqueueSnackbar('Price must be greater than 0', { variant: 'error' });
            return;
        }

        setLoading(true);
        try {
            const request: VendorPricingRequest = {
                vendor_id: selectedVendor.id,
                item_id: selectedItem.id,
                price: parseFloat(price),
                effective_from: effectiveFrom,
                effective_to: effectiveTo || undefined,
                notes: notes || undefined,
            };

            await purchaseOrdersAPI.addVendorPrice(request);
            enqueueSnackbar('Vendor pricing added successfully', { variant: 'success' });

            // Reset form
            setSelectedItem(null);
            setPrice('');
            setEffectiveFrom(getTodayISO());
            setEffectiveTo('');
            setNotes('');

            // Reload history if same vendor
            if (filterVendor?.id === selectedVendor.id) {
                const history = await purchaseOrdersAPI.getPriceHistory(
                    selectedVendor.id,
                    filterItem?.id
                );
                setPriceHistory(history);
            }
        } catch (error: any) {
            console.error('Failed to add pricing:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to add pricing', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    // Check if price is taking effect soon
    const isPriceSoon = (effectiveFrom: string): boolean => {
        const days = getDaysUntil(effectiveFrom);
        return days > 0 && days <= 7;
    };

    if (!isAdmin) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">
                    Access Denied: This page is only accessible to administrators.
                </Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" component="h1" gutterBottom>
                Vendor Pricing Management
            </Typography>

            {/* Vendor Summary Table */}
            <Card sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Vendors with Pricing Configured
                </Typography>
                <Divider sx={{ mb: 2 }} />

                {summaryLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                        <CircularProgress />
                    </Box>
                ) : vendorSummary.length === 0 ? (
                    <Alert severity="info">
                        No vendors with pricing configured yet. Add prices below to get started.
                    </Alert>
                ) : (
                    <Box sx={{ overflowX: 'auto' }}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Vendor Name</TableCell>
                                    <TableCell>Company</TableCell>
                                    <TableCell align="right">Items with Pricing</TableCell>
                                    <TableCell>Last Price Update</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {vendorSummary.map((vendor) => (
                                    <TableRow key={vendor.id}>
                                        <TableCell>{vendor.contact_name}</TableCell>
                                        <TableCell>{vendor.company_name || '-'}</TableCell>
                                        <TableCell align="right">
                                            <Chip
                                                label={vendor.items_count}
                                                size="small"
                                                color="primary"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            {new Date(vendor.last_price_update).toLocaleDateString()}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </Box>
                )}
            </Card>

            <Grid container spacing={3}>
                {/* Add New Pricing */}
                <Grid item xs={12} md={5}>
                    <Card sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Add Vendor-Item Price
                        </Typography>
                        <Divider sx={{ mb: 2 }} />

                        <Autocomplete
                            options={vendors}
                            getOptionLabel={(option) => option.name}
                            value={selectedVendor}
                            onChange={(_, value) => setSelectedVendor(value)}
                            renderInput={(params) => <TextField {...params} label="Vendor *" required />}
                            sx={{ mb: 2 }}
                        />

                        <Autocomplete
                            options={items}
                            getOptionLabel={(option) => option.name}
                            value={selectedItem}
                            onChange={(_, value) => setSelectedItem(value)}
                            renderInput={(params) => <TextField {...params} label="Item *" required />}
                            sx={{ mb: 2 }}
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
                        />

                        <TextField
                            label="Effective From *"
                            type="date"
                            value={effectiveFrom}
                            onChange={(e) => setEffectiveFrom(e.target.value)}
                            InputLabelProps={{ shrink: true }}
                            fullWidth
                            required
                            sx={{ mb: 2 }}
                        />

                        <TextField
                            label="Effective To (Optional)"
                            type="date"
                            value={effectiveTo}
                            onChange={(e) => setEffectiveTo(e.target.value)}
                            InputLabelProps={{ shrink: true }}
                            fullWidth
                            sx={{ mb: 2 }}
                            helperText="Leave empty for indefinite validity"
                        />

                        <TextField
                            label="Notes"
                            multiline
                            rows={2}
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            fullWidth
                            sx={{ mb: 2 }}
                        />

                        <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            onClick={handleSubmit}
                            disabled={loading}
                            fullWidth
                        >
                            {loading ? <CircularProgress size={24} /> : 'Add Pricing'}
                        </Button>
                    </Card>
                </Grid>

                {/* Price History */}
                <Grid item xs={12} md={7}>
                    <Card sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Price History
                        </Typography>
                        <Divider sx={{ mb: 2 }} />

                        {/* Filters */}
                        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                            <Autocomplete
                                options={vendors}
                                getOptionLabel={(option) => option.name}
                                value={filterVendor}
                                onChange={(_, value) => setFilterVendor(value)}
                                renderInput={(params) => <TextField {...params} label="Filter by Vendor" />}
                                sx={{ flex: 1 }}
                            />

                            <Autocomplete
                                options={items}
                                getOptionLabel={(option) => option.name}
                                value={filterItem}
                                onChange={(_, value) => setFilterItem(value)}
                                renderInput={(params) => <TextField {...params} label="Filter by Item" />}
                                sx={{ flex: 1 }}
                            />
                        </Box>

                        {loading ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                                <CircularProgress />
                            </Box>
                        ) : priceHistory.length === 0 ? (
                            <Alert severity="info">
                                {filterVendor
                                    ? 'No pricing history found. Add a new price above.'
                                    : 'Select a vendor to view price history.'}
                            </Alert>
                        ) : (
                            <Box sx={{ overflowX: 'auto' }}>
                                <Table>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Vendor</TableCell>
                                            <TableCell>Item</TableCell>
                                            <TableCell>Price</TableCell>
                                            <TableCell>Effective From</TableCell>
                                            <TableCell>Effective To</TableCell>
                                            <TableCell>Created By</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {priceHistory.map((entry) => (
                                            <TableRow key={entry.id}>
                                                <TableCell>{entry.vendor_name}</TableCell>
                                                <TableCell>{entry.item_name}</TableCell>
                                                <TableCell>₹{Number(entry.price).toFixed(2)}</TableCell>
                                                <TableCell>
                                                    <Box>
                                                        {formatDateForDisplay(entry.effective_from)}
                                                        {isPriceSoon(entry.effective_from) && (
                                                            <Chip
                                                                icon={<WarningIcon />}
                                                                label={`${getDaysUntil(entry.effective_from)} days`}
                                                                color="warning"
                                                                size="small"
                                                                sx={{ ml: 1 }}
                                                            />
                                                        )}
                                                    </Box>
                                                </TableCell>
                                                <TableCell>
                                                    {entry.effective_to ? formatDateForDisplay(entry.effective_to) : 'Indefinite'}
                                                </TableCell>
                                                <TableCell>
                                                    <Typography variant="caption">{entry.created_by || 'N/A'}</Typography>
                                                    <Typography variant="caption" display="block" color="text.secondary">
                                                        {new Date(entry.created_at).toLocaleDateString()}
                                                    </Typography>
                                                </TableCell>
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

export default VendorPricingManager;

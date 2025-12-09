/**
 * B2C Order List Component
 * Version: 1.0.0
 * Last Updated: 2025-12-08
 *
 * Description:
 *   Clone of Order Extractor for B2C Order management
 *   Fetch orders from WooCommerce between dates and export to Excel
 *   - Date range selection (max 31 days)
 *   - Concurrent API fetching with loading states
 *   - Selectable orders with checkboxes
 *   - Two-sheet Excel export (Orders + Item Summary)
 *   - Activity logging for fetch and download
 */

import { useState } from 'react';
import {
    Box,
    Typography,
    Button,
    TextField,
    Paper,
    Alert,
    CircularProgress,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    LinearProgress,
} from '@mui/material';
import {
    Search as SearchIcon,
    Download as DownloadIcon,
    ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridRowSelectionModel } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import { b2cOpsAPI } from '../../api';

interface FetchProgress {
    current: number;
    total: number;
    estimatedTime: number;
}

interface OrderRow {
    id: number;
    sNo: number;
    orderNumber: string;
    date: string;
    customerName: string;
    itemsOrdered: string;
    totalItems: number;
    shippingAddress: string;
    mobileNumber: string;
    customerNotes: string;
    orderTotal: number;
    paymentMethod: string;
    transactionId: string;
    orderStatus: string;
}

export default function B2COrderList() {
    const { enqueueSnackbar } = useSnackbar();

    // State
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [orderStatus, setOrderStatus] = useState<string[]>([]);  // Multi-select array
    const [orders, setOrders] = useState<OrderRow[]>([]);
    const [selectedOrders, setSelectedOrders] = useState<GridRowSelectionModel>([]);
    const [loading, setLoading] = useState(false);
    const [exporting, setExporting] = useState(false);
    const [fetchProgress, setFetchProgress] = useState<FetchProgress>({ current: 0, total: 0, estimatedTime: 0 });

    // Validate date range
    const validateDateRange = () => {
        if (!startDate || !endDate) {
            return { valid: false, message: 'Please select both start and end dates' };
        }

        const start = new Date(startDate);
        const end = new Date(endDate);

        if (start > end) {
            return { valid: false, message: 'Start date cannot be after end date' };
        }

        const daysDiff = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
        if (daysDiff > 31) {
            return { valid: false, message: 'Date range cannot exceed 31 days' };
        }

        return { valid: true };
    };

    // Fetch orders
    const handleFetchOrders = async () => {
        const validation = validateDateRange();
        if (!validation.valid && validation.message) {
            enqueueSnackbar(validation.message, { variant: 'error' });
            return;
        }

        setLoading(true);
        setFetchProgress({ current: 0, total: 100, estimatedTime: 0 });

        // Start progress simulation
        const startTime = Date.now();
        const progressInterval = setInterval(() => {
            setFetchProgress(prev => {
                const elapsed = (Date.now() - startTime) / 1000; // seconds
                const newProgress = Math.min(prev.current + 2, 95); // Cap at 95% until complete
                const estimatedTotal = elapsed / (newProgress / 100) || 0;
                const remaining = Math.max(0, estimatedTotal - elapsed);

                return {
                    current: newProgress,
                    total: 100,
                    estimatedTime: Math.ceil(remaining)
                };
            });
        }, 200);

        try {
            // Convert status array to comma-separated string, or 'any' if empty
            const statusParam = orderStatus.length > 0 ? orderStatus.join(',') : 'any';
            const response = await b2cOpsAPI.fetchOrders(startDate, endDate, statusParam);

            // Transform orders for DataGrid
            const transformedOrders: OrderRow[] = response.orders.map((order: any, idx: number) => {
                // Build items ordered string
                const itemsOrdered = order.line_items
                    .map((item: any) => `${item.name} x ${item.quantity}`)
                    .join(', ');

                // Total items
                const totalItems = order.line_items.reduce((sum: number, item: any) => sum + item.quantity, 0);

                // Shipping address
                const shipping = order.shipping;
                const shippingAddress = [
                    shipping.address_1,
                    shipping.address_2,
                    shipping.city,
                    shipping.state,
                    shipping.postcode,
                    shipping.country
                ].filter(Boolean).join(', ');

                // Customer name
                const billing = order.billing;
                const customerName = `${billing.first_name || ''} ${billing.last_name || ''}`.trim() || 'N/A';

                return {
                    id: order.id,
                    sNo: idx + 1,
                    orderNumber: order.order_number,
                    date: new Date(order.date_created).toLocaleDateString(),
                    customerName,
                    itemsOrdered: itemsOrdered || 'N/A',
                    totalItems,
                    shippingAddress: shippingAddress || 'N/A',
                    mobileNumber: billing.phone || '',
                    customerNotes: order.customer_note || '-',
                    orderTotal: parseFloat(order.total),
                    paymentMethod: order.payment_method_title || '',
                    transactionId: order.transaction_id || '-',
                    orderStatus: order.status,
                };
            });

            // Complete progress
            clearInterval(progressInterval);
            setFetchProgress({ current: 100, total: 100, estimatedTime: 0 });

            setOrders(transformedOrders);
            setSelectedOrders(transformedOrders.map(o => o.id)); // Select all by default
            enqueueSnackbar(`Successfully fetched ${transformedOrders.length} orders!`, { variant: 'success' });
        } catch (error: any) {
            clearInterval(progressInterval);
            setFetchProgress({ current: 0, total: 0, estimatedTime: 0 });
            enqueueSnackbar(error.response?.data?.detail || 'Failed to fetch orders', { variant: 'error' });
        } finally {
            clearInterval(progressInterval);
            setLoading(false);
            setTimeout(() => setFetchProgress({ current: 0, total: 0, estimatedTime: 0 }), 1000);
        }
    };

    // Export orders
    const handleExportOrders = async () => {
        if (selectedOrders.length === 0) {
            enqueueSnackbar('Please select at least one order to export', { variant: 'warning' });
            return;
        }

        setExporting(true);
        try {
            const blob = await b2cOpsAPI.exportOrders(selectedOrders as any[], startDate, endDate);

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `orders_${startDate.replace(/-/g, '')}_${endDate.replace(/-/g, '')}.xlsx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            enqueueSnackbar(`Successfully exported ${selectedOrders.length} orders!`, { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to export orders', { variant: 'error' });
        } finally {
            setExporting(false);
        }
    };

    // DataGrid columns - Status moved to 4th position for display
    const columns: GridColDef[] = [
        { field: 'sNo', headerName: 'S.No', width: 70 },
        { field: 'orderNumber', headerName: 'Order #', width: 100 },
        { field: 'date', headerName: 'Date', width: 110 },
        { field: 'orderStatus', headerName: 'Status', width: 120 },  // Moved to 4th position
        { field: 'customerName', headerName: 'Name', width: 150 },
        { field: 'itemsOrdered', headerName: 'Items Ordered', width: 250 },
        { field: 'totalItems', headerName: 'Total Items', width: 100 },
        { field: 'shippingAddress', headerName: 'Shipping Address', width: 300 },
        { field: 'mobileNumber', headerName: 'Mobile', width: 130 },
        { field: 'customerNotes', headerName: 'Notes', width: 200 },
        { field: 'orderTotal', headerName: 'Total', width: 100, type: 'number' },
        { field: 'paymentMethod', headerName: 'Payment Method', width: 150 },
        { field: 'transactionId', headerName: 'Transaction ID', width: 150 },
    ];

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" gutterBottom fontWeight="bold">
                    📦 B2C Order List
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Fetch and view B2C orders from WooCommerce
                </Typography>
            </Box>

            {/* Date Selection */}
            <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                    📅 Select Date Range & Status
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mt: 2, alignItems: 'center' }}>
                    <TextField
                        label="Start Date"
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        inputProps={{ style: { cursor: 'pointer' } }}
                        onClick={(e) => (e.target as any).showPicker && (e.target as any).showPicker()}
                        fullWidth
                    />
                    <TextField
                        label="End Date"
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        inputProps={{ style: { cursor: 'pointer' } }}
                        onClick={(e) => (e.target as any).showPicker && (e.target as any).showPicker()}
                        fullWidth
                    />
                    <FormControl fullWidth>
                        <InputLabel>Order Status</InputLabel>
                        <Select
                            multiple
                            value={orderStatus}
                            label="Order Status"
                            onChange={(e) => setOrderStatus(typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value)}
                            renderValue={(selected) =>
                                selected.length === 0
                                    ? 'Any Status'
                                    : selected.map(s => s.charAt(0).toUpperCase() + s.slice(1).replace('-', ' ')).join(', ')
                            }
                        >
                            <MenuItem value="processing">Processing</MenuItem>
                            <MenuItem value="pending">Pending Payment</MenuItem>
                            <MenuItem value="on-hold">On Hold</MenuItem>
                            <MenuItem value="completed">Completed</MenuItem>
                            <MenuItem value="cancelled">Cancelled</MenuItem>
                            <MenuItem value="failed">Failed</MenuItem>
                        </Select>
                    </FormControl>
                    <Button
                        variant="contained"
                        startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
                        onClick={handleFetchOrders}
                        disabled={loading}
                        sx={{ minWidth: 150 }}
                    >
                        {loading ? 'Fetching...' : 'Fetch Orders'}
                    </Button>
                </Box>
                <Alert severity="info" sx={{ mt: 2 }}>
                    Maximum date range: 31 days
                </Alert>

                {/* Progress Bar */}
                {loading && fetchProgress.total > 0 && (
                    <Box sx={{ mt: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                                Fetching orders from WooCommerce...
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                {fetchProgress.current}% {fetchProgress.estimatedTime > 0 && `• ~${fetchProgress.estimatedTime}s remaining`}
                            </Typography>
                        </Box>
                        <LinearProgress
                            variant="determinate"
                            value={fetchProgress.current}
                            sx={{ height: 8, borderRadius: 1 }}
                        />
                    </Box>
                )}
            </Paper>

            {/* Orders Table */}
            {orders.length > 0 && (
                <Paper sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">
                            📊 Total Orders Found: {orders.length}
                        </Typography>
                        <Button
                            variant="contained"
                            color="primary"
                            startIcon={exporting ? <CircularProgress size={20} /> : <DownloadIcon />}
                            onClick={handleExportOrders}
                            disabled={exporting || selectedOrders.length === 0}
                        >
                            {exporting ? 'Exporting...' : `Download Selected (${selectedOrders.length})`}
                        </Button>
                    </Box>

                    <Box sx={{ height: 600, width: '100%' }}>
                        <DataGrid
                            rows={orders}
                            columns={columns}
                            checkboxSelection
                            disableRowSelectionOnClick
                            rowSelectionModel={selectedOrders}
                            onRowSelectionModelChange={(newSelection) => setSelectedOrders(newSelection)}
                            initialState={{
                                pagination: { paginationModel: { pageSize: 25 } },
                            }}
                            pageSizeOptions={[10, 25, 50, 100]}
                        />
                    </Box>
                </Paper>
            )}

            {/* Help Section */}
            <Accordion sx={{ mt: 3 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>ℹ️ Help & Instructions</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Typography variant="body2" component="div">
                        <strong>How to use Order Extractor:</strong>
                        <ol>
                            <li><strong>Select Date Range</strong>: Choose start and end dates (max 31 days)</li>
                            <li><strong>Fetch Orders</strong>: Click to retrieve orders from WooCommerce</li>
                            <li><strong>Review Orders</strong>: Check the order list and select which ones to download</li>
                            <li><strong>Download Excel</strong>: Export selected orders to Excel with two sheets:
                                <ul>
                                    <li><strong>Orders Sheet</strong>: Customer details and order information</li>
                                    <li><strong>Item Summary Sheet</strong>: Aggregated item quantities</li>
                                </ul>
                            </li>
                        </ol>

                        <strong>Troubleshooting:</strong>
                        <ul>
                            <li><strong>No orders found</strong>: Check date range and WooCommerce order dates</li>
                            <li><strong>API errors</strong>: Contact admin to verify WooCommerce API credentials</li>
                            <li><strong>Timeout</strong>: Try a shorter date range (fewer orders)</li>
                        </ul>
                    </Typography>
                </AccordionDetails>
            </Accordion>
        </Box>
    );
}

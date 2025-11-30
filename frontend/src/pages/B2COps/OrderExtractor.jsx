/**
 * Order Extractor Component
 * Version: 1.0.0
 * Last Updated: 2025-11-30
 *
 * Description:
 *   Fetch orders from WooCommerce between dates and export to Excel
 *   - Date range selection (max 31 days)
 *   - Concurrent API fetching with loading states
 *   - Selectable orders with checkboxes
 *   - Two-sheet Excel export (Orders + Item Summary)
 *   - Activity logging for fetch and download
 */

import React, { useState } from 'react';
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
} from '@mui/material';
import {
    Search as SearchIcon,
    Download as DownloadIcon,
    ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import { b2cOpsAPI } from '../../api';

export default function OrderExtractor() {
    const { enqueueSnackbar } = useSnackbar();

    // State
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [orders, setOrders] = useState([]);
    const [selectedOrders, setSelectedOrders] = useState([]);
    const [loading, setLoading] = useState(false);
    const [exporting, setExporting] = useState(false);

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

        const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        if (daysDiff > 31) {
            return { valid: false, message: 'Date range cannot exceed 31 days' };
        }

        return { valid: true };
    };

    // Fetch orders
    const handleFetchOrders = async () => {
        const validation = validateDateRange();
        if (!validation.valid) {
            enqueueSnackbar(validation.message, { variant: 'error' });
            return;
        }

        setLoading(true);
        try {
            const response = await b2cOpsAPI.fetchOrders(startDate, endDate);

            // Transform orders for DataGrid
            const transformedOrders = response.orders.map((order, idx) => {
                // Build items ordered string
                const itemsOrdered = order.line_items
                    .map(item => `${item.name} x ${item.quantity}`)
                    .join(', ');

                // Total items
                const totalItems = order.line_items.reduce((sum, item) => sum + item.quantity, 0);

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

            setOrders(transformedOrders);
            setSelectedOrders(transformedOrders.map(o => o.id)); // Select all by default
            enqueueSnackbar(`Successfully fetched ${transformedOrders.length} orders!`, { variant: 'success' });
        } catch (error) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to fetch orders', { variant: 'error' });
        } finally {
            setLoading(false);
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
            const blob = await b2cOpsAPI.exportOrders(selectedOrders, startDate, endDate);

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
        } catch (error) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to export orders', { variant: 'error' });
        } finally {
            setExporting(false);
        }
    };

    // DataGrid columns
    const columns = [
        { field: 'sNo', headerName: 'S.No', width: 70 },
        { field: 'orderNumber', headerName: 'Order #', width: 100 },
        { field: 'date', headerName: 'Date', width: 110 },
        { field: 'customerName', headerName: 'Name', width: 150 },
        { field: 'itemsOrdered', headerName: 'Items Ordered', width: 250 },
        { field: 'totalItems', headerName: 'Total Items', width: 100 },
        { field: 'shippingAddress', headerName: 'Shipping Address', width: 300 },
        { field: 'mobileNumber', headerName: 'Mobile', width: 130 },
        { field: 'customerNotes', headerName: 'Notes', width: 200 },
        { field: 'orderTotal', headerName: 'Total', width: 100, type: 'number' },
        { field: 'paymentMethod', headerName: 'Payment Method', width: 150 },
        { field: 'transactionId', headerName: 'Transaction ID', width: 150 },
        { field: 'orderStatus', headerName: 'Status', width: 120 },
    ];

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" gutterBottom fontWeight="bold">
                    📦 Order Extractor
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Extract orders from WooCommerce between dates and export to Excel
                </Typography>
            </Box>

            {/* Date Selection */}
            <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                    📅 Select Date Range
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mt: 2, alignItems: 'center' }}>
                    <TextField
                        label="Start Date"
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        fullWidth
                    />
                    <TextField
                        label="End Date"
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        fullWidth
                    />
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

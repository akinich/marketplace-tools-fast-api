/**
 * B2C Orders Component (Simplified)
 * Version: 3.0.0
 * Created: 2025-12-08
 *
 * Description:
 *   Simple order management interface modeled after Order Extractor
 *   - Two sync options: Quick (last 3 days) + Custom date range
 *   - Order listing with pagination
 *   - Order details dialog
 *   - No stats, no export, no automated sync
 */

import { useState } from 'react';
import {
    Box,
    Typography,
    Button,
    Paper,
    Alert,
    CircularProgress,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    MenuItem,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TablePagination,
    Chip,
    IconButton,
    Grid,
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    Visibility as ViewIcon,
    CalendarToday as CalendarIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useSnackbar } from 'notistack';
import axios from 'axios';

const API_BASE_URL = window.location.origin.includes('localhost')
    ? 'http://localhost:8000/api/v1'
    : `${window.location.origin}/api/v1`;

interface Order {
    id: number;
    woo_order_id: number;
    order_number: string;
    status: string;
    date_created: string;
    customer_id?: number;
    billing: {
        first_name?: string;
        last_name?: string;
        email?: string;
        phone?: string;
    };
    shipping: {
        address_1?: string;
        city?: string;
        state?: string;
        postcode?: string;
    };
    total: number;
    payment_method_title?: string;
    line_items?: Array<{
        name: string;
        quantity: number;
        total: number;
    }>;
}

export default function B2COrders() {
    const { enqueueSnackbar } = useSnackbar();
    const queryClient = useQueryClient();

    const [statusFilter, setStatusFilter] = useState<string>('');
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(25);
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
    const [detailsOpen, setDetailsOpen] = useState(false);
    const [customSyncOpen, setCustomSyncOpen] = useState(false);
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    // Fetch orders from database
    const { data: ordersData, isLoading, error, refetch } = useQuery(
        ['b2c-orders', statusFilter, page, rowsPerPage],
        async () => {
            const params = new URLSearchParams({
                page: String(page + 1),
                limit: String(rowsPerPage),
            });
            if (statusFilter) params.append('status', statusFilter);

            const response = await axios.get(`${API_BASE_URL}/orders?${params}`, {
                headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
            });
            return response.data;
        },
        {
            retry: 1,
            refetchOnWindowFocus: false,
            onError: (error: any) => {
                console.error('Error fetching orders:', error);
                enqueueSnackbar(
                    error.response?.data?.detail || 'Failed to load orders',
                    { variant: 'error' }
                );
            },
        }
    );

    // Quick sync: last 3 days
    const quickSyncMutation = useMutation(
        async () => {
            console.log('[B2C Orders] Starting quick sync...');
            const response = await axios.post(
                `${API_BASE_URL}/orders/sync`,
                {},  // Empty body = defaults to last 3 days
                { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } }
            );
            console.log('[B2C Orders] Sync response:', response.data);
            return response.data;
        },
        {
            onSuccess: (data) => {
                console.log('[B2C Orders] Sync success data:', data);
                const synced = data?.synced || 0;
                const created = data?.created || 0;
                const updated = data?.updated || 0;

                enqueueSnackbar(
                    `Synced ${synced} orders (${created} created, ${updated} updated)`,
                    { variant: 'success' }
                );
                queryClient.invalidateQueries('b2c-orders');
            },
            onError: (error: any) => {
                console.error('[B2C Orders] Sync error:', error);
                enqueueSnackbar(error.response?.data?.detail || 'Failed to sync orders', {
                    variant: 'error',
                });
            },
        }
    );

    // Custom range sync
    const customSyncMutation = useMutation(
        async () => {
            console.log('[B2C Orders] Starting custom sync:', startDate, 'to', endDate);
            const response = await axios.post(
                `${API_BASE_URL}/orders/sync`,
                { start_date: startDate, end_date: endDate },
                { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } }
            );
            console.log('[B2C Orders] Custom sync response:', response.data);
            return response.data;
        },
        {
            onSuccess: (data) => {
                console.log('[B2C Orders] Custom sync success:', data);
                const synced = data?.synced || 0;
                const created = data?.created || 0;
                const updated = data?.updated || 0;

                enqueueSnackbar(
                    `Synced ${synced} orders (${created} created, ${updated} updated)`,
                    { variant: 'success' }
                );
                queryClient.invalidateQueries('b2c-orders');
                setCustomSyncOpen(false);
            },
            onError: (error: any) => {
                console.error('[B2C Orders] Custom sync error:', error);
                enqueueSnackbar(error.response?.data?.detail || 'Failed to sync orders', {
                    variant: 'error',
                });
            },
        }
    );

    // View order details
    const handleViewDetails = async (orderId: number) => {
        try {
            const response = await axios.get(`${API_BASE_URL}/orders/${orderId}`, {
                headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
            });
            setSelectedOrder(response.data);
            setDetailsOpen(true);
        } catch (error: any) {
            enqueueSnackbar('Failed to load order details', { variant: 'error' });
        }
    };

    const getStatusColor = (status: string): 'default' | 'primary' | 'success' | 'warning' | 'error' => {
        const colors: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error'> = {
            pending: 'warning',
            processing: 'primary',
            completed: 'success',
            cancelled: 'error',
            refunded: 'default',
            failed: 'error',
            'on-hold': 'warning',
        };
        return colors[status] || 'default';
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    B2C Orders
                </Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                        variant="contained"
                        startIcon={<RefreshIcon />}
                        onClick={() => quickSyncMutation.mutate()}
                        disabled={quickSyncMutation.isLoading}
                    >
                        {quickSyncMutation.isLoading ? 'Syncing...' : 'Sync Last 3 Days'}
                    </Button>
                    <Button
                        variant="outlined"
                        startIcon={<CalendarIcon />}
                        onClick={() => setCustomSyncOpen(true)}
                    >
                        Custom Range
                    </Button>
                    <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => refetch()}>
                        Refresh
                    </Button>
                </Box>
            </Box>

            {/* Error State */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    Failed to load orders. Please try refreshing the page.
                </Alert>
            )}

            {/* Filters */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                        <TextField
                            select
                            fullWidth
                            label="Status"
                            value={statusFilter}
                            onChange={(e) => {
                                setStatusFilter(e.target.value);
                                setPage(0);
                            }}
                        >
                            <MenuItem value="">All Statuses</MenuItem>
                            <MenuItem value="pending">Pending</MenuItem>
                            <MenuItem value="processing">Processing</MenuItem>
                            <MenuItem value="on-hold">On Hold</MenuItem>
                            <MenuItem value="completed">Completed</MenuItem>
                            <MenuItem value="cancelled">Cancelled</MenuItem>
                            <MenuItem value="refunded">Refunded</MenuItem>
                            <MenuItem value="failed">Failed</MenuItem>
                        </TextField>
                    </Grid>
                </Grid>
            </Paper>

            {/* Orders Table */}
            <Paper>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Order #</TableCell>
                                <TableCell>Date</TableCell>
                                <TableCell>Customer</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell align="right">Total</TableCell>
                                <TableCell>Payment</TableCell>
                                <TableCell align="center">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={7} align="center">
                                        <CircularProgress />
                                    </TableCell>
                                </TableRow>
                            ) : ordersData?.orders?.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={7} align="center">
                                        <Typography variant="body2" color="text.secondary">
                                            No orders found
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                ordersData?.orders?.map((order: Order) => (
                                    <TableRow key={order.id} hover>
                                        <TableCell>#{order.order_number}</TableCell>
                                        <TableCell>
                                            {new Date(order.date_created).toLocaleDateString()}
                                        </TableCell>
                                        <TableCell>
                                            {order.billing?.first_name} {order.billing?.last_name}
                                            <br />
                                            <Typography variant="caption" color="text.secondary">
                                                {order.billing?.email}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={order.status}
                                                color={getStatusColor(order.status)}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell align="right">₹{(order.total || 0).toLocaleString()}</TableCell>
                                        <TableCell>{order.payment_method_title || '-'}</TableCell>
                                        <TableCell align="center">
                                            <IconButton
                                                size="small"
                                                onClick={() => handleViewDetails(order.id)}
                                            >
                                                <ViewIcon />
                                            </IconButton>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
                <TablePagination
                    component="div"
                    count={ordersData?.total || 0}
                    page={page}
                    onPageChange={(_, newPage) => setPage(newPage)}
                    rowsPerPage={rowsPerPage}
                    onRowsPerPageChange={(e) => {
                        setRowsPerPage(parseInt(e.target.value, 10));
                        setPage(0);
                    }}
                    rowsPerPageOptions={[10, 25, 50, 100]}
                />
            </Paper>

            {/* Custom Range Sync Dialog */}
            <Dialog open={customSyncOpen} onClose={() => setCustomSyncOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Sync Custom Date Range</DialogTitle>
                <DialogContent>
                    <Alert severity="info" sx={{ mb: 2 }}>
                        Select a date range to fetch orders from WooCommerce.
                    </Alert>
                    <Grid container spacing={2} sx={{ mt: 1 }}>
                        <Grid item xs={6}>
                            <TextField
                                fullWidth
                                type="date"
                                label="Start Date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                InputLabelProps={{ shrink: true }}
                            />
                        </Grid>
                        <Grid item xs={6}>
                            <TextField
                                fullWidth
                                type="date"
                                label="End Date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                InputLabelProps={{ shrink: true }}
                            />
                        </Grid>
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCustomSyncOpen(false)}>Cancel</Button>
                    <Button
                        variant="contained"
                        onClick={() => customSyncMutation.mutate()}
                        disabled={!startDate || !endDate || customSyncMutation.isLoading}
                    >
                        {customSyncMutation.isLoading ? 'Syncing...' : 'Sync'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Order Details Dialog */}
            <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>Order Details - #{selectedOrder?.order_number}</DialogTitle>
                <DialogContent>
                    {selectedOrder && (
                        <Box>
                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={6}>
                                    <Typography variant="subtitle2" color="text.secondary">
                                        Customer
                                    </Typography>
                                    <Typography>
                                        {selectedOrder.billing?.first_name} {selectedOrder.billing?.last_name}
                                    </Typography>
                                    <Typography variant="body2">{selectedOrder.billing?.email}</Typography>
                                    <Typography variant="body2">{selectedOrder.billing?.phone}</Typography>
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <Typography variant="subtitle2" color="text.secondary">
                                        Shipping Address
                                    </Typography>
                                    <Typography variant="body2">
                                        {selectedOrder.shipping?.address_1}
                                        <br />
                                        {selectedOrder.shipping?.city}, {selectedOrder.shipping?.state}{' '}
                                        {selectedOrder.shipping?.postcode}
                                    </Typography>
                                </Grid>
                                <Grid item xs={12}>
                                    <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>
                                        Order Items
                                    </Typography>
                                    <TableContainer>
                                        <Table size="small">
                                            <TableHead>
                                                <TableRow>
                                                    <TableCell>Item</TableCell>
                                                    <TableCell align="right">Qty</TableCell>
                                                    <TableCell align="right">Total</TableCell>
                                                </TableRow>
                                            </TableHead>
                                            <TableBody>
                                                {selectedOrder.line_items?.map((item, idx) => (
                                                    <TableRow key={idx}>
                                                        <TableCell>{item.name}</TableCell>
                                                        <TableCell align="right">{item.quantity}</TableCell>
                                                        <TableCell align="right">
                                                            ₹{(item.total || 0).toLocaleString()}
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    </TableContainer>
                                </Grid>
                            </Grid>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDetailsOpen(false)}>Close</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}

/**
 * B2C Orders Management Page
 * Version: 1.0.0
 * Created: 2025-12-07
 *
 * Description:
 *   Manage WooCommerce B2C orders synced via webhooks and API
 *   - View orders list with filtering
 *   - Order statistics dashboard
 *   - Manual sync from WooCommerce
 *   - Export orders to Excel
 *   - View order details
 */

import { useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    TextField,
    MenuItem,
    Grid,
    Card,
    CardContent,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TablePagination,
    Chip,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    CircularProgress,
    Alert,
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    Download as DownloadIcon,
    Visibility as ViewIcon,
    ShoppingCart as OrdersIcon,
    TrendingUp as RevenueIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useSnackbar } from 'notistack';
import axios from 'axios';

const API_BASE_URL = window.location.origin.includes('localhost')
    ? 'http://localhost:8000/api'
    : `${window.location.origin}/api`;

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

interface OrderStats {
    total_orders: number;
    pending_orders: number;
    processing_orders: number;
    completed_orders: number;
    cancelled_orders: number;
    total_revenue: number;
    average_order_value: number;
}

export default function B2COrders() {
    const { enqueueSnackbar } = useSnackbar();
    const queryClient = useQueryClient();

    const [statusFilter, setStatusFilter] = useState<string>('');
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(25);
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
    const [detailsOpen, setDetailsOpen] = useState(false);
    const [syncDialogOpen, setSyncDialogOpen] = useState(false);
    const [syncDays, setSyncDays] = useState(3);

    // Fetch orders
    const { data: ordersData, isLoading: ordersLoading, error: ordersError, refetch: refetchOrders } = useQuery(
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

    // Fetch stats
    const { data: stats, error: statsError } = useQuery<OrderStats>(
        'b2c-orders-stats',
        async () => {
            const response = await axios.get(`${API_BASE_URL}/orders/stats`, {
                headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
            });
            return response.data;
        },
        {
            retry: 1,
            refetchOnWindowFocus: false,
            onError: (error: any) => {
                console.error('Error fetching stats:', error);
                // Don't show error for stats, just log it
            },
        }
    );

    // Sync orders mutation
    const syncMutation = useMutation(
        async (days: number) => {
            const response = await axios.post(
                `${API_BASE_URL}/orders/sync`,
                { days, force_full_sync: false },
                { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } }
            );
            return response.data;
        },
        {
            onSuccess: (data) => {
                enqueueSnackbar(
                    `Synced ${data.synced} orders (${data.created} created, ${data.updated} updated)`,
                    { variant: 'success' }
                );
                queryClient.invalidateQueries('b2c-orders');
                queryClient.invalidateQueries('b2c-orders-stats');
                setSyncDialogOpen(false);
            },
            onError: (error: any) => {
                enqueueSnackbar(error.response?.data?.detail || 'Failed to sync orders', {
                    variant: 'error',
                });
            },
        }
    );

    // Export orders
    const handleExport = async () => {
        try {
            const params: any = {};
            if (statusFilter) params.status = statusFilter;

            const response = await axios.post(`${API_BASE_URL}/orders/export`, params, {
                headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
                responseType: 'blob',
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `orders_export_${new Date().toISOString().split('T')[0]}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();

            enqueueSnackbar('Orders exported successfully', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to export orders', {
                variant: 'error',
            });
        }
    };

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

    const getStatusColor = (status: string) => {
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
                        variant="outlined"
                        startIcon={<RefreshIcon />}
                        onClick={() => setSyncDialogOpen(true)}
                    >
                        Sync from WooCommerce
                    </Button>
                    <Button
                        variant="outlined"
                        startIcon={<DownloadIcon />}
                        onClick={handleExport}
                        disabled={!ordersData?.orders?.length}
                    >
                        Export to Excel
                    </Button>
                    <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => refetchOrders()}>
                        Refresh
                    </Button>
                </Box>
            </Box>

            {/* Error State */}
            {ordersError && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    Failed to load orders. Please try refreshing the page or contact support if the issue persists.
                </Alert>
            )}

            {/* Statistics Cards */}
            {stats && (
                <Grid container spacing={3} sx={{ mb: 3 }}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <OrdersIcon color="primary" sx={{ fontSize: 40 }} />
                                    <Box>
                                        <Typography variant="h4">{stats.total_orders}</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Total Orders
                                        </Typography>
                                    </Box>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <RevenueIcon color="success" sx={{ fontSize: 40 }} />
                                    <Box>
                                        <Typography variant="h4">₹{(stats.total_revenue || 0).toLocaleString()}</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Total Revenue
                                        </Typography>
                                    </Box>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6">Pending: {stats.pending_orders}</Typography>
                                <Typography variant="body2">Processing: {stats.processing_orders}</Typography>
                                <Typography variant="body2">Completed: {stats.completed_orders}</Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Typography variant="h4">₹{stats.average_order_value.toFixed(2)}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Avg Order Value
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
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
                            {ordersLoading ? (
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

            {/* Sync Dialog */}
            <Dialog open={syncDialogOpen} onClose={() => setSyncDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Sync Orders from WooCommerce</DialogTitle>
                <DialogContent>
                    <Alert severity="info" sx={{ mb: 2 }}>
                        This will fetch recent orders from WooCommerce and update the database.
                    </Alert>
                    <TextField
                        fullWidth
                        type="number"
                        label="Number of days to sync"
                        value={syncDays}
                        onChange={(e) => setSyncDays(parseInt(e.target.value) || 3)}
                        inputProps={{ min: 1, max: 90 }}
                        helperText="Sync orders from the last N days (1-90)"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setSyncDialogOpen(false)}>Cancel</Button>
                    <Button
                        variant="contained"
                        onClick={() => syncMutation.mutate(syncDays)}
                        disabled={syncMutation.isLoading}
                    >
                        {syncMutation.isLoading ? 'Syncing...' : 'Start Sync'}
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

/**
 * Sales Orders List Page
 * Version: 1.0.0
 * Created: 2025-12-07
 *
 * Dashboard for viewing and managing sales orders
 */

import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Card,
    Chip,
    TextField,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Typography,
    IconButton,
    Tooltip,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
    Add as AddIcon,
    Visibility as ViewIcon,
    PictureAsPdf as PdfIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { salesOrdersAPI } from '../../../api/salesOrders';
import { SalesOrder, SalesOrderListFilters, SalesOrderStatus } from '../../../types/SalesOrder';
import { formatDateForDisplay } from '../../../utils/dateUtils';

const SalesOrderList: React.FC = () => {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();

    const [orders, setOrders] = useState<SalesOrder[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [filters, setFilters] = useState<SalesOrderListFilters>({
        page: 1,
        limit: 20,
    });

    // Status color mapping
    const getStatusColor = (status: SalesOrderStatus): 'default' | 'info' | 'warning' | 'success' | 'secondary' => {
        const muiColors: Record<string, 'default' | 'info' | 'warning' | 'success' | 'secondary'> = {
            [SalesOrderStatus.DRAFT]: 'default',
            [SalesOrderStatus.CONFIRMED]: 'info',
            [SalesOrderStatus.PACKING]: 'warning', // Reuse warning
            [SalesOrderStatus.SHIPPED]: 'info', // Reuse info or primary if available, but staying safe with info/warning/success
            [SalesOrderStatus.COMPLETED]: 'success',
            [SalesOrderStatus.CANCELLED]: 'secondary', // or error
            [SalesOrderStatus.EXPORTED_TO_ZOHO]: 'default',
        };

        // Custom logic if we want to force explicit colors not in the standard set
        if (status === SalesOrderStatus.SHIPPED) return 'info';
        if (status === SalesOrderStatus.CANCELLED) return 'secondary';

        return muiColors[status] || 'default';
    };

    // Format status for display
    const formatStatus = (status: string): string => {
        return status.replace(/_/g, ' ').toUpperCase();
    };

    // Load Orders
    const loadOrders = async () => {
        setLoading(true);
        try {
            const response = await salesOrdersAPI.getOrders(filters);
            setOrders(response.orders);
            setTotal(response.total);
        } catch (error: any) {
            console.error('Failed to load sales orders:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load sales orders', {
                variant: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadOrders();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filters]);

    // DataGrid columns
    const columns: GridColDef[] = [
        {
            field: 'so_number',
            headerName: 'SO #',
            width: 140,
            renderCell: (params) => (
                <Typography
                    variant="body2"
                    sx={{ cursor: 'pointer', color: 'primary.main', fontWeight: 500 }}
                    onClick={() => navigate(`/outward/sales-orders/${params.row.id}`)}
                >
                    {params.value}
                </Typography>
            ),
        },
        { field: 'customer_name', headerName: 'Customer', width: 200 },
        { field: 'order_source', headerName: 'Source', width: 130 },
        {
            field: 'order_date',
            headerName: 'Order Date',
            width: 130,
            valueFormatter: (params) => formatDateForDisplay(params.value),
        },
        {
            field: 'delivery_date',
            headerName: 'Delivery Date',
            width: 130,
            valueFormatter: (params) => params.value ? formatDateForDisplay(params.value) : '-',
        },
        {
            field: 'status',
            headerName: 'Status',
            width: 150,
            renderCell: (params) => (
                <Chip
                    label={formatStatus(params.value)}
                    color={getStatusColor(params.value)}
                    size="small"
                    variant={params.value === SalesOrderStatus.DRAFT ? 'outlined' : 'filled'}
                />
            ),
        },
        {
            field: 'total_amount',
            headerName: 'Amount (₹)',
            width: 130,
            valueFormatter: (params) => `₹${Number(params.value).toFixed(2)}`,
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 150,
            sortable: false,
            renderCell: (params) => (
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="View/Edit">
                        <IconButton
                            size="small"
                            onClick={() => navigate(`/outward/sales-orders/${params.row.id}`)}
                        >
                            <ViewIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                    {/* Placeholder for future PDF generation */}
                    <Tooltip title="Download PDF">
                        <IconButton size="small" disabled>
                            <PdfIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                </Box>
            ),
        },
    ];

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4" component="h1">
                    Sales Orders
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => navigate('/outward/sales-orders/new')}
                >
                    Create New Order
                </Button>
            </Box>

            {/* Filters */}
            <Card sx={{ p: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <FormControl sx={{ minWidth: 200 }}>
                        <InputLabel>Status</InputLabel>
                        <Select
                            value={filters.status || ''}
                            label="Status"
                            onChange={(e) => setFilters({ ...filters, status: e.target.value as SalesOrderStatus, page: 1 })}
                        >
                            <MenuItem value="">All</MenuItem>
                            <MenuItem value={SalesOrderStatus.DRAFT}>Draft</MenuItem>
                            <MenuItem value={SalesOrderStatus.CONFIRMED}>Confirmed</MenuItem>
                            <MenuItem value={SalesOrderStatus.PACKING}>Packing</MenuItem>
                            <MenuItem value={SalesOrderStatus.SHIPPED}>Shipped</MenuItem>
                            <MenuItem value={SalesOrderStatus.COMPLETED}>Completed</MenuItem>
                            <MenuItem value={SalesOrderStatus.EXPORTED_TO_ZOHO}>Exported to Zoho</MenuItem>
                            <MenuItem value={SalesOrderStatus.CANCELLED}>Cancelled</MenuItem>
                        </Select>
                    </FormControl>

                    <TextField
                        label="From Date"
                        type="date"
                        value={filters.from_date || ''}
                        onChange={(e) => setFilters({ ...filters, from_date: e.target.value, page: 1 })}
                        InputLabelProps={{ shrink: true }}
                        sx={{ minWidth: 180 }}
                    />

                    <TextField
                        label="To Date"
                        type="date"
                        value={filters.to_date || ''}
                        onChange={(e) => setFilters({ ...filters, to_date: e.target.value, page: 1 })}
                        InputLabelProps={{ shrink: true }}
                        sx={{ minWidth: 180 }}
                    />

                    {filters.status || filters.from_date || filters.to_date ? (
                        <Button
                            variant="outlined"
                            onClick={() => setFilters({ page: 1, limit: 20 })}
                        >
                            Clear Filters
                        </Button>
                    ) : null}
                </Box>
            </Card>

            {/* DataGrid */}
            <Card>
                <DataGrid
                    rows={orders}
                    columns={columns}
                    loading={loading}
                    pageSizeOptions={[20, 50, 100]}
                    paginationMode="server"
                    rowCount={total}
                    paginationModel={{ page: filters.page! - 1, pageSize: filters.limit! }}
                    onPaginationModelChange={(model) =>
                        setFilters({ ...filters, page: model.page + 1, limit: model.pageSize })
                    }
                    autoHeight
                    disableRowSelectionOnClick
                    sx={{
                        '& .MuiDataGrid-cell:focus': {
                            outline: 'none',
                        },
                    }}
                />
            </Card>
        </Box>
    );
};

export default SalesOrderList;

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
        const colors: Record<SalesOrderStatus, 'default' | 'info' | 'warning' | 'success' | 'secondary'> = {
            [SalesOrderStatus.DRAFT]: 'default',
            [SalesOrderStatus.CONFIRMED]: 'info',
            [SalesOrderStatus.PACKING]: 'warning', // Use warning for in-progress
            [SalesOrderStatus.SHIPPED]: 'primary' as any, // Mui Chip supports primary, but types might be strict. Using warning/info logic
            [SalesOrderStatus.COMPLETED]: 'success',
            [SalesOrderStatus.CANCELLED]: 'error' as any,
            [SalesOrderStatus.EXPORTED_TO_ZOHO]: 'default', // Grey for exported
        };
        // Fallback for valid Mui Chip colors
        const muiColors: Record<string, 'default' | 'info' | 'warning' | 'success' | 'secondary' | 'primary' | 'error'> = {
            [SalesOrderStatus.DRAFT]: 'default',
            [SalesOrderStatus.CONFIRMED]: 'info',
            [SalesOrderStatus.PACKING]: 'warning',
            [SalesOrderStatus.SHIPPED]: 'primary',
            [SalesOrderStatus.COMPLETED]: 'success',
            [SalesOrderStatus.CANCELLED]: 'error',
            [SalesOrderStatus.EXPORTED_TO_ZOHO]: 'secondary',
        };
        return (muiColors[status] as any) || 'default';
    };

    // Format status for display
    const formatStatus = (status: string): string => {
        return status.replace(/_/g, ' ').toUpperCase();
    };

    // ... (loadOrders code remains) ...

    // DataGrid columns
    const columns: GridColDef[] = [
        // ... (previous columns) ...
        {
            field: 'status',
            headerName: 'Status',
            width: 140,
            renderCell: (params) => (
                <Chip
                    label={formatStatus(params.value)}
                    color={getStatusColor(params.value)}
                    size="small"
                />
            ),
        },
        // ...
    ];

    return (
        <Box sx={{ p: 3 }}>
            {/* ... */}
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

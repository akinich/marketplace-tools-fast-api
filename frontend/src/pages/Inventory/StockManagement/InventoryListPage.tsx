/**
 * Inventory List Page
 * Version: 1.0.0
 * Created: 2024-12-12
 *
 * Main dashboard for viewing and managing inventory stock across locations
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
    Alert,
} from '@mui/material';
import { DataGrid, GridColDef, useGridApiRef } from '@mui/x-data-grid';
import {
    Add as AddIcon,
    Visibility as ViewIcon,
    SwapHoriz as TransferIcon,
    Edit as EditIcon,
    Fullscreen as FullscreenIcon,
    FullscreenExit as FullscreenExitIcon,
    Warning as WarningIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { inventoryAPI } from '../../../api/inventory';
import { formatDateForDisplay } from '../../../utils/dateUtils';
import ManualStockEntryModal from './components/ManualStockEntryModal';

interface InventoryItem {
    id: number;
    item_id: number;
    item_name: string;
    item_sku: string;
    batch_id: number;
    batch_number: string;
    location: string;
    quantity: number;
    grade?: string;
    status: string;
    shelf_life_days?: number;
    entry_date: string;
    expiry_date?: string;
    days_until_expiry?: number;
    created_at: string;
}

const InventoryListPage: React.FC = () => {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const gridRef = useGridApiRef();

    const [inventory, setInventory] = useState<InventoryItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [showAddModal, setShowAddModal] = useState(false);
    const [filters, setFilters] = useState({
        location: '',
        status: '',
        grade: '',
        expiring_within_days: '',
        page: 1,
        limit: 20,
    });

    // Location options
    const locations = [
        { value: 'receiving_area', label: 'Receiving Area' },
        { value: 'processing_area', label: 'Processing Area' },
        { value: 'packed_warehouse', label: 'Packed Warehouse' },
        { value: 'delivery_vehicles', label: 'Delivery Vehicles' },
        { value: 'quality_hold', label: 'Quality Hold' },
    ];

    // Status options
    const statuses = [
        { value: 'available', label: 'Available' },
        { value: 'allocated', label: 'Allocated' },
        { value: 'hold', label: 'Hold' },
        { value: 'in_transit', label: 'In Transit' },
        { value: 'delivered', label: 'Delivered' },
    ];

    // Status color mapping
    const getStatusColor = (status: string): 'default' | 'success' | 'warning' | 'info' | 'error' => {
        const colors: Record<string, 'default' | 'success' | 'warning' | 'info' | 'error'> = {
            available: 'success',
            allocated: 'info',
            hold: 'warning',
            in_transit: 'info',
            delivered: 'default',
        };
        return colors[status] || 'default';
    };

    // Location color mapping
    const getLocationColor = (location: string): 'default' | 'primary' | 'secondary' => {
        const colors: Record<string, 'default' | 'primary' | 'secondary'> = {
            receiving_area: 'default',
            processing_area: 'secondary',
            packed_warehouse: 'primary',
            delivery_vehicles: 'secondary',
            quality_hold: 'default',
        };
        return colors[location] || 'default';
    };

    // Format location for display
    const formatLocation = (location: string): string => {
        return location.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    // Load inventory
    const loadInventory = async () => {
        setLoading(true);
        try {
            const params: any = { ...filters };
            // Clean up empty filters
            Object.keys(params).forEach(key => {
                if (params[key] === '') delete params[key];
            });

            const response = await inventoryAPI.list(params);
            setInventory(response.items);
            setTotal(response.total);
        } catch (error: any) {
            console.error('Failed to load inventory:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load inventory', {
                variant: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadInventory();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filters]);

    // DataGrid columns
    const columns: GridColDef[] = [
        {
            field: 'batch_number',
            headerName: 'Batch',
            width: 110,
            renderCell: (params) => (
                <Typography
                    variant="body2"
                    sx={{ cursor: 'pointer', color: 'primary.main', fontWeight: 500 }}
                    onClick={() => navigate(`/inventory/stock/batch/${params.row.batch_id}`)}
                >
                    {params.value}
                </Typography>
            ),
        },
        {
            field: 'item_name',
            headerName: 'Item',
            width: 200,
            renderCell: (params) => (
                <Box>
                    <Typography variant="body2">{params.value}</Typography>
                    <Typography variant="caption" color="text.secondary">
                        {params.row.item_sku}
                    </Typography>
                </Box>
            ),
        },
        {
            field: 'location',
            headerName: 'Location',
            width: 160,
            renderCell: (params) => (
                <Chip
                    label={formatLocation(params.value)}
                    color={getLocationColor(params.value)}
                    size="small"
                />
            ),
        },
        {
            field: 'quantity',
            headerName: 'Quantity',
            width: 100,
            valueFormatter: (params) => `${Number(params.value).toFixed(2)}`,
        },
        {
            field: 'grade',
            headerName: 'Grade',
            width: 80,
            renderCell: (params) => params.value ? (
                <Chip label={params.value} size="small" variant="outlined" />
            ) : null,
        },
        {
            field: 'status',
            headerName: 'Status',
            width: 120,
            renderCell: (params) => (
                <Chip
                    label={params.value.replace(/_/g, ' ').toUpperCase()}
                    color={getStatusColor(params.value)}
                    size="small"
                />
            ),
        },
        {
            field: 'expiry_date',
            headerName: 'Expiry Date',
            width: 130,
            renderCell: (params) => {
                if (!params.value) return null;
                const days = params.row.days_until_expiry;
                const isExpiring = days !== null && days < 7;
                const isCritical = days !== null && days < 2;

                return (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        {isExpiring && (
                            <WarningIcon
                                sx={{
                                    fontSize: 16,
                                    color: isCritical ? 'error.main' : 'warning.main'
                                }}
                            />
                        )}
                        <Typography
                            variant="body2"
                            color={isCritical ? 'error' : isExpiring ? 'warning' : 'inherit'}
                        >
                            {formatDateForDisplay(params.value)}
                        </Typography>
                    </Box>
                );
            },
        },
        {
            field: 'entry_date',
            headerName: 'Entry Date',
            width: 130,
            valueFormatter: (params) => formatDateForDisplay(params.value),
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 150,
            sortable: false,
            renderCell: (params) => (
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="View Batch">
                        <IconButton
                            size="small"
                            onClick={() => navigate(`/inventory/stock/batch/${params.row.batch_id}`)}
                        >
                            <ViewIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                    {params.row.status === 'available' && (
                        <Tooltip title="Transfer Location">
                            <IconButton
                                size="small"
                                color="primary"
                                onClick={() => {/* TODO: Transfer modal */ }}
                            >
                                <TransferIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    )}
                    <Tooltip title="Adjust Stock">
                        <IconButton
                            size="small"
                            onClick={() => navigate('/inventory/stock/adjustments?create=true')}
                        >
                            <EditIcon fontSize="small" />
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
                <Box>
                    <Typography variant="h4" component="h1">
                        Stock Management
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        View and manage inventory across all locations
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setShowAddModal(true)}
                >
                    Add Stock
                </Button>
            </Box>

            {/* Expiring items alert */}
            {inventory.some(item => item.days_until_expiry !== null && item.days_until_expiry < 2) && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    <strong>Critical:</strong> {inventory.filter(i => i.days_until_expiry !== null && i.days_until_expiry < 2).length} item(s) expiring within 2 days!
                    <Button size="small" sx={{ ml: 2 }} onClick={() => setFilters({ ...filters, expiring_within_days: '2' })}>
                        View Expiring Items
                    </Button>
                </Alert>
            )}

            {/* Filters */}
            <Card sx={{ p: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <FormControl sx={{ minWidth: 200 }}>
                        <InputLabel>Location</InputLabel>
                        <Select
                            value={filters.location}
                            label="Location"
                            onChange={(e) => setFilters({ ...filters, location: e.target.value, page: 1 })}
                        >
                            <MenuItem value="">All Locations</MenuItem>
                            {locations.map(loc => (
                                <MenuItem key={loc.value} value={loc.value}>{loc.label}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <FormControl sx={{ minWidth: 180 }}>
                        <InputLabel>Status</InputLabel>
                        <Select
                            value={filters.status}
                            label="Status"
                            onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}
                        >
                            <MenuItem value="">All Statuses</MenuItem>
                            {statuses.map(status => (
                                <MenuItem key={status.value} value={status.value}>{status.label}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <FormControl sx={{ minWidth: 120 }}>
                        <InputLabel>Grade</InputLabel>
                        <Select
                            value={filters.grade}
                            label="Grade"
                            onChange={(e) => setFilters({ ...filters, grade: e.target.value, page: 1 })}
                        >
                            <MenuItem value="">All Grades</MenuItem>
                            <MenuItem value="A">Grade A</MenuItem>
                            <MenuItem value="B">Grade B</MenuItem>
                            <MenuItem value="C">Grade C</MenuItem>
                        </Select>
                    </FormControl>

                    <FormControl sx={{ minWidth: 180 }}>
                        <InputLabel>Expiring Within</InputLabel>
                        <Select
                            value={filters.expiring_within_days}
                            label="Expiring Within"
                            onChange={(e) => setFilters({ ...filters, expiring_within_days: e.target.value, page: 1 })}
                        >
                            <MenuItem value="">All Items</MenuItem>
                            <MenuItem value="2">2 Days</MenuItem>
                            <MenuItem value="7">7 Days</MenuItem>
                            <MenuItem value="14">14 Days</MenuItem>
                        </Select>
                    </FormControl>

                    {(filters.location || filters.status || filters.grade || filters.expiring_within_days) && (
                        <Button
                            variant="outlined"
                            onClick={() => setFilters({ location: '', status: '', grade: '', expiring_within_days: '', page: 1, limit: 20 })}
                        >
                            Clear Filters
                        </Button>
                    )}
                </Box>
            </Card>

            {/* Quick Stats */}
            <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
                <Card sx={{ p: 2, flex: 1, minWidth: 200 }}>
                    <Typography variant="caption" color="text.secondary">Total Items</Typography>
                    <Typography variant="h5">{total}</Typography>
                </Card>
                <Card sx={{ p: 2, flex: 1, minWidth: 200, cursor: 'pointer' }}
                    onClick={() => navigate('/inventory/stock/reports')}>
                    <Typography variant="caption" color="text.secondary">View Reports</Typography>
                    <Typography variant="h6" color="primary">Reports →</Typography>
                </Card>
                <Card sx={{ p: 2, flex: 1, minWidth: 200, cursor: 'pointer' }}
                    onClick={() => navigate('/inventory/stock/movements')}>
                    <Typography variant="caption" color="text.secondary">Stock Movements</Typography>
                    <Typography variant="h6" color="primary">View →</Typography>
                </Card>
            </Box>

            {/* DataGrid */}
            <Card>
                <Box sx={{
                    height: isFullscreen ? '100vh' : 'auto',
                    width: '100%',
                    ...(isFullscreen && {
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        zIndex: 9999,
                        bgcolor: 'background.paper',
                    })
                }}>
                    <DataGrid
                        apiRef={gridRef}
                        rows={inventory}
                        columns={columns}
                        loading={loading}
                        pageSizeOptions={[20, 50, 100]}
                        paginationMode="server"
                        rowCount={total}
                        paginationModel={{ page: filters.page - 1, pageSize: filters.limit }}
                        onPaginationModelChange={(model) =>
                            setFilters({ ...filters, page: model.page + 1, limit: model.pageSize })
                        }
                        autoHeight={!isFullscreen}
                        disableRowSelectionOnClick
                        slots={{
                            toolbar: () => (
                                <Box sx={{ p: 1, display: 'flex', gap: 1, alignItems: 'center', borderBottom: '1px solid #e0e0e0' }}>
                                    <Box sx={{ flexGrow: 1 }} />
                                    <Button
                                        startIcon={isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                                        onClick={() => setIsFullscreen(!isFullscreen)}
                                        size="small"
                                    >
                                        {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
                                    </Button>
                                </Box>
                            ),
                        }}
                        sx={{
                            border: '1px solid #e0e0e0',
                            height: isFullscreen ? '100%' : 'auto',
                            '& .MuiDataGrid-cell': {
                                borderRight: '1px solid #e0e0e0',
                            },
                            '& .MuiDataGrid-columnHeaders': {
                                borderBottom: '2px solid #e0e0e0',
                                backgroundColor: '#fafafa',
                            },
                            '& .MuiDataGrid-columnHeader': {
                                borderRight: '1px solid #e0e0e0',
                            },
                            '& .MuiDataGrid-cell:focus': {
                                outline: 'none',
                            },
                        }}
                    />
                </Box>
            </Card>

            {/* Manual Stock Entry Modal */}
            <ManualStockEntryModal
                open={showAddModal}
                onClose={() => setShowAddModal(false)}
                onSuccess={() => {
                    setShowAddModal(false);
                    loadInventory();
                }}
            />
        </Box>
    );
};

export default InventoryListPage;

/**
 * Purchase Orders List Page
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Main dashboard for viewing and managing purchase orders
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
    Send as SendIcon,
    PictureAsPdf as PdfIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { purchaseOrdersAPI, POListParams, POResponse } from '../../../api/purchaseOrders';
import { formatDateForDisplay } from '../../../utils/dateUtils';

const POListPage: React.FC = () => {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();

    const [pos, setPOs] = useState<POResponse[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [filters, setFilters] = useState<POListParams>({
        page: 1,
        limit: 20,
    });

    // Status color mapping
    const getStatusColor = (status: string): 'default' | 'info' | 'warning' | 'success' | 'secondary' => {
        const colors: Record<string, 'default' | 'info' | 'warning' | 'success' | 'secondary'> = {
            draft: 'default',
            sent_to_farm: 'info',
            grn_generated: 'warning',
            completed: 'success',
            exported_to_zoho: 'secondary',
            closed: 'default',
        };
        return colors[status] || 'default';
    };

    // Format status for display
    const formatStatus = (status: string): string => {
        return status.replace(/_/g, ' ').toUpperCase();
    };

    // Load POs
    const loadPOs = async () => {
        setLoading(true);
        try {
            const response = await purchaseOrdersAPI.list(filters);
            setPOs(response.pos);
            setTotal(response.total);
        } catch (error: any) {
            console.error('Failed to load POs:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load purchase orders', {
                variant: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPOs();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filters]);

    // Handle send to farm
    const handleSendToFarm = async (poId: number, poNumber: string) => {
        try {
            await purchaseOrdersAPI.send(poId);
            enqueueSnackbar(`PO ${poNumber} sent to farm successfully`, { variant: 'success' });
            loadPOs(); // Reload to get updated status
        } catch (error: any) {
            console.error('Failed to send PO:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to send PO', { variant: 'error' });
        }
    };

    // Handle PDF download
    const handleDownloadPDF = async (poId: number, poNumber: string) => {
        try {
            const blob = await purchaseOrdersAPI.generatePDF(poId);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${poNumber}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            enqueueSnackbar('PDF downloaded successfully', { variant: 'success' });
        } catch (error: any) {
            console.error('Failed to download PDF:', error);
            enqueueSnackbar('Failed to download PDF', { variant: 'error' });
        }
    };

    // DataGrid columns
    const columns: GridColDef[] = [
        {
            field: 'po_number',
            headerName: 'PO #',
            width: 120,
            renderCell: (params) => (
                <Typography
                    variant="body2"
                    sx={{ cursor: 'pointer', color: 'primary.main', fontWeight: 500 }}
                    onClick={() => navigate(`/inward/purchase-orders/${params.row.id}`)}
                >
                    {params.value}
                </Typography>
            ),
        },
        { field: 'vendor_name', headerName: 'Vendor', width: 200 },
        {
            field: 'dispatch_date',
            headerName: 'Dispatch Date',
            width: 130,
            valueFormatter: (params) => formatDateForDisplay(params.value),
        },
        {
            field: 'delivery_date',
            headerName: 'Delivery Date',
            width: 130,
            valueFormatter: (params) => formatDateForDisplay(params.value),
        },
        {
            field: 'status',
            headerName: 'Status',
            width: 160,
            renderCell: (params) => (
                <Chip
                    label={formatStatus(params.value)}
                    color={getStatusColor(params.value)}
                    size="small"
                />
            ),
        },
        {
            field: 'total_amount',
            headerName: 'Total (₹)',
            width: 130,
            valueFormatter: (params) => `₹${Number(params.value).toFixed(2)}`,
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 200,
            sortable: false,
            renderCell: (params) => (
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="View Details">
                        <IconButton
                            size="small"
                            onClick={() => navigate(`/inward/purchase-orders/${params.row.id}`)}
                        >
                            <ViewIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                    {params.row.status === 'draft' && (
                        <Tooltip title="Send to Farm">
                            <IconButton
                                size="small"
                                color="primary"
                                onClick={() => handleSendToFarm(params.row.id, params.row.po_number)}
                            >
                                <SendIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    )}
                    <Tooltip title="Download PDF">
                        <IconButton
                            size="small"
                            onClick={() => handleDownloadPDF(params.row.id, params.row.po_number)}
                        >
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
                    Purchase Orders
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => navigate('/inward/purchase-orders/create')}
                >
                    Create New PO
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
                            onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}
                        >
                            <MenuItem value="">All</MenuItem>
                            <MenuItem value="draft">Draft</MenuItem>
                            <MenuItem value="sent_to_farm">Sent to Farm</MenuItem>
                            <MenuItem value="grn_generated">GRN Generated</MenuItem>
                            <MenuItem value="completed">Completed</MenuItem>
                            <MenuItem value="exported_to_zoho">Exported to Zoho</MenuItem>
                            <MenuItem value="closed">Closed</MenuItem>
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
                    rows={pos}
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

export default POListPage;

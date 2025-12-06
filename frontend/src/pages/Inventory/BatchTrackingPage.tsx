/**
 * Batch Tracking Page - Main List View
 * Version: 1.0.0
 * Created: 2024-12-04
 *
 * Description:
 *   Main batch tracking page with search, filters, and batch list
 *   - Search and filter batches
 *   - DataGrid with pagination
 *   - Navigate to batch details
 *   - Generate new batch button
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    Button,
    Paper,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    CircularProgress,
} from '@mui/material';
import {
    Add as AddIcon,
    Timeline as TimelineIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import { batchTrackingAPI, BatchSearchResult, SearchBatchesRequest } from '../../api/batchTracking';
import BatchSearch from './BatchSearch';
import useAuthStore from '../../store/authStore';

export default function BatchTrackingPage() {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const { user } = useAuthStore();

    // State
    const [batches, setBatches] = useState<BatchSearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [totalBatches, setTotalBatches] = useState(0);
    const [paginationModel, setPaginationModel] = useState({ page: 0, pageSize: 25 });
    const [currentFilters, setCurrentFilters] = useState<SearchBatchesRequest>({});

    // Generate batch modal
    const [generateModalOpen, setGenerateModalOpen] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [poId, setPoId] = useState('');
    const [grnId, setGrnId] = useState('');

    // Fetch batches
    const fetchBatches = async (filters: SearchBatchesRequest = {}) => {
        setLoading(true);
        try {
            const response = await batchTrackingAPI.searchBatches({
                ...filters,
                page: paginationModel.page + 1, // API uses 1-indexed pages
                limit: paginationModel.pageSize,
            });

            setBatches(response.batches);
            setTotalBatches(response.total);
            setCurrentFilters(filters);
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to fetch batches', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    // Initial load
    useEffect(() => {
        fetchBatches();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [paginationModel.page, paginationModel.pageSize]);

    // Handle search
    const handleSearch = (filters: SearchBatchesRequest) => {
        setPaginationModel({ ...paginationModel, page: 0 }); // Reset to first page
        fetchBatches(filters);
    };

    // Handle generate batch
    const handleGenerateBatch = async () => {
        if (!user) return;

        setGenerating(true);
        try {
            const response = await batchTrackingAPI.generateBatch({
                po_id: poId ? parseInt(poId) : undefined,
                grn_id: grnId ? parseInt(grnId) : undefined,
                created_by: user.email,
            });

            enqueueSnackbar(`Batch ${response.batch_number} generated successfully!`, { variant: 'success' });
            setGenerateModalOpen(false);
            setPoId('');
            setGrnId('');
            fetchBatches(currentFilters); // Refresh list
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to generate batch', { variant: 'error' });
        } finally {
            setGenerating(false);
        }
    };

    // Status chip color
    const getStatusColor = (status: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
        const statusColors: Record<string, "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning"> = {
            ordered: 'info',
            received: 'primary',
            in_grading: 'secondary',
            in_packing: 'secondary',
            in_inventory: 'success',
            allocated: 'warning',
            in_transit: 'warning',
            delivered: 'success',
            archived: 'default',
        };
        return statusColors[status] || 'default';
    };

    // DataGrid columns
    const columns: GridColDef[] = [
        {
            field: 'batch_number',
            headerName: 'Batch Number',
            width: 180,
            renderCell: (params: GridRenderCellParams) => (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TimelineIcon fontSize="small" color="action" />
                    <Typography variant="body2" fontWeight="bold">
                        {params.value}
                    </Typography>
                </Box>
            ),
        },
        {
            field: 'status',
            headerName: 'Status',
            width: 150,
            renderCell: (params: GridRenderCellParams) => (
                <Chip
                    label={params.value.replace('_', ' ').toUpperCase()}
                    color={getStatusColor(params.value)}
                    size="small"
                />
            ),
        },
        {
            field: 'is_repacked',
            headerName: 'Repacked',
            width: 120,
            renderCell: (params: GridRenderCellParams) => (
                params.value ? (
                    <Chip label="REPACKED" color="warning" size="small" variant="outlined" />
                ) : null
            ),
        },
        {
            field: 'created_at',
            headerName: 'Created',
            width: 180,
            valueFormatter: (params) => new Date(params.value).toLocaleString(),
        },
        {
            field: 'farm',
            headerName: 'Farm',
            width: 150,
            valueGetter: (params) => params || 'N/A',
        },
        {
            field: 'current_location',
            headerName: 'Location',
            width: 150,
            valueGetter: (params) => params || 'N/A',
        },
    ];

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                    <Typography variant="h4" gutterBottom fontWeight="bold">
                        📦 Batch Tracking
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Complete traceability from farm to customer
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setGenerateModalOpen(true)}
                >
                    Generate New Batch
                </Button>
            </Box>

            {/* Search Filters */}
            <BatchSearch onSearch={handleSearch} loading={loading} />

            {/* Batches Table */}
            <Paper sx={{ p: 3 }}>
                <Box sx={{ mb: 2 }}>
                    <Typography variant="h6">
                        Total Batches: {totalBatches}
                    </Typography>
                </Box>

                <Box sx={{ height: 600, width: '100%' }}>
                    <DataGrid
                        rows={batches}
                        columns={columns}
                        loading={loading}
                        getRowId={(row) => row.batch_id}
                        pagination
                        paginationMode="server"
                        rowCount={totalBatches}
                        paginationModel={paginationModel}
                        onPaginationModelChange={setPaginationModel}
                        pageSizeOptions={[25, 50, 100]}
                        disableRowSelectionOnClick
                        onRowClick={(params) => navigate(`/inventory/batch-tracking/${params.row.batch_number}`)}
                        sx={{
                            '& .MuiDataGrid-row': {
                                cursor: 'pointer',
                            },
                        }}
                    />
                </Box>
            </Paper>

            {/* Generate Batch Modal */}
            <Dialog open={generateModalOpen} onClose={() => setGenerateModalOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Generate New Batch</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                        <TextField
                            label="PO ID (Optional)"
                            type="number"
                            value={poId}
                            onChange={(e) => setPoId(e.target.value)}
                            fullWidth
                            helperText="Link this batch to a Purchase Order"
                        />
                        <TextField
                            label="GRN ID (Optional)"
                            type="number"
                            value={grnId}
                            onChange={(e) => setGrnId(e.target.value)}
                            fullWidth
                            helperText="Link this batch to a Goods Receipt Note"
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setGenerateModalOpen(false)} disabled={generating}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleGenerateBatch}
                        variant="contained"
                        disabled={generating}
                        startIcon={generating ? <CircularProgress size={20} /> : <AddIcon />}
                    >
                        {generating ? 'Generating...' : 'Generate'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}

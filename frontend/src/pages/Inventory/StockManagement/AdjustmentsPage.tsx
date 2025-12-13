/**
 * Stock Adjustments Page
 * Version: 1.0.0
 * Created: 2024-12-12
 *
 * Manage inventory adjustments with approval workflow
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
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Autocomplete,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
    Add as AddIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import {
    inventoryAPI,
    InventoryAdjustment,
    InventoryAdjustmentRequest,
} from '../../../api/inventory';
import { zohoItemAPI } from '../../../api/zohoItem';
import batchTrackingAPI from '../../../api/batchTracking';
import { formatDateForDisplay } from '../../../utils/dateUtils';
import { useSearchParams } from 'react-router-dom';

const AdjustmentsPage: React.FC = () => {
    const { enqueueSnackbar } = useSnackbar();
    const [searchParams] = useSearchParams();

    const [adjustments, setAdjustments] = useState<InventoryAdjustment[]>([]);
    const [loading, setLoading] = useState(false);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [filters, setFilters] = useState({
        approval_status: '',
        page: 1,
        limit: 20,
    });

    // Create form state
    const [items, setItems] = useState<any[]>([]);
    const [batches, setBatches] = useState<any[]>([]);
    const [createForm, setCreateForm] = useState<InventoryAdjustmentRequest>({
        item_id: 0,
        location: 'packed_warehouse',
        adjustment_type: 'correction',
        quantity: 0,
        reason: '',
    });

    // Location options
    const locations = [
        { value: 'receiving_area', label: 'Receiving Area' },
        { value: 'processing_area', label: 'Processing Area' },
        { value: 'packed_warehouse', label: 'Packed Warehouse' },
        { value: 'delivery_vehicles', label: 'Delivery Vehicles' },
        { value: 'quality_hold', label: 'Quality Hold' },
    ];

    // Status color mapping
    const getStatusColor = (status: string): 'default' | 'warning' | 'success' | 'error' => {
        const colors: Record<string, 'default' | 'warning' | 'success' | 'error'> = {
            pending_approval: 'warning',
            approved: 'success',
            rejected: 'error',
            applied: 'default',
        };
        return colors[status] || 'default';
    };

    // Load adjustments
    const loadAdjustments = async () => {
        setLoading(true);
        try {
            const response = await inventoryAPI.listAdjustments(filters);
            setAdjustments(response.adjustments || []);
        } catch (error: any) {
            console.error('Failed to load adjustments:', error);
            enqueueSnackbar('Failed to load adjustments', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadAdjustments();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filters]);

    // Check if should open create modal from URL param
    useEffect(() => {
        if (searchParams.get('create') === 'true') {
            setShowCreateModal(true);
        }
    }, [searchParams]);

    // Load dropdown data for create form
    useEffect(() => {
        const loadDropdownData = async () => {
            try {
                const [itemsRes, batchesRes] = await Promise.all([
                    zohoItemAPI.getItems({ type: 'Finished Goods', limit: 100 }),
                    batchTrackingAPI.getActiveBatches({ limit: 100 }),
                ]);
                // zohoItemAPI returns paginated response: { items: [...], total, page, pages }
                setItems(Array.isArray(itemsRes) ? itemsRes : (itemsRes?.items || []));
                setBatches(batchesRes.batches || []);
            } catch (error) {
                console.error('Failed to load dropdown data:', error);
            }
        };

        if (showCreateModal) {
            loadDropdownData();
        }
    }, [showCreateModal]);

    // Handle create adjustment
    const handleCreate = async () => {
        // Validation
        if (!createForm.item_id || createForm.quantity <= 0 || createForm.reason.length < 10) {
            enqueueSnackbar('Please fill all required fields correctly', { variant: 'warning' });
            return;
        }

        setLoading(true);
        try {
            await inventoryAPI.createAdjustment(createForm);
            enqueueSnackbar('Adjustment request created successfully', { variant: 'success' });
            setShowCreateModal(false);
            setCreateForm({
                item_id: 0,
                location: 'packed_warehouse',
                adjustment_type: 'correction',
                quantity: 0,
                reason: '',
            });
            loadAdjustments();
        } catch (error: any) {
            console.error('Failed to create adjustment:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to create adjustment', {
                variant: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    // DataGrid columns
    const columns: GridColDef[] = [
        {
            field: 'created_at',
            headerName: 'Created',
            width: 130,
            valueFormatter: (params) => formatDateForDisplay(params.value),
        },
        { field: 'item_name', headerName: 'Item', width: 200 },
        { field: 'batch_number', headerName: 'Batch', width: 110 },
        {
            field: 'location',
            headerName: 'Location',
            width: 150,
            valueFormatter: (params) =>
                params.value.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        },
        {
            field: 'adjustment_type',
            headerName: 'Type',
            width: 120,
            renderCell: (params) => (
                <Chip
                    label={params.value.toUpperCase()}
                    size="small"
                    color={params.value === 'increase' ? 'success' : 'error'}
                />
            ),
        },
        {
            field: 'quantity',
            headerName: 'Quantity',
            width: 100,
            valueFormatter: (params) => params.value.toFixed(2),
        },
        { field: 'reason', headerName: 'Reason', width: 250 },
        {
            field: 'approval_status',
            headerName: 'Status',
            width: 140,
            renderCell: (params) => (
                <Chip
                    label={params.value.replace(/_/g, ' ').toUpperCase()}
                    color={getStatusColor(params.value)}
                    size="small"
                />
            ),
        },
        {
            field: 'created_by',
            headerName: 'Created By',
            width: 150,
        },
    ];

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Box>
                    <Typography variant="h4">
                        Stock Adjustments
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Manage inventory adjustments with approval workflow
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setShowCreateModal(true)}
                >
                    New Adjustment
                </Button>
            </Box>

            {/* Filters */}
            <Card sx={{ p: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <FormControl sx={{ minWidth: 200 }}>
                        <InputLabel>Approval Status</InputLabel>
                        <Select
                            value={filters.approval_status}
                            label="Approval Status"
                            onChange={(e) => setFilters({ ...filters, approval_status: e.target.value, page: 1 })}
                        >
                            <MenuItem value="">All</MenuItem>
                            <MenuItem value="pending_approval">Pending Approval</MenuItem>
                            <MenuItem value="approved">Approved</MenuItem>
                            <MenuItem value="rejected">Rejected</MenuItem>
                            <MenuItem value="applied">Applied</MenuItem>
                        </Select>
                    </FormControl>

                    {filters.approval_status && (
                        <Button
                            variant="outlined"
                            onClick={() => setFilters({ approval_status: '', page: 1, limit: 20 })}
                        >
                            Clear Filters
                        </Button>
                    )}
                </Box>
            </Card>

            {/* DataGrid */}
            <Card>
                <DataGrid
                    rows={adjustments}
                    columns={columns}
                    loading={loading}
                    pageSizeOptions={[20, 50]}
                    paginationModel={{ page: filters.page - 1, pageSize: filters.limit }}
                    onPaginationModelChange={(model) =>
                        setFilters({ ...filters, page: model.page + 1, limit: model.pageSize })
                    }
                    autoHeight
                    disableRowSelectionOnClick
                    sx={{
                        border: '1px solid #e0e0e0',
                    }}
                />
            </Card>

            {/* Create Adjustment Dialog */}
            <Dialog open={showCreateModal} onClose={() => setShowCreateModal(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Create Stock Adjustment</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                        <Autocomplete
                            options={items}
                            getOptionLabel={(option) => `${option.name} (${option.sku})`}
                            renderInput={(params) => (
                                <TextField {...params} label="Item *" placeholder="Search..." />
                            )}
                            onChange={(_, value) => setCreateForm({ ...createForm, item_id: value?.id || 0 })}
                        />

                        <Autocomplete
                            options={batches}
                            getOptionLabel={(option) => option.batch_number}
                            renderInput={(params) => (
                                <TextField {...params} label="Batch (Optional)" placeholder="Search..." />
                            )}
                            onChange={(_, value) => setCreateForm({ ...createForm, batch_id: value?.id })}
                        />

                        <FormControl fullWidth>
                            <InputLabel>Location *</InputLabel>
                            <Select
                                value={createForm.location}
                                label="Location *"
                                onChange={(e) => setCreateForm({ ...createForm, location: e.target.value })}
                            >
                                {locations.map((loc) => (
                                    <MenuItem key={loc.value} value={loc.value}>{loc.label}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Adjustment Type *</InputLabel>
                            <Select
                                value={createForm.adjustment_type}
                                label="Adjustment Type *"
                                onChange={(e) => setCreateForm({ ...createForm, adjustment_type: e.target.value as any })}
                            >
                                <MenuItem value="increase">Increase</MenuItem>
                                <MenuItem value="decrease">Decrease</MenuItem>
                                <MenuItem value="correction">Correction</MenuItem>
                            </Select>
                        </FormControl>

                        <TextField
                            label="Quantity *"
                            type="number"
                            value={createForm.quantity || ''}
                            onChange={(e) => setCreateForm({ ...createForm, quantity: parseFloat(e.target.value) || 0 })}
                            inputProps={{ min: 0, step: 0.01 }}
                            fullWidth
                        />

                        <TextField
                            label="Reason *"
                            multiline
                            rows={3}
                            value={createForm.reason}
                            onChange={(e) => setCreateForm({ ...createForm, reason: e.target.value })}
                            helperText="Minimum 10 characters"
                            fullWidth
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowCreateModal(false)} disabled={loading}>
                        Cancel
                    </Button>
                    <Button onClick={handleCreate} variant="contained" disabled={loading}>
                        {loading ? 'Creating...' : 'Create Adjustment'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default AdjustmentsPage;

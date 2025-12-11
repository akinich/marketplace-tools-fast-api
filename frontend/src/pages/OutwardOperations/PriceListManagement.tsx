import { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    TextField,
    MenuItem,
    Select,
    FormControl,
    InputLabel,
    CircularProgress,
    Alert,
    Grid,
    Chip,
    IconButton,
    Tooltip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import { useNavigate } from 'react-router-dom';
import {
    Add as AddIcon,
    Refresh as RefreshIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    ContentCopy as CopyIcon,
    Visibility as ViewIcon,
} from '@mui/icons-material';
import priceListAPI, { PriceList } from '../../api/priceList';
import PriceListDialog from './components/PriceListDialog';

function PriceListManagement() {
    const { enqueueSnackbar } = useSnackbar();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(false);
    const [priceLists, setPriceLists] = useState<PriceList[]>([]);
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(50);
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [searchTerm, setSearchTerm] = useState('');

    const [dialogOpen, setDialogOpen] = useState(false);
    const [editingPriceList, setEditingPriceList] = useState<PriceList | null>(null);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [deletingPriceList, setDeletingPriceList] = useState<PriceList | null>(null);

    // Get user info
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isAdmin = user.role === 'Admin';

    // Fetch price lists
    const fetchPriceLists = async () => {
        setLoading(true);
        try {
            const params: any = {
                page,
                limit,
            };

            if (statusFilter && statusFilter !== 'all') {
                params.status_filter = statusFilter;
            }

            const response = await priceListAPI.list(params);

            // Client-side search if needed
            let filtered = response.price_lists;
            if (searchTerm) {
                filtered = filtered.filter(pl =>
                    pl.price_list_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    (pl.description && pl.description.toLowerCase().includes(searchTerm.toLowerCase()))
                );
            }

            setPriceLists(filtered);
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load price lists', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPriceLists();
    }, [page, limit, statusFilter]);

    // Handle create/edit
    const handleDialogClose = (refresh?: boolean) => {
        setDialogOpen(false);
        setEditingPriceList(null);
        if (refresh) {
            fetchPriceLists();
        }
    };

    const handleCreate = () => {
        setEditingPriceList(null);
        setDialogOpen(true);
    };

    const handleEdit = (priceList: PriceList) => {
        setEditingPriceList(priceList);
        setDialogOpen(true);
    };

    // Handle delete
    const handleDeleteClick = (priceList: PriceList) => {
        setDeletingPriceList(priceList);
        setDeleteDialogOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (!deletingPriceList) return;

        try {
            await priceListAPI.delete(deletingPriceList.id);
            enqueueSnackbar('Price list deleted successfully', { variant: 'success' });
            setDeleteDialogOpen(false);
            setDeletingPriceList(null);
            fetchPriceLists();
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to delete price list', { variant: 'error' });
        }
    };

    // Handle duplicate
    const handleDuplicate = async (priceList: PriceList) => {
        const newName = prompt(`Enter name for duplicated price list:`, `${priceList.price_list_name} (Copy)`);
        if (!newName) return;

        try {
            await priceListAPI.duplicate(priceList.id, {
                new_name: newName,
                copy_items: true,
            });
            enqueueSnackbar('Price list duplicated successfully', { variant: 'success' });
            fetchPriceLists();
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to duplicate price list', { variant: 'error' });
        }
    };

    // Handle view details
    const handleView = (priceList: PriceList) => {
        navigate(`/outward/price-lists/${priceList.id}`);
    };

    // Status badge component
    const getStatusBadge = (status: string) => {
        const colors: any = {
            active: 'success',
            expired: 'error',
            upcoming: 'warning',
            inactive: 'default',
        };

        const labels: any = {
            active: '🟢 Active',
            expired: '🔴 Expired',
            upcoming: '🟡 Upcoming',
            inactive: '⚫ Inactive',
        };

        return (
            <Chip
                label={labels[status] || status}
                color={colors[status] || 'default'}
                size="small"
            />
        );
    };

    // DataGrid columns
    const columns: GridColDef[] = [
        { field: 'id', headerName: 'ID', width: 80 },
        {
            field: 'price_list_name',
            headerName: 'Price List Name',
            width: 250,
            renderCell: (params) => (
                <Box>
                    <Typography variant="body2" fontWeight="bold">
                        {params.value}
                    </Typography>
                    {params.row.description && (
                        <Typography variant="caption" color="text.secondary">
                            {params.row.description}
                        </Typography>
                    )}
                </Box>
            ),
        },
        {
            field: 'valid_from',
            headerName: 'Valid From',
            width: 120,
            valueFormatter: (params) => new Date(params.value).toLocaleDateString(),
        },
        {
            field: 'valid_to',
            headerName: 'Valid To',
            width: 120,
            valueFormatter: (params) => params.value ? new Date(params.value).toLocaleDateString() : 'Indefinite',
        },
        {
            field: 'status',
            headerName: 'Status',
            width: 130,
            renderCell: (params) => getStatusBadge(params.value),
        },
        {
            field: 'items_count',
            headerName: 'Items',
            width: 100,
            type: 'number',
        },
        {
            field: 'customers_count',
            headerName: 'Customers',
            width: 120,
            type: 'number',
        },
        {
            field: 'is_active',
            headerName: 'Active',
            width: 100,
            renderCell: (params) => (params.value ? '✅' : '❌'),
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 200,
            sortable: false,
            renderCell: (params) => (
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="View Details">
                        <IconButton size="small" onClick={() => handleView(params.row)}>
                            <ViewIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                    {isAdmin && (
                        <>
                            <Tooltip title="Edit">
                                <IconButton size="small" onClick={() => handleEdit(params.row)}>
                                    <EditIcon fontSize="small" />
                                </IconButton>
                            </Tooltip>
                            <Tooltip title="Duplicate">
                                <IconButton size="small" onClick={() => handleDuplicate(params.row)}>
                                    <CopyIcon fontSize="small" />
                                </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                                <IconButton
                                    size="small"
                                    color="error"
                                    onClick={() => handleDeleteClick(params.row)}
                                >
                                    <DeleteIcon fontSize="small" />
                                </IconButton>
                            </Tooltip>
                        </>
                    )}
                </Box>
            ),
        },
    ];

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                💰 Customer Price Lists
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                {user.full_name || user.email} | Role: {user.role}
            </Typography>

            {!isAdmin && (
                <Alert severity="info" sx={{ mb: 2 }}>
                    You have view-only access. Contact admin for edit permissions.
                </Alert>
            )}

            <Paper sx={{ mt: 2, p: 3 }}>
                {/* Filters and Actions */}
                <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={12} md={4}>
                        <TextField
                            fullWidth
                            label="🔍 Search price lists"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Search by name or description"
                        />
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <FormControl fullWidth>
                            <InputLabel>Status Filter</InputLabel>
                            <Select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                label="Status Filter"
                            >
                                <MenuItem value="all">All</MenuItem>
                                <MenuItem value="active">Active</MenuItem>
                                <MenuItem value="expired">Expired</MenuItem>
                                <MenuItem value="upcoming">Upcoming</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} md={5} sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        <Button
                            variant="outlined"
                            startIcon={<RefreshIcon />}
                            onClick={fetchPriceLists}
                        >
                            Refresh
                        </Button>
                        {isAdmin && (
                            <Button
                                variant="contained"
                                startIcon={<AddIcon />}
                                onClick={handleCreate}
                            >
                                Create Price List
                            </Button>
                        )}
                    </Grid>
                </Grid>

                {/* Data Grid */}
                {loading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                        <CircularProgress />
                    </Box>
                ) : (
                    <>
                        <Box sx={{ mb: 2 }}>
                            <Typography variant="body2">
                                ✅ Found {priceLists.length} price list{priceLists.length !== 1 ? 's' : ''}
                            </Typography>
                        </Box>
                        <Box sx={{ height: 600, width: '100%' }}>
                            <DataGrid
                                rows={priceLists}
                                columns={columns}
                                paginationModel={{ page: page - 1, pageSize: limit }}
                                onPaginationModelChange={(model) => {
                                    setPage(model.page + 1);
                                    setLimit(model.pageSize);
                                }}
                                pageSizeOptions={[25, 50, 100]}
                                disableRowSelectionOnClick
                                rowHeight={60}
                            />
                        </Box>
                    </>
                )}
            </Paper>

            {/* Create/Edit Dialog */}
            <PriceListDialog
                open={dialogOpen}
                priceList={editingPriceList}
                onClose={handleDialogClose}
            />

            {/* Delete Confirmation Dialog */}
            <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
                <DialogTitle>Delete Price List?</DialogTitle>
                <DialogContent>
                    <Typography>
                        Are you sure you want to delete "{deletingPriceList?.price_list_name}"?
                    </Typography>
                    {deletingPriceList && deletingPriceList.customers_count > 0 && (
                        <Alert severity="warning" sx={{ mt: 2 }}>
                            This price list has {deletingPriceList.customers_count} customer(s) assigned.
                            You must unassign all customers before deleting.
                        </Alert>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
                    <Button
                        onClick={handleDeleteConfirm}
                        color="error"
                        variant="contained"
                        disabled={deletingPriceList ? deletingPriceList.customers_count > 0 : false}
                    >
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}

export default PriceListManagement;

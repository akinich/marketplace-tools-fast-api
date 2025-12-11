import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Typography,
    Tab,
    Tabs,
    Paper,
    TextField,
    MenuItem,
    LinearProgress,
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Chip,
    IconButton,
    Tooltip,
} from '@mui/material';
import {
    DataGrid,
    GridToolbarContainer,
    GridToolbarExport,
    GridToolbarFilterButton,
    GridToolbarQuickFilter,
    GridColDef,
    GridRenderCellParams,
    useGridApiRef
} from '@mui/x-data-grid';
import {
    Refresh as RefreshIcon,
    Sync as SyncIcon,
    Download as DownloadIcon,
    Upload as UploadIcon,
    Lock as LockIcon,
    LockOpen as LockOpenIcon,
    Restore as RestoreIcon,
    Visibility as VisibilityIcon,
    Fullscreen as FullscreenIcon,
    FullscreenExit as FullscreenExitIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import stockPriceAPI from '../../api/stockPrice';

// Define Interfaces
interface Product {
    id: number;
    product_id: number;
    variation_id: number;
    product_name: string;
    parent_product?: string;
    sku: string;
    stock_quantity: number;
    regular_price: number;
    sale_price: number;
    is_updatable: boolean;
    is_deleted: boolean;
    updated_stock?: number;
    updated_regular_price?: number;
    updated_sale_price?: number;
}

interface Statistics {
    total_products: number;
    updatable: number;
    non_updatable: number;
    deleted: number;
    recent_changes: number;
}

interface ChangePreview {
    db_id: number;
    product_name: string;
    parent_product?: string;
    sku: string;
    changes: Array<{
        field: string;
        old_value: any;
        new_value: any;
    }>;
}

interface SyncResult {
    updated_count: number;
    deleted_count: number;
}

interface UploadResult {
    success_count: number;
    failure_count: number;
}

function StockPriceUpdater() {
    const apiRef = useGridApiRef();
    const { enqueueSnackbar } = useSnackbar();
    const [currentTab, setCurrentTab] = useState(0);
    const [loading, setLoading] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Product lists
    const [updatableProducts, setUpdatableProducts] = useState<Product[]>([]);
    const [nonUpdatableProducts, setNonUpdatableProducts] = useState<Product[]>([]);
    const [deletedProducts, setDeletedProducts] = useState<Product[]>([]);

    // Preview
    const [previewChanges, setPreviewChanges] = useState<ChangePreview[] | null>(null);
    const [previewDialogOpen, setPreviewDialogOpen] = useState(false);

    // Statistics
    const [statistics, setStatistics] = useState<Statistics | null>(null);

    // Search/filter for manage lists
    const [searchTerm, setSearchTerm] = useState('');
    const [filterList, setFilterList] = useState('All');

    // User role
    const [isAdmin, setIsAdmin] = useState(false);

    // ========================================================================
    // Load Data
    // ========================================================================

    useEffect(() => {
        loadProducts();
        checkUserRole();
    }, []);

    // Load statistics when tab changes to Statistics
    useEffect(() => {
        if (currentTab === 2 && isAdmin) {
            loadStatistics();
        }
    }, [currentTab, isAdmin]);

    const checkUserRole = () => {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        setIsAdmin(user.role?.toLowerCase() === 'admin');
    };

    const loadProducts = async () => {
        setLoading(true);
        try {
            const data = await stockPriceAPI.getProducts();
            setUpdatableProducts(data.updatable || []);
            setNonUpdatableProducts(data.non_updatable || []);
            setDeletedProducts(data.deleted || []);
        } catch (error: any) {
            console.error('Load products error:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load products', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const loadStatistics = async () => {
        try {
            const stats = await stockPriceAPI.getStatistics();
            setStatistics(stats);
        } catch (error: any) {
            console.error('Load statistics error:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load statistics', { variant: 'error' });
        }
    };

    // ========================================================================
    // Sync from WooCommerce
    // ========================================================================

    const handleSync = async () => {
        setSyncing(true);
        try {
            const result: SyncResult = await stockPriceAPI.syncFromWooCommerce();
            enqueueSnackbar(
                `Sync complete! Updated: ${result.updated_count}, Deleted: ${result.deleted_count}`,
                { variant: 'success' }
            );
            await loadProducts();
        } catch (error) {
            enqueueSnackbar('Sync failed', { variant: 'error' });
        } finally {
            setSyncing(false);
        }
    };

    // ========================================================================
    // Excel Upload/Download
    // ========================================================================

    const handleDownloadTemplate = async () => {
        try {
            const blob = await stockPriceAPI.downloadExcelTemplate();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `stock_price_template_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            enqueueSnackbar('Template downloaded', { variant: 'success' });
        } catch (error) {
            enqueueSnackbar('Failed to download template', { variant: 'error' });
        }
    };

    const handleExcelUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setLoading(true);
        try {
            const result: UploadResult = await stockPriceAPI.uploadExcel(file);
            enqueueSnackbar(
                `Upload complete! Success: ${result.success_count}, Failed: ${result.failure_count}`,
                { variant: 'success' }
            );
            await loadProducts();
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Upload failed', { variant: 'error' });
        } finally {
            setLoading(false);
            event.target.value = '';
        }
    };

    // ========================================================================
    // Preview and Apply Changes
    // ========================================================================

    const handlePreviewChanges = async (editedRows: Product[]) => {
        const changes: any[] = [];

        editedRows.forEach((row) => {
            const change: any = { db_id: row.id };
            let hasChanges = false;

            if (row.updated_stock !== null && row.updated_stock !== undefined) {
                change.stock_quantity = row.updated_stock;
                hasChanges = true;
            }
            if (row.updated_regular_price !== null && row.updated_regular_price !== undefined) {
                change.regular_price = row.updated_regular_price;
                hasChanges = true;
            }
            if (row.updated_sale_price !== null && row.updated_sale_price !== undefined) {
                change.sale_price = row.updated_sale_price;
                hasChanges = true;
            }

            if (hasChanges) {
                changes.push(change);
            }
        });

        if (changes.length === 0) {
            enqueueSnackbar('No changes detected', { variant: 'info' });
            return;
        }

        setLoading(true);
        try {
            const result = await stockPriceAPI.previewChanges(changes);

            if (result.validation_errors.length > 0) {
                result.validation_errors.forEach((error: string) => {
                    enqueueSnackbar(error, { variant: 'error' });
                });
            }

            if (result.valid_changes.length > 0) {
                setPreviewChanges(result.valid_changes);
                setPreviewDialogOpen(true);
            } else {
                enqueueSnackbar('No valid changes found', { variant: 'warning' });
            }
        } catch (error) {
            enqueueSnackbar('Preview failed', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const handleApplyUpdates = async () => {
        if (!previewChanges) return;

        setLoading(true);
        setPreviewDialogOpen(false);
        try {
            const result = await stockPriceAPI.applyUpdates(previewChanges);
            enqueueSnackbar(
                `Updates complete! Success: ${result.success_count}, Failed: ${result.failure_count}`,
                { variant: 'success' }
            );

            if (result.failed_items.length > 0) {
                result.failed_items.forEach((item: string) => {
                    enqueueSnackbar(item, { variant: 'error' });
                });
            }

            setPreviewChanges(null);
            await loadProducts();
        } catch (error) {
            enqueueSnackbar('Update failed', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    // ========================================================================
    // Product Settings (Lock/Unlock/Restore)
    // ========================================================================

    const handleToggleLock = async (productId: number, variationId: number, currentlyUpdatable: boolean) => {
        try {
            await stockPriceAPI.updateProductSetting(productId, variationId, !currentlyUpdatable);
            enqueueSnackbar(
                currentlyUpdatable ? 'Product locked' : 'Product unlocked',
                { variant: 'success' }
            );
            await loadProducts();
        } catch (error) {
            enqueueSnackbar('Failed to update setting', { variant: 'error' });
        }
    };

    const handleRestoreProduct = async (productId: number, variationId: number) => {
        try {
            await stockPriceAPI.restoreProduct(productId, variationId);
            enqueueSnackbar('Product restored', { variant: 'success' });
            await loadProducts();
        } catch (error) {
            enqueueSnackbar('Failed to restore product', { variant: 'error' });
        }
    };

    // ========================================================================
    // Render Functions
    // ========================================================================

    const renderUpdateTab = () => {
        const columns: GridColDef[] = [
            { field: 'product_id', headerName: 'Product ID', width: 100 },
            { field: 'variation_id', headerName: 'Variation ID', width: 110 },
            {
                field: 'product_name',
                headerName: 'Product Name',
                width: 300,
                renderCell: (params: GridRenderCellParams) => {
                    const displayName = params.row.parent_product && params.row.variation_id
                        ? `${params.row.parent_product} - ${params.row.product_name}`
                        : params.row.product_name;
                    return <Typography variant="body2">{displayName}</Typography>;
                },
            },
            { field: 'sku', headerName: 'SKU', width: 120 },
            { field: 'stock_quantity', headerName: 'Current Stock', width: 120, type: 'number' },
            { field: 'regular_price', headerName: 'Current Regular Price', width: 150, type: 'number' },
            { field: 'sale_price', headerName: 'Current Sale Price', width: 150, type: 'number' },
            { field: 'updated_stock', headerName: '✏️ New Stock', width: 120, type: 'number', editable: true, headerClassName: 'editable-column-header' },
            { field: 'updated_regular_price', headerName: '✏️ New Regular Price', width: 150, type: 'number', editable: true, headerClassName: 'editable-column-header' },
            { field: 'updated_sale_price', headerName: '✏️ New Sale Price', width: 150, type: 'number', editable: true, headerClassName: 'editable-column-header' },
        ];

        return (
            <Box>
                <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                    <Button
                        startIcon={<RefreshIcon />}
                        onClick={loadProducts}
                        disabled={loading}
                    >
                        Refresh Data
                    </Button>
                    <Button
                        startIcon={<SyncIcon />}
                        onClick={handleSync}
                        disabled={syncing}
                    >
                        {syncing ? 'Syncing...' : 'Sync from WooCommerce'}
                    </Button>
                    <Button
                        startIcon={<DownloadIcon />}
                        onClick={handleDownloadTemplate}
                    >
                        Download Template
                    </Button>
                    <Button
                        startIcon={<UploadIcon />}
                        component="label"
                    >
                        Upload Excel
                        <input
                            type="file"
                            hidden
                            accept=".xlsx,.xls"
                            onChange={handleExcelUpload}
                        />
                    </Button>
                </Box>

                {syncing && <LinearProgress sx={{ mb: 2 }} />}

                <Typography variant="h6" gutterBottom>
                    ✅ Updatable Products ({updatableProducts.length})
                </Typography>

                <Box sx={{
                    height: isFullscreen ? '100vh' : 600,
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
                        apiRef={apiRef}
                        rows={updatableProducts}
                        columns={columns}
                        initialState={{
                            pagination: { paginationModel: { pageSize: 25, page: 0 } },
                        }}
                        pageSizeOptions={[25, 50, 100]}
                        disableRowSelectionOnClick
                        loading={loading}
                        editMode="cell"
                        processRowUpdate={(newRow) => {
                            // Update the row in state
                            setUpdatableProducts((prev) =>
                                prev.map((row) => (row.id === newRow.id ? newRow : row))
                            );
                            return newRow;
                        }}
                        onCellClick={(params, event) => {
                            // Enable single-click editing for editable cells
                            if (params.isEditable && apiRef.current) {
                                event.defaultMuiPrevented = true;
                                apiRef.current.startCellEditMode({
                                    id: params.id,
                                    field: params.field,
                                });
                            }
                        }}
                        slots={{
                            toolbar: () => (
                                <GridToolbarContainer>
                                    <GridToolbarQuickFilter />
                                    <GridToolbarFilterButton />
                                    <GridToolbarExport />
                                    <Box sx={{ flexGrow: 1 }} />
                                    <Button
                                        startIcon={isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                                        onClick={() => setIsFullscreen(!isFullscreen)}
                                        size="small"
                                    >
                                        {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
                                    </Button>
                                    <Button
                                        startIcon={<VisibilityIcon />}
                                        onClick={() => handlePreviewChanges(updatableProducts)}
                                        size="small"
                                    >
                                        Preview Changes
                                    </Button>
                                </GridToolbarContainer>
                            ),
                        }}
                        sx={{
                            border: '1px solid #e0e0e0',
                            height: '100%',
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
                            '& .editable-column-header': {
                                backgroundColor: '#e3f2fd',
                                fontWeight: 'bold',
                            },
                        }}
                    />
                </Box>

                <Box sx={{ mt: 4 }}>
                    <Typography variant="h6" gutterBottom>
                        🔒 Non-Updatable Products ({nonUpdatableProducts.length})
                    </Typography>
                    <DataGrid
                        rows={nonUpdatableProducts}
                        columns={columns.filter((col) => !col.field.startsWith('updated_'))}
                        initialState={{
                            pagination: { paginationModel: { pageSize: 10, page: 0 } },
                        }}
                        pageSizeOptions={[10, 25, 50]}
                        autoHeight
                        disableRowSelectionOnClick
                    />
                </Box>

                <Box sx={{ mt: 4 }}>
                    <Typography variant="h6" gutterBottom>
                        🗑️ Deleted Products ({deletedProducts.length})
                    </Typography>
                    <DataGrid
                        rows={deletedProducts}
                        columns={columns.filter((col) => !col.field.startsWith('updated_'))}
                        initialState={{
                            pagination: { paginationModel: { pageSize: 10, page: 0 } },
                        }}
                        pageSizeOptions={[10, 25, 50]}
                        autoHeight
                        disableRowSelectionOnClick
                    />
                </Box>
            </Box>
        );
    };

    const renderManageListsTab = () => {
        if (!isAdmin) {
            return <Alert severity="warning">Admin access required</Alert>;
        }

        const allProducts = [...updatableProducts, ...nonUpdatableProducts, ...deletedProducts];
        const filteredProducts = allProducts.filter((product) => {
            const matchesSearch =
                searchTerm === '' ||
                product.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                (product.sku && product.sku.toLowerCase().includes(searchTerm.toLowerCase()));

            const matchesFilter =
                filterList === 'All' ||
                (filterList === 'Updatable' && product.is_updatable && !product.is_deleted) ||
                (filterList === 'Non-Updatable' && !product.is_updatable && !product.is_deleted) ||
                (filterList === 'Deleted' && product.is_deleted);

            return matchesSearch && matchesFilter;
        });

        const columns: GridColDef[] = [
            {
                field: 'product_name',
                headerName: 'Product Name',
                width: 400,
                renderCell: (params: GridRenderCellParams) => {
                    const displayName = params.row.parent_product && params.row.variation_id
                        ? `${params.row.parent_product} - ${params.row.product_name}`
                        : params.row.product_name;
                    return <Typography variant="body2">{displayName}</Typography>;
                },
            },
            { field: 'sku', headerName: 'SKU', width: 150 },
            { field: 'stock_quantity', headerName: 'Stock', width: 100 },
            {
                field: 'status',
                headerName: 'Status',
                width: 150,
                renderCell: (params: GridRenderCellParams) => {
                    if (params.row.is_deleted) {
                        return <Chip label="Deleted" color="error" size="small" />;
                    }
                    if (params.row.is_updatable) {
                        return <Chip label="Updatable" color="success" size="small" />;
                    }
                    return <Chip label="Locked" color="warning" size="small" />;
                },
            },
            {
                field: 'actions',
                headerName: 'Actions',
                width: 150,
                renderCell: (params: GridRenderCellParams) => (
                    <Box>
                        {!params.row.is_deleted && (
                            <Tooltip title={params.row.is_updatable ? 'Lock' : 'Unlock'}>
                                <IconButton
                                    size="small"
                                    onClick={() =>
                                        handleToggleLock(
                                            params.row.product_id,
                                            params.row.variation_id,
                                            params.row.is_updatable
                                        )
                                    }
                                >
                                    {params.row.is_updatable ? <LockIcon /> : <LockOpenIcon />}
                                </IconButton>
                            </Tooltip>
                        )}
                        {params.row.is_deleted && (
                            <Tooltip title="Restore">
                                <IconButton
                                    size="small"
                                    onClick={() =>
                                        handleRestoreProduct(params.row.product_id, params.row.variation_id)
                                    }
                                >
                                    <RestoreIcon />
                                </IconButton>
                            </Tooltip>
                        )}
                    </Box>
                ),
            },
        ];

        return (
            <Box>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <TextField
                        label="Search"
                        variant="outlined"
                        size="small"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        sx={{ width: 300 }}
                    />
                    <TextField
                        select
                        label="Filter"
                        variant="outlined"
                        size="small"
                        value={filterList}
                        onChange={(e) => setFilterList(e.target.value)}
                        sx={{ width: 200 }}
                    >
                        <MenuItem value="All">All</MenuItem>
                        <MenuItem value="Updatable">Updatable</MenuItem>
                        <MenuItem value="Non-Updatable">Non-Updatable</MenuItem>
                        <MenuItem value="Deleted">Deleted</MenuItem>
                    </TextField>
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                    Found {filteredProducts.length} products
                </Typography>

                <DataGrid
                    rows={filteredProducts}
                    columns={columns}
                    initialState={{
                        pagination: { paginationModel: { pageSize: 25, page: 0 } },
                    }}
                    pageSizeOptions={[25, 50, 100]}
                    autoHeight
                    disableRowSelectionOnClick
                />
            </Box>
        );
    };

    const renderStatisticsTab = () => {
        if (!isAdmin) {
            return <Alert severity="warning">Admin access required</Alert>;
        }

        return (
            <Box>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Paper sx={{ p: 3, minWidth: 200 }}>
                        <Typography variant="h4" color="primary">
                            {statistics?.total_products || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Total Products
                        </Typography>
                    </Paper>
                    <Paper sx={{ p: 3, minWidth: 200 }}>
                        <Typography variant="h4" color="success.main">
                            {statistics?.updatable || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Updatable
                        </Typography>
                    </Paper>
                    <Paper sx={{ p: 3, minWidth: 200 }}>
                        <Typography variant="h4" color="warning.main">
                            {statistics?.non_updatable || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Non-Updatable
                        </Typography>
                    </Paper>
                    <Paper sx={{ p: 3, minWidth: 200 }}>
                        <Typography variant="h4" color="error.main">
                            {statistics?.deleted || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Deleted
                        </Typography>
                    </Paper>
                    <Paper sx={{ p: 3, minWidth: 200 }}>
                        <Typography variant="h4" color="info.main">
                            {statistics?.recent_changes || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Changes (24h)
                        </Typography>
                    </Paper>
                </Box>
            </Box>
        );
    };

    // ========================================================================
    // Main Render
    // ========================================================================

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                💰 Stock & Price Updater
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                Update WooCommerce product stock and prices with list management
            </Typography>

            <Box sx={{ mt: 3 }}>
                <Tabs value={currentTab} onChange={(_, v) => setCurrentTab(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tab label="📊 Update Products" />
                    {isAdmin && <Tab label="⚙️ Manage Lists" />}
                    {isAdmin && <Tab label="📈 Statistics" />}
                </Tabs>
            </Box>

            <Box sx={{ mt: 3 }}>
                {currentTab === 0 && renderUpdateTab()}
                {currentTab === 1 && isAdmin && renderManageListsTab()}
                {currentTab === 2 && isAdmin && renderStatisticsTab()}
            </Box>

            {/* Preview Dialog */}
            <Dialog
                open={previewDialogOpen}
                onClose={() => setPreviewDialogOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>Preview Changes</DialogTitle>
                <DialogContent>
                    {previewChanges && (
                        <Box>
                            <Typography variant="body2" gutterBottom>
                                {previewChanges.length} products will be updated
                            </Typography>
                            {previewChanges.map((item, index) => (
                                <Paper key={index} sx={{ p: 2, mb: 1 }}>
                                    <Typography variant="subtitle2">
                                        {item.parent_product && item.parent_product !== item.product_name
                                            ? `${item.parent_product} - ${item.product_name}`
                                            : item.product_name}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        SKU: {item.sku}
                                    </Typography>
                                    <Box sx={{ mt: 1 }}>
                                        {item.changes.map((change, idx) => (
                                            <Typography key={idx} variant="body2">
                                                {change.field}: {change.old_value} → {change.new_value}
                                            </Typography>
                                        ))}
                                    </Box>
                                </Paper>
                            ))}
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setPreviewDialogOpen(false)}>Cancel</Button>
                    <Button onClick={handleApplyUpdates} variant="contained" color="primary">
                        Apply Updates
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}

export default StockPriceUpdater;

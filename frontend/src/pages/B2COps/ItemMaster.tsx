import { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    Tabs,
    Tab,
    TextField,
    Button,
    MenuItem,
    Select,
    FormControl,
    InputLabel,
    CircularProgress,
    Alert,
    Grid,
    Card,
    CardContent,
} from '@mui/material';
import { DataGrid, GridColDef, useGridApiRef } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import {
    Refresh as RefreshIcon,
    Sync as SyncIcon,
    Download as DownloadIcon,
    Fullscreen as FullscreenIcon,
    FullscreenExit as FullscreenExitIcon,
} from '@mui/icons-material';
import { productAPI } from '../../api';

// Interfaces
interface Product {
    id: number;
    product_id: number;
    variation_id: number | null;
    sku: string;
    product_name: string;
    parent_product: string | null;
    stock_quantity: number;
    regular_price: number;
    sale_price: number;
    hsn: string | null;
    zoho_name: string | null;
    usage_units: string | null;
    categories: string | null;
    attribute: string | null;
    is_active: boolean;
    notes: string | null;
}

interface ProductStats {
    total: number;
    active: number;
    inactive: number;
    simple: number;
    variations: number;
}



function ItemMaster() {
    const { enqueueSnackbar } = useSnackbar();
    const apiRef = useGridApiRef();
    const [currentTab, setCurrentTab] = useState(0);
    const [loading, setLoading] = useState(false);
    const [products, setProducts] = useState<Product[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterActive, setFilterActive] = useState('active');
    const [filterType, setFilterType] = useState('all');
    const [stats, setStats] = useState<ProductStats | null>(null);
    const [syncLimit, setSyncLimit] = useState(100);
    const [updateExisting, setUpdateExisting] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    // Get user role
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isAdmin = user.role === 'Admin';

    // Fetch products
    const fetchProducts = async () => {
        setLoading(true);
        try {
            const params = {
                search: searchTerm || undefined,
                active_only: filterActive === 'active',
                product_type: filterType === 'all' ? undefined : filterType,
                limit: 1000,
            };

            const response = await productAPI.getProducts(params);
            setProducts(response.products || []);
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load products', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    // Fetch stats
    const fetchStats = async () => {
        try {
            const stats = await productAPI.getStats();
            setStats(stats);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    // Initial load
    useEffect(() => {
        fetchProducts();
        fetchStats();
    }, [refreshTrigger, searchTerm, filterActive, filterType]);

    // Handle product update
    const handleProductUpdate = async (updatedRow: Product, originalRow: Product) => {
        try {
            const changes: Partial<Product> = {};

            // Find changed fields
            (Object.keys(updatedRow) as Array<keyof Product>).forEach((key) => {
                if (updatedRow[key] !== originalRow[key] && key !== 'id') {
                    // @ts-ignore
                    changes[key] = updatedRow[key];
                }
            });

            if (Object.keys(changes).length === 0) {
                return originalRow;
            }

            await productAPI.updateProduct(updatedRow.id, changes);

            enqueueSnackbar('Product updated successfully', { variant: 'success' });
            return updatedRow;
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to update product', { variant: 'error' });
            return originalRow;
        }
    };

    // Handle sync
    const handleSync = async () => {
        setSyncing(true);
        try {
            const response = await productAPI.syncFromWooCommerce(syncLimit, updateExisting);
            enqueueSnackbar(response.message, { variant: 'success' });
            setRefreshTrigger((prev) => prev + 1);
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Sync failed', { variant: 'error' });
        } finally {
            setSyncing(false);
        }
    };

    // Export to Excel
    const handleExport = () => {
        const csvContent = [
            ['ID', 'Product ID', 'Variation ID', 'SKU', 'Product Name', 'Parent Product', 'Stock', 'Regular Price', 'Sale Price', 'HSN', 'Zoho Name', 'Usage Units', 'Categories', 'Attributes', 'Active', 'Notes'],
            ...products.map((p) => [
                p.id,
                p.product_id,
                p.variation_id || '',
                p.sku,
                p.product_name,
                p.parent_product || '',
                p.stock_quantity,
                p.regular_price,
                p.sale_price,
                p.hsn || '',
                p.zoho_name || '',
                p.usage_units || '',
                p.categories || '',
                p.attribute || '',
                p.is_active ? 'Yes' : 'No',
                p.notes || '',
            ]),
        ]
            .map((row) => row.join(','))
            .join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `products_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    // DataGrid columns
    const columns: GridColDef[] = [
        { field: 'id', headerName: 'DB ID', width: 80, editable: false },
        { field: 'product_id', headerName: 'Product ID', width: 100, editable: false },
        { field: 'variation_id', headerName: 'Variation ID', width: 120, editable: false },
        {
            field: 'product_name',
            headerName: isAdmin ? '✏️ Product Name' : 'Product Name',
            width: 250,
            editable: isAdmin,
            headerClassName: isAdmin ? 'editable-column-header' : ''
        },
        {
            field: 'parent_product',
            headerName: isAdmin ? '✏️ Parent Name' : 'Parent Name',
            width: 200,
            editable: isAdmin,
            headerClassName: isAdmin ? 'editable-column-header' : ''
        },
        {
            field: 'sku',
            headerName: isAdmin ? '✏️ SKU' : 'SKU',
            width: 150,
            editable: isAdmin,
            headerClassName: isAdmin ? 'editable-column-header' : ''
        },
        {
            field: 'stock_quantity',
            headerName: isAdmin ? '✏️ Stock' : 'Stock',
            width: 100,
            editable: isAdmin,
            type: 'number',
            headerClassName: isAdmin ? 'editable-column-header' : ''
        },
        {
            field: 'regular_price',
            headerName: isAdmin ? '✏️ Regular Price' : 'Regular Price',
            width: 120,
            editable: isAdmin,
            type: 'number',
            headerClassName: isAdmin ? 'editable-column-header' : ''
        },
        {
            field: 'sale_price',
            headerName: isAdmin ? '✏️ Sale Price' : 'Sale Price',
            width: 120,
            editable: isAdmin,
            type: 'number',
            headerClassName: isAdmin ? 'editable-column-header' : ''
        },
        {
            field: 'hsn',
            headerName: '✏️ HSN',
            width: 120,
            editable: true,
            headerClassName: 'editable-column-header'
        },
        {
            field: 'zoho_name',
            headerName: '✏️ Zoho Name',
            width: 200,
            editable: true,
            headerClassName: 'editable-column-header'
        },
        {
            field: 'usage_units',
            headerName: '✏️ Usage Units',
            width: 120,
            editable: true,
            headerClassName: 'editable-column-header'
        },
        {
            field: 'categories',
            headerName: isAdmin ? '✏️ Categories' : 'Categories',
            width: 200,
            editable: isAdmin,
            headerClassName: isAdmin ? 'editable-column-header' : ''
        },
        {
            field: 'attribute',
            headerName: isAdmin ? '✏️ Attributes' : 'Attributes',
            width: 200,
            editable: isAdmin,
            headerClassName: isAdmin ? 'editable-column-header' : ''
        },
        {
            field: 'is_active',
            headerName: isAdmin ? '✏️ Active' : 'Active',
            width: 100,
            editable: isAdmin,
            type: 'boolean',
            headerClassName: isAdmin ? 'editable-column-header' : ''
        },
        {
            field: 'notes',
            headerName: '✏️ Notes',
            width: 200,
            editable: true,
            headerClassName: 'editable-column-header'
        },
    ];

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                📦 Woo Item Master
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                {user.full_name || user.email} | Role: {user.role}
            </Typography>

            {!isAdmin && (
                <Alert severity="info" sx={{ mb: 2 }}>
                    You have view and limited edit access (HSN, Zoho Name, Usage Units, Notes). Contact admin for full access.
                </Alert>
            )}

            <Paper sx={{ mt: 2 }}>
                <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)}>
                    <Tab label="📊 Products" />
                    {isAdmin && <Tab label="🔄 Sync from WooCommerce" />}
                    {isAdmin && <Tab label="📈 Statistics" />}
                </Tabs>

                {/* Products Tab */}
                {currentTab === 0 && (
                    <Box sx={{ p: 3 }}>
                        <Grid container spacing={2} sx={{ mb: 2 }}>
                            <Grid item xs={12} md={4}>
                                <TextField
                                    fullWidth
                                    label="🔍 Search products"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    placeholder="Search by name or SKU"
                                />
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <FormControl fullWidth>
                                    <InputLabel>Filter</InputLabel>
                                    <Select value={filterActive} onChange={(e) => setFilterActive(e.target.value)}>
                                        <MenuItem value="active">Active only</MenuItem>
                                        <MenuItem value="inactive">Inactive only</MenuItem>
                                        <MenuItem value="all">All products</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <FormControl fullWidth>
                                    <InputLabel>Type</InputLabel>
                                    <Select value={filterType} onChange={(e) => setFilterType(e.target.value as string)}>
                                        <MenuItem value="all">All</MenuItem>
                                        <MenuItem value="simple">Simple</MenuItem>
                                        <MenuItem value="variations">Variations</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12} md={2}>
                                <Button
                                    fullWidth
                                    variant="outlined"
                                    startIcon={<RefreshIcon />}
                                    onClick={() => setRefreshTrigger((prev) => prev + 1)}
                                    sx={{ height: '56px' }}
                                >
                                    Refresh
                                </Button>
                            </Grid>
                        </Grid>

                        {loading ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                                <CircularProgress />
                            </Box>
                        ) : (
                            <>
                                <Typography variant="body2" sx={{ mb: 2 }}>
                                    ✅ Found {products.length} products
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
                                        rows={products}
                                        columns={columns}
                                        initialState={{
                                            pagination: {
                                                paginationModel: { pageSize: 25, page: 0 },
                                            },
                                        }}
                                        pageSizeOptions={[10, 25, 50, 100]}
                                        disableRowSelectionOnClick
                                        processRowUpdate={handleProductUpdate}
                                        editMode="cell"
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
                                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                                    <Button variant="contained" startIcon={<DownloadIcon />} onClick={handleExport}>
                                        Export to CSV
                                    </Button>
                                </Box>
                            </>
                        )}
                    </Box>
                )}

                {/* Sync Tab */}
                {currentTab === 1 && isAdmin && (
                    <Box sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            🔄 Sync Products from WooCommerce
                        </Typography>
                        <Alert severity="info" sx={{ mb: 2 }}>
                            <strong>How Sync Works:</strong>
                            <ul>
                                <li>Fetches products from WooCommerce API (with pagination)</li>
                                <li>{updateExisting ? 'UPDATES existing products with latest data' : 'Only ADDS new products (skips existing)'}</li>
                                <li>Maximum 1000 products per sync</li>
                                <li>Includes simple products and variations</li>
                            </ul>
                        </Alert>

                        <Grid container spacing={2} sx={{ mb: 2 }}>
                            <Grid item xs={12} md={6}>
                                <TextField
                                    fullWidth
                                    type="number"
                                    label="Products to fetch"
                                    value={syncLimit}
                                    onChange={(e) => setSyncLimit(Math.min(1000, Math.max(1, parseInt(e.target.value) || 100)))}
                                    inputProps={{ min: 1, max: 1000 }}
                                    helperText="1-1000 products (fetches in pages of 100)"
                                />
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                                    <input
                                        type="checkbox"
                                        id="updateExisting"
                                        checked={updateExisting}
                                        onChange={(e) => setUpdateExisting(e.target.checked)}
                                        style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                                    />
                                    <label htmlFor="updateExisting" style={{ cursor: 'pointer', fontSize: '14px' }}>
                                        <strong>Update Existing Products</strong> - Refresh prices, stock, details
                                    </label>
                                </Box>
                                <Typography variant="caption" color="text.secondary" sx={{ ml: '28px', display: 'block' }}>
                                    Use this to sync price/stock changes from WooCommerce
                                </Typography>
                            </Grid>
                        </Grid>

                        <Button
                            variant="contained"
                            size="large"
                            startIcon={syncing ? <CircularProgress size={20} /> : <SyncIcon />}
                            onClick={handleSync}
                            disabled={syncing}
                        >
                            {syncing ? 'Syncing...' : updateExisting ? '🔄 Sync & Update All' : '🚀 Sync New Products'}
                        </Button>
                    </Box>
                )}


                {/* Statistics Tab */}
                {currentTab === 2 && isAdmin && (
                    <Box sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            📈 Product Statistics
                        </Typography>

                        {stats && (
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.total}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                📦 Total Products
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.active}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                ✅ Active
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.inactive}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                ❌ Inactive
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.simple}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                📝 Simple Products
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.variations}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                🔀 Variations
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                            </Grid>
                        )}

                        <Alert severity="info" sx={{ mt: 3 }}>
                            💡 More detailed analytics coming soon...
                        </Alert>
                    </Box>
                )}
            </Paper>
        </Box>
    );
}

export default ItemMaster;

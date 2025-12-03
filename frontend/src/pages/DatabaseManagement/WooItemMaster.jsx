import React, { useState, useEffect } from 'react';
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
import { DataGrid } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import {
    Refresh as RefreshIcon,
    Sync as SyncIcon,
    Download as DownloadIcon,
    Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { productAPI } from '../../api';

function ItemMaster() {
    const { enqueueSnackbar } = useSnackbar();
    const [currentTab, setCurrentTab] = useState(0);
    const [loading, setLoading] = useState(false);
    const [products, setProducts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterActive, setFilterActive] = useState('active');
    const [filterType, setFilterType] = useState('all');
    const [stats, setStats] = useState(null);
    const [syncLimit, setSyncLimit] = useState(100);
    const [updateExisting, setUpdateExisting] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    // Get user role
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isAdmin = user.role === 'Admin';

    // New product form state
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
        } catch (error) {
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
    const handleProductUpdate = async (updatedRow, originalRow) => {
        try {
            const changes = {};

            // Find changed fields
            Object.keys(updatedRow).forEach((key) => {
                if (updatedRow[key] !== originalRow[key] && key !== 'id') {
                    changes[key] = updatedRow[key];
                }
            });

            if (Object.keys(changes).length === 0) {
                return originalRow;
            }

            await productAPI.updateProduct(updatedRow.id, changes);

            enqueueSnackbar('Product updated successfully', { variant: 'success' });
            return updatedRow;
        } catch (error) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to update product', { variant: 'error' });
            return originalRow;
        }
    };

    // Handle sync
    const handleSync = async () => {
        if (syncing) {
            enqueueSnackbar('Sync already in progress. Please wait...', { variant: 'warning' });
            return;
        }

        setSyncing(true);
        try {
            const response = await productAPI.syncFromWooCommerce(syncLimit, updateExisting);
            enqueueSnackbar(response.message, { variant: 'success' });
            setRefreshTrigger((prev) => prev + 1);
        } catch (error) {
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
    const columns = [
        { field: 'id', headerName: 'DB ID', width: 80, editable: false },
        { field: 'product_id', headerName: 'Product ID', width: 100, editable: false },
        { field: 'variation_id', headerName: 'Variation ID', width: 120, editable: false },
        { field: 'product_name', headerName: 'Product Name', width: 250, editable: isAdmin },
        { field: 'parent_product', headerName: 'Parent Name', width: 200, editable: isAdmin },
        { field: 'sku', headerName: 'SKU', width: 150, editable: isAdmin },
        { field: 'stock_quantity', headerName: 'Stock', width: 100, editable: isAdmin, type: 'number' },
        { field: 'regular_price', headerName: 'Regular Price', width: 120, editable: isAdmin, type: 'number' },
        { field: 'sale_price', headerName: 'Sale Price', width: 120, editable: isAdmin, type: 'number' },
        { field: 'hsn', headerName: 'HSN', width: 120, editable: true },
        { field: 'zoho_name', headerName: 'Zoho Name', width: 200, editable: true },
        { field: 'usage_units', headerName: 'Usage Units', width: 120, editable: true },
        { field: 'categories', headerName: 'Categories', width: 200, editable: isAdmin },
        { field: 'attribute', headerName: 'Attributes', width: 200, editable: isAdmin },
        { field: 'is_active', headerName: 'Active', width: 100, editable: isAdmin, type: 'boolean' },
        { field: 'notes', headerName: 'Notes', width: 200, editable: true },
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
                                    <Select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
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
                                <Box sx={{ height: 600, width: '100%' }}>
                                    <DataGrid
                                        rows={products}
                                        columns={columns}
                                        pageSize={25}
                                        rowsPerPageOptions={[10, 25, 50, 100]}
                                        disableSelectionOnClick
                                        processRowUpdate={handleProductUpdate}
                                        experimentalFeatures={{ newEditingApi: true }}
                                    />
                                </Box>
                                {isAdmin && (
                                    <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                                        <Button variant="contained" startIcon={<DownloadIcon />} onClick={handleExport}>
                                            Export to CSV
                                        </Button>
                                    </Box>
                                )}
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

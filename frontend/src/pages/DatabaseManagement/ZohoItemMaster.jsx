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
    LinearProgress,
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
import { zohoItemAPI } from '../../api/zohoItem';

function ZohoItemMaster() {
    const { enqueueSnackbar } = useSnackbar();
    const [currentTab, setCurrentTab] = useState(0);
    const [loading, setLoading] = useState(false);
    const [items, setItems] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterActive, setFilterActive] = useState('active');
    const [filterProductType, setFilterProductType] = useState('all');
    const [stats, setStats] = useState(null);
    const [syncing, setSyncing] = useState(false);
    const [syncResult, setSyncResult] = useState(null);
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [lastSyncTime, setLastSyncTime] = useState(null);

    // Get user role
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isAdmin = user.role === 'Admin';

    // Format time difference
    const formatTimeSince = (dateString) => {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    };

    // Fetch items
    const fetchItems = async () => {
        setLoading(true);
        try {
            const params = {
                search: searchTerm || undefined,
                active_only: filterActive === 'active',
                product_type: filterProductType === 'all' ? undefined : filterProductType,
                limit: 1000,
            };

            const response = await zohoItemAPI.getItems(params);
            setItems(response.items || []);

            // Calculate last sync time from items
            if (response.items && response.items.length > 0) {
                const syncTimes = response.items
                    .map(item => item.last_sync_at)
                    .filter(time => time !== null);

                if (syncTimes.length > 0) {
                    const mostRecent = syncTimes.reduce((latest, current) => {
                        return new Date(current) > new Date(latest) ? current : latest;
                    });
                    setLastSyncTime(mostRecent);
                }
            }
        } catch (error) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load items', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    // Fetch stats
    const fetchStats = async () => {
        try {
            const stats = await zohoItemAPI.getStats();
            setStats(stats);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    // Initial load
    useEffect(() => {
        fetchItems();
        fetchStats();
    }, [refreshTrigger, searchTerm, filterActive, filterProductType]);

    // Handle item update
    const handleItemUpdate = async (updatedRow, originalRow) => {
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

            await zohoItemAPI.updateItem(updatedRow.id, changes);

            enqueueSnackbar('Item updated successfully', { variant: 'success' });
            return updatedRow;
        } catch (error) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to update item', { variant: 'error' });
            return originalRow;
        }
    };

    // Handle sync
    const handleSync = async () => {
        setSyncing(true);
        setSyncResult(null);
        enqueueSnackbar('Sync started in background...', { variant: 'info' });

        try {
            await zohoItemAPI.syncFromZohoBooks(false);

            // Poll to check when sync completes
            const checkInterval = setInterval(async () => {
                try {
                    const progress = await zohoItemAPI.getSyncProgress();
                    if (!progress.in_progress) {
                        clearInterval(checkInterval);
                        setSyncResult({
                            total: progress.total,
                            added: progress.added,
                            updated: progress.updated,
                            skipped: progress.skipped,
                            errors: progress.errors
                        });
                        enqueueSnackbar('Sync completed!', { variant: 'success' });
                        setSyncing(false);
                        setRefreshTrigger((prev) => prev + 1);
                    }
                } catch (err) {
                    clearInterval(checkInterval);
                    setSyncing(false);
                }
            }, 2000);
        } catch (error) {
            setSyncing(false);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to start sync', { variant: 'error' });
        }
    };

    // Export to CSV
    const handleExport = () => {
        const csvContent = [
            ['ID', 'Item ID', 'Name', 'SKU', 'Description', 'Rate', 'Purchase Rate', 'Item Type', 'Product Type', 'HSN/SAC', 'Unit', 'Status', 'Taxable'],
            ...items.map((item) => [
                item.id,
                item.item_id,
                item.name,
                item.sku || '',
                item.description || '',
                item.rate || '',
                item.purchase_rate || '',
                item.item_type || '',
                item.product_type || '',
                item.hsn_or_sac || '',
                item.unit || '',
                item.status,
                item.is_taxable ? 'Yes' : 'No',
            ]),
        ]
            .map((row) => row.join(','))
            .join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `zoho_items_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    // DataGrid columns
    const columns = [
        { field: 'id', headerName: 'DB ID', width: 80, editable: false },
        { field: 'item_id', headerName: 'Zoho Item ID', width: 120, editable: false },
        { field: 'name', headerName: 'Item Name', width: 250, editable: isAdmin },
        { field: 'sku', headerName: 'SKU', width: 150, editable: isAdmin },
        { field: 'description', headerName: 'Description', width: 200, editable: isAdmin },
        { field: 'rate', headerName: 'Selling Price', width: 120, editable: isAdmin, type: 'number' },
        { field: 'purchase_rate', headerName: 'Purchase Price', width: 130, editable: isAdmin, type: 'number' },
        { field: 'item_type', headerName: 'Item Type', width: 150, editable: isAdmin },
        { field: 'product_type', headerName: 'Product Type', width: 120, editable: isAdmin },
        { field: 'hsn_or_sac', headerName: 'HSN/SAC', width: 120, editable: isAdmin },
        { field: 'unit', headerName: 'Unit', width: 100, editable: isAdmin },
        { field: 'status', headerName: 'Status', width: 100, editable: isAdmin },
        { field: 'is_taxable', headerName: 'Taxable', width: 100, editable: isAdmin, type: 'boolean' },
    ];

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                📚 Zoho Item Master
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                {user.full_name || user.email} | Role: {user.role}
            </Typography>

            {!isAdmin && (
                <Alert severity="info" sx={{ mb: 2 }}>
                    You have view-only access. Contact admin for edit permissions.
                </Alert>
            )}

            <Paper sx={{ mt: 2 }}>
                <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)}>
                    <Tab label="📊 Items" />
                    {isAdmin && <Tab label="🔄 Sync from Zoho Books" />}
                    {isAdmin && <Tab label="📈 Statistics" />}
                </Tabs>

                {/* Items Tab */}
                {currentTab === 0 && (
                    <Box sx={{ p: 3 }}>
                        <Grid container spacing={2} sx={{ mb: 2 }}>
                            <Grid item xs={12} md={4}>
                                <TextField
                                    fullWidth
                                    label="🔍 Search items"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    placeholder="Search by name, SKU, or HSN/SAC"
                                />
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <FormControl fullWidth>
                                    <InputLabel>Filter</InputLabel>
                                    <Select value={filterActive} onChange={(e) => setFilterActive(e.target.value)}>
                                        <MenuItem value="active">Active only</MenuItem>
                                        <MenuItem value="inactive">Inactive only</MenuItem>
                                        <MenuItem value="all">All items</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <FormControl fullWidth>
                                    <InputLabel>Product Type</InputLabel>
                                    <Select value={filterProductType} onChange={(e) => setFilterProductType(e.target.value)}>
                                        <MenuItem value="all">All</MenuItem>
                                        <MenuItem value="goods">Goods</MenuItem>
                                        <MenuItem value="service">Service</MenuItem>
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
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                    <Typography variant="body2">
                                        ✅ Found {items.length} items
                                    </Typography>
                                    {lastSyncTime && (
                                        <Typography variant="body2" color="text.secondary">
                                            🔄 Last synced: {formatTimeSince(lastSyncTime)}
                                        </Typography>
                                    )}
                                </Box>
                                <Box sx={{ height: 600, width: '100%' }}>
                                    <DataGrid
                                        rows={items}
                                        columns={columns}
                                        initialState={{
                                            pagination: {
                                                paginationModel: { pageSize: 25 },
                                            },
                                        }}
                                        pageSizeOptions={[10, 25, 50, 100]}
                                        disableRowSelectionOnClick
                                        processRowUpdate={handleItemUpdate}
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
                            🔄 Sync Items from Zoho Books
                        </Typography>
                        <Alert severity="info" sx={{ mb: 2 }}>
                            <strong>How Sync Works:</strong>
                            <ul>
                                <li>Fetches all items from Zoho Books API (with pagination)</li>
                                <li>Updates existing items with latest data from Zoho</li>
                                <li>Adds new items that don't exist locally</li>
                                <li>Zoho Books is the source of truth - local edits will be overwritten</li>
                            </ul>
                        </Alert>

                        <Alert severity="warning" sx={{ mb: 2 }}>
                            <strong>Scheduled Sync:</strong> Items are automatically synced daily at 4:00 AM IST.
                        </Alert>

                        <Button
                            variant="contained"
                            size="large"
                            startIcon={syncing ? <CircularProgress size={20} /> : <SyncIcon />}
                            onClick={handleSync}
                            disabled={syncing}
                        >
                            {syncing ? 'Syncing...' : '🔄 Sync Now'}
                        </Button>

                        {/* Sync Progress */}
                        {syncing && (
                            <Box sx={{ mt: 3 }}>
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    🔄 Syncing in progress... Please wait.
                                </Typography>
                                <LinearProgress sx={{ mt: 1 }} />
                            </Box>
                        )}

                        {/* Sync Result */}
                        {syncResult && !syncing && (
                            <Box sx={{ mt: 3 }}>
                                <Alert severity={syncResult.errors > 0 ? 'warning' : 'success'}>
                                    <Typography variant="body2">
                                        <strong>Sync Complete!</strong>
                                    </Typography>
                                    <Typography variant="body2" sx={{ mt: 1 }}>
                                        📊 Total Items: {syncResult.total}
                                    </Typography>
                                    <Typography variant="body2">
                                        ✅ Added: {syncResult.added} | 🔄 Updated: {syncResult.updated} |
                                        ⏭️ Skipped: {syncResult.skipped} | ❌ Errors: {syncResult.errors}
                                    </Typography>
                                </Alert>
                            </Box>
                        )}
                    </Box>
                )}

                {/* Statistics Tab */}
                {currentTab === 2 && isAdmin && (
                    <Box sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            📈 Item Statistics
                        </Typography>

                        {stats && (
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={3}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.total}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                📦 Total Items
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={3}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.active}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                ✅ Active
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={3}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.goods}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                📦 Goods
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={3}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.services}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                🛠️ Services
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

export default ZohoItemMaster;

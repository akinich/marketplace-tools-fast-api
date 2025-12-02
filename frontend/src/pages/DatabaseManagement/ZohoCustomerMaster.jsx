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
import { zohoCustomerAPI } from '../../api/zohoCustomer';

function ZohoCustomerMaster() {
    const { enqueueSnackbar } = useSnackbar();
    const [currentTab, setCurrentTab] = useState(0);
    const [loading, setLoading] = useState(false);
    const [customers, setCustomers] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterActive, setFilterActive] = useState('active');
    const [filterProductType, setFilterProductType] = useState('all');
    const [stats, setStats] = useState(null);
    const [syncing, setSyncing] = useState(false);
    const [syncResult, setSyncResult] = useState(null);
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [lastSyncTime, setLastSyncTime] = useState(null);
    const [lastSyncRunTime, setLastSyncRunTime] = useState(() => {
        // Load from localStorage on mount
        const stored = localStorage.getItem('zoho_customer_last_sync_run');
        return stored ? stored : null;
    });

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

    // Fetch customers
    const fetchCustomers = async () => {
        setLoading(true);
        try {
            const params = {
                search: searchTerm || undefined,
                active_only: filterActive === 'active',
                product_type: filterProductType === 'all' ? undefined : filterProductType,
                limit: 1000,
            };

            const response = await zohoCustomerAPI.getItems(params);
            setCustomers(response.customers || []);

            // Calculate last sync time from customers
            if (response.customers && response.customers.length > 0) {
                const syncTimes = response.customers
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
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load customers', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    // Fetch stats
    const fetchStats = async () => {
        try {
            const stats = await zohoCustomerAPI.getStats();
            setStats(stats);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    // Initial load
    useEffect(() => {
        fetchCustomers();
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

            await zohoCustomerAPI.updateItem(updatedRow.id, changes);

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
            await zohoCustomerAPI.syncFromZohoBooks(false);

            // Poll to check when sync completes
            let pollAttempts = 0;
            const maxPollAttempts = 150; // Max 5 minutes (150 * 2 seconds)

            const checkInterval = setInterval(async () => {
                try {
                    const progress = await zohoCustomerAPI.getSyncProgress();
                    pollAttempts = 0; // Reset on successful fetch

                    if (!progress.in_progress) {
                        clearInterval(checkInterval);

                        // Store sync completion time
                        const syncCompletionTime = new Date().toISOString();
                        setLastSyncRunTime(syncCompletionTime);
                        localStorage.setItem('zoho_customer_last_sync_run', syncCompletionTime);

                        setSyncResult({
                            total: progress.total,
                            added: progress.added,
                            updated: progress.updated,
                            skipped: progress.skipped,
                            errors: progress.errors,
                            status: progress.errors > 0 && progress.added === 0 && progress.updated === 0 ? 'failed' : 'completed'
                        });

                        // Show appropriate notification based on result
                        if (progress.errors > 0 && progress.added === 0 && progress.updated === 0) {
                            enqueueSnackbar('Sync failed with errors!', { variant: 'error' });
                        } else if (progress.errors > 0) {
                            enqueueSnackbar('Sync completed with some errors', { variant: 'warning' });
                        } else {
                            enqueueSnackbar('Sync completed successfully!', { variant: 'success' });
                        }

                        setSyncing(false);
                        setRefreshTrigger((prev) => prev + 1);
                    }
                } catch (err) {
                    pollAttempts++;
                    console.error(`Failed to fetch sync progress (attempt ${pollAttempts}):`, err);

                    // Only stop polling after multiple failures or max attempts reached
                    if (pollAttempts >= 5 || pollAttempts >= maxPollAttempts) {
                        clearInterval(checkInterval);
                        setSyncing(false);
                        enqueueSnackbar(
                            'Lost connection to sync progress. Sync may still be running in background. Please refresh the page to see results.',
                            { variant: 'warning', autoHideDuration: 8000 }
                        );
                    }
                    // Otherwise, keep polling (transient network error)
                }
            }, 2000);
        } catch (error) {
            setSyncResult({
                status: 'failed',
                errors: 1,
                total: 0,
                added: 0,
                updated: 0,
                skipped: 0
            });
            setSyncing(false);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to start sync', { variant: 'error' });
        }
    };

    // Export to CSV
    const handleExport = () => {
        const csvContent = [
            ['ID', 'Contact ID', 'Contact Name', 'Company Name', 'Email', 'Phone', 'Mobile', 'Customer Type', 'GST No', 'PAN No', 'Payment Terms', 'Outstanding', 'Credit Limit', 'Status', 'Notes'],
            ...customers.map((customer) => [
                customer.id,
                customer.contact_id,
                customer.contact_name,
                customer.company_name || '',
                customer.email || '',
                customer.phone || '',
                customer.mobile || '',
                customer.customer_type || '',
                customer.gst_no || '',
                customer.pan_no || '',
                customer.payment_terms_label || '',
                customer.outstanding_receivable_amount || '',
                customer.credit_limit || '',
                customer.status,
                customer.notes || '',
            ]),
        ]
            .map((row) => row.join(','))
            .join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `zoho_customers_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    // DataGrid columns
    const columns = [
        { field: 'id', headerName: 'DB ID', width: 80, editable: false },
        { field: 'contact_id', headerName: 'Zoho Contact ID', width: 120, editable: false },
        { field: 'contact_name', headerName: 'Contact Name', width: 200, editable: false },
        { field: 'company_name', headerName: 'Company Name', width: 200, editable: false },
        { field: 'email', headerName: 'Email', width: 200, editable: false },
        { field: 'phone', headerName: 'Phone', width: 130, editable: false },
        { field: 'mobile', headerName: 'Mobile', width: 130, editable: false },
        { field: 'customer_type', headerName: 'Type', width: 100, editable: false },
        { field: 'gst_no', headerName: 'GST No', width: 150, editable: false },
        { field: 'pan_no', headerName: 'PAN No', width: 120, editable: false },
        { field: 'payment_terms_label', headerName: 'Payment Terms', width: 150, editable: false },
        { field: 'outstanding_receivable_amount', headerName: 'Outstanding', width: 120, editable: false, type: 'number' },
        { field: 'credit_limit', headerName: 'Credit Limit', width: 120, editable: false, type: 'number' },
        { field: 'status', headerName: 'Status', width: 100, editable: false },
        { field: 'notes', headerName: 'Notes', width: 200, editable: true },
    ];

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                📚 Zoho Customer Master
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
                    <Tab label="📊 Customers" />
                    {isAdmin && <Tab label="🔄 Sync from Zoho Books" />}
                    {isAdmin && <Tab label="📈 Statistics" />}
                </Tabs>

                {/* Customers Tab */}
                {currentTab === 0 && (
                    <Box sx={{ p: 3 }}>
                        <Grid container spacing={2} sx={{ mb: 2 }}>
                            <Grid item xs={12} md={4}>
                                <TextField
                                    fullWidth
                                    label="🔍 Search customers"
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
                                        <MenuItem value="all">All customers</MenuItem>
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
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignCustomers: 'center', mb: 2 }}>
                                    <Typography variant="body2">
                                        ✅ Found {customers.length} customers
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', alignCustomers: 'flex-end' }}>
                                        {lastSyncRunTime && (
                                            <Typography variant="body2" color="text.secondary">
                                                🔄 Last sync run: {formatTimeSince(lastSyncRunTime)}
                                            </Typography>
                                        )}
                                        {lastSyncTime && lastSyncTime !== lastSyncRunTime && (
                                            <Typography variant="caption" color="text.secondary">
                                                Last item update: {formatTimeSince(lastSyncTime)}
                                            </Typography>
                                        )}
                                    </Box>
                                </Box>
                                <Box sx={{ height: 600, width: '100%' }}>
                                    <DataGrid
                                        rows={customers}
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
                            🔄 Sync Customers from Zoho Books
                        </Typography>
                        <Alert severity="info" sx={{ mb: 2 }}>
                            <strong>How Sync Works:</strong>
                            <ul>
                                <li>Fetches all customers from Zoho Books API (with pagination)</li>
                                <li>Updates existing customers with latest data from Zoho</li>
                                <li>Adds new customers that don't exist locally</li>
                                <li>Zoho Books is the source of truth - local edits will be overwritten</li>
                            </ul>
                        </Alert>

                        <Alert severity="warning" sx={{ mb: 2 }}>
                            <strong>Scheduled Sync:</strong> Customers are automatically synced daily at 4:00 AM IST.
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

                        {/* Sync Status */}
                        {syncing && (
                            <Box sx={{ mt: 3 }}>
                                <Alert severity="info">
                                    <Typography variant="body2">
                                        🔄 Syncing in progress... Please wait.
                                    </Typography>
                                </Alert>
                            </Box>
                        )}

                        {/* Sync Result */}
                        {syncResult && !syncing && (
                            <Box sx={{ mt: 3 }}>
                                <Alert severity={syncResult.status === 'failed' ? 'error' : (syncResult.errors > 0 ? 'warning' : 'success')}>
                                    <Typography variant="body2">
                                        <strong>
                                            {syncResult.status === 'failed' ? '❌ Sync Failed!' :
                                                syncResult.errors > 0 ? '⚠️ Sync Completed with Errors' : '✅ Sync Complete!'}
                                        </strong>
                                    </Typography>
                                    <Typography variant="body2" sx={{ mt: 1 }}>
                                        📊 Total Customers: {syncResult.total}
                                    </Typography>
                                    <Typography variant="body2">
                                        ✅ Added: {syncResult.added} | 🔄 Updated: {syncResult.updated} |
                                        ⏭️ Skipped: {syncResult.skipped} | ❌ Errors: {syncResult.errors}
                                    </Typography>
                                    {syncResult.status === 'failed' && (
                                        <Typography variant="body2" sx={{ mt: 1, color: 'error.main' }}>
                                            ⚠️ Please check logs or contact admin for details.
                                        </Typography>
                                    )}
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
                                                📦 Total Customers
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

export default ZohoCustomerMaster;

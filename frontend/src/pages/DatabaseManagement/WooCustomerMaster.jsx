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
} from '@mui/icons-material';
import { wooCustomerAPI } from '../../api/wooCustomer';

function WooCustomerMaster() {
    const { enqueueSnackbar } = useSnackbar();
    const [currentTab, setCurrentTab] = useState(0);
    const [loading, setLoading] = useState(false);
    const [customers, setCustomers] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterPayingOnly, setFilterPayingOnly] = useState(false);
    const [stats, setStats] = useState(null);
    const [syncing, setSyncing] = useState(false);
    const [syncResult, setSyncResult] = useState(null);
    const [syncProgress, setSyncProgress] = useState(null);
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [error, setError] = useState(null);
    const [lastSyncRunTime, setLastSyncRunTime] = useState(() => {
        // Load from localStorage on mount
        const stored = localStorage.getItem('woo_customer_last_sync_run');
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
        setError(null);
        try {
            const params = {
                search: searchTerm || undefined,
                paying_only: filterPayingOnly,
                limit: 5000,
            };

            const response = await wooCustomerAPI.getCustomers(params);
            setCustomers(response.customers || []);
        } catch (error) {
            console.error('Error fetching customers:', error);
            const errorMsg = error.response?.data?.detail || error.message || 'Failed to load customers';
            setError(errorMsg);
            enqueueSnackbar(errorMsg, { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    // Fetch stats
    const fetchStats = async () => {
        try {
            const stats = await wooCustomerAPI.getStats();
            setStats(stats);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    // Initial load
    useEffect(() => {
        console.log('WooCustomerMaster component mounted');
        fetchCustomers();
        fetchStats();

        // Check if sync is already in progress
        checkForOngoingSync();
    }, [refreshTrigger, searchTerm, filterPayingOnly]);

    // Check for ongoing sync on mount
    const checkForOngoingSync = async () => {
        try {
            const progress = await wooCustomerAPI.getSyncProgress();
            if (progress.in_progress) {
                console.log('Detected ongoing sync, starting progress monitoring');
                setSyncing(true);
                setSyncProgress(progress);
                startProgressPolling();
            }
        } catch (error) {
            console.error('Error checking sync progress:', error);
        }
    };

    // Start polling for sync progress
    const startProgressPolling = () => {
        let pollAttempts = 0;
        const maxPollAttempts = 150; // Max 5 minutes

        const checkInterval = setInterval(async () => {
            try {
                const progress = await wooCustomerAPI.getSyncProgress();
                pollAttempts = 0; // Reset on successful fetch

                // Update progress state for display
                if (progress.in_progress) {
                    setSyncProgress(progress);
                }

                if (!progress.in_progress) {
                    clearInterval(checkInterval);

                    console.log('Sync completed, progress data:', progress);

                    // Store sync completion time
                    const syncCompletionTime = new Date().toISOString();
                    setLastSyncRunTime(syncCompletionTime);
                    localStorage.setItem('woo_customer_last_sync_run', syncCompletionTime);

                    setSyncResult({
                        total: progress.total || 0,
                        added: progress.added || 0,
                        updated: progress.updated || 0,
                        skipped: progress.skipped || 0,
                        errors: progress.errors || 0,
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
                    setSyncProgress(null);
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
            }
        }, 2000);
    };

    // Handle customer update
    const handleCustomerUpdate = async (updatedRow, originalRow) => {
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

            await wooCustomerAPI.updateCustomer(updatedRow.id, changes);

            enqueueSnackbar('Customer updated successfully', { variant: 'success' });
            return updatedRow;
        } catch (error) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to update customer', { variant: 'error' });
            return originalRow;
        }
    };

    // Handle sync
    const handleSync = async () => {
        setSyncing(true);
        setSyncResult(null);
        setSyncProgress(null);
        enqueueSnackbar('Sync started in background...', { variant: 'info' });

        try {
            await wooCustomerAPI.syncFromWooCommerce();

            // Start polling for progress
            startProgressPolling();
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
            ['ID', 'Customer ID', 'Email', 'First Name', 'Last Name', 'Billing Company', 'Billing City', 'Billing State', 'Billing Country', 'Billing Phone', 'Shipping City', 'Shipping Country', 'Is Paying Customer', 'Date Created', 'Notes'],
            ...customers.map((customer) => [
                customer.id,
                customer.customer_id,
                customer.email || '',
                customer.first_name || '',
                customer.last_name || '',
                customer.billing_company || '',
                customer.billing_city || '',
                customer.billing_state || '',
                customer.billing_country || '',
                customer.billing_phone || '',
                customer.shipping_city || '',
                customer.shipping_country || '',
                customer.is_paying_customer ? 'Yes' : 'No',
                customer.date_created || '',
                customer.notes || '',
            ]),
        ]
            .map((row) => row.join(','))
            .join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `woo_customers_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    // DataGrid columns
    const columns = [
        { field: 'id', headerName: 'DB ID', width: 80, editable: false },
        { field: 'customer_id', headerName: 'WC Customer ID', width: 120, editable: false },
        { field: 'email', headerName: 'Email', width: 200, editable: false },
        { field: 'first_name', headerName: 'First Name', width: 130, editable: false },
        { field: 'last_name', headerName: 'Last Name', width: 130, editable: false },
        { field: 'billing_company', headerName: 'Company', width: 180, editable: false },
        { field: 'billing_city', headerName: 'Billing City', width: 130, editable: false },
        { field: 'billing_state', headerName: 'Billing State', width: 100, editable: false },
        { field: 'billing_country', headerName: 'Billing Country', width: 80, editable: false },
        { field: 'billing_phone', headerName: 'Phone', width: 130, editable: false },
        { field: 'shipping_city', headerName: 'Ship City', width: 130, editable: false },
        { field: 'shipping_country', headerName: 'Ship Country', width: 80, editable: false },
        { field: 'is_paying_customer', headerName: 'Paying', width: 80, editable: false, type: 'boolean' },
        { field: 'notes', headerName: 'Notes', width: 200, editable: true },
    ];

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                👥 Woo Customer Master
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                {user.full_name || user.email} | Role: {user.role}
            </Typography>

            {!isAdmin && (
                <Alert severity="info" sx={{ mb: 2 }}>
                    You have view and limited edit access (Notes only). Contact admin for full access.
                </Alert>
            )}

            <Paper sx={{ mt: 2 }}>
                <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)}>
                    <Tab label="📊 Customers" />
                    {isAdmin && <Tab label="🔄 Sync from WooCommerce" />}
                    {isAdmin && <Tab label="📈 Statistics" />}
                </Tabs>

                {/* Customers Tab */}
                {currentTab === 0 && (
                    <Box sx={{ p: 3 }}>
                        <Grid container spacing={2} sx={{ mb: 2 }}>
                            <Grid item xs={12} md={5}>
                                <TextField
                                    fullWidth
                                    label="🔍 Search customers"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    placeholder="Search by name, email, or company"
                                />
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <FormControl fullWidth>
                                    <InputLabel>Filter</InputLabel>
                                    <Select value={filterPayingOnly ? 'paying' : 'all'} onChange={(e) => setFilterPayingOnly(e.target.value === 'paying')}>
                                        <MenuItem value="all">All customers</MenuItem>
                                        <MenuItem value="paying">Paying customers only</MenuItem>
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
                            <Grid item xs={12} md={2}>
                                <Button
                                    fullWidth
                                    variant="contained"
                                    startIcon={<DownloadIcon />}
                                    onClick={handleExport}
                                    sx={{ height: '56px' }}
                                >
                                    Export CSV
                                </Button>
                            </Grid>
                        </Grid>

                        {error && (
                            <Alert severity="error" sx={{ mb: 2, mt: 2 }}>
                                <strong>Error loading customers:</strong> {error}
                                <br />
                                <Typography variant="caption">
                                    Make sure the backend server is running and the woo_customer routes are loaded.
                                </Typography>
                            </Alert>
                        )}

                        {loading ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                                <CircularProgress />
                            </Box>
                        ) : (
                            <>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                    <Typography variant="body2">
                                        ✅ Found {customers.length} customers
                                    </Typography>
                                    {lastSyncRunTime && (
                                        <Typography variant="body2" color="text.secondary">
                                            🔄 Last sync: {formatTimeSince(lastSyncRunTime)}
                                        </Typography>
                                    )}
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
                                        processRowUpdate={handleCustomerUpdate}
                                    />
                                </Box>
                            </>
                        )}
                    </Box>
                )}

                {/* Sync Tab */}
                {currentTab === 1 && isAdmin && (
                    <Box sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            🔄 Sync Customers from WooCommerce
                        </Typography>
                        <Alert severity="info" sx={{ mb: 2 }}>
                            <strong>How Sync Works:</strong>
                            <ul>
                                <li>Fetches all customers from WooCommerce API (with pagination)</li>
                                <li>Updates existing customers with latest data from WooCommerce</li>
                                <li>Adds new customers that don't exist locally</li>
                                <li>WooCommerce is the source of truth - local edits will be overwritten</li>
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
                                    <Typography variant="body2" gutterBottom>
                                        🔄 Syncing in progress...
                                    </Typography>

                                    {syncProgress && (
                                        <>
                                            <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
                                                {syncProgress.current} / {syncProgress.total} customers ({syncProgress.percentage}%)
                                            </Typography>

                                            <LinearProgress
                                                variant="determinate"
                                                value={syncProgress.percentage}
                                                sx={{ height: 10, borderRadius: 5, mb: 2 }}
                                            />

                                            <Grid container spacing={2}>
                                                <Grid item xs={3}>
                                                    <Typography variant="caption" color="text.secondary">
                                                        ✅ Added: {syncProgress.added}
                                                    </Typography>
                                                </Grid>
                                                <Grid item xs={3}>
                                                    <Typography variant="caption" color="text.secondary">
                                                        🔄 Updated: {syncProgress.updated}
                                                    </Typography>
                                                </Grid>
                                                <Grid item xs={3}>
                                                    <Typography variant="caption" color="text.secondary">
                                                        ⏭️ Skipped: {syncProgress.skipped}
                                                    </Typography>
                                                </Grid>
                                                <Grid item xs={3}>
                                                    <Typography variant="caption" color="text.secondary">
                                                        ❌ Errors: {syncProgress.errors}
                                                    </Typography>
                                                </Grid>
                                            </Grid>
                                        </>
                                    )}

                                    {!syncProgress && (
                                        <Typography variant="body2" sx={{ mt: 1 }}>
                                            Initializing sync...
                                        </Typography>
                                    )}
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
                            📈 Customer Statistics
                        </Typography>

                        {stats && (
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.total}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                👥 Total Customers
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.paying_customers}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                💰 Paying Customers
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.countries}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                🌍 Countries
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.india_customers}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                🇮🇳 India Customers
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                                <Grid item xs={12} md={2.4}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h4">{stats.new_this_month}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                🆕 New This Month
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

export default WooCustomerMaster;

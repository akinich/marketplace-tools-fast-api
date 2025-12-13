import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box,
    Paper,
    Typography,
    Tabs,
    Tab,
    Button,
    CircularProgress,
    Alert,
    Chip,
    IconButton,
    Tooltip,
} from '@mui/material';
import {
    ArrowBack as BackIcon,
    Edit as EditIcon,
    Download as DownloadIcon,
    Upload as UploadIcon,
    Add as AddIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import priceListAPI, { PriceList, PriceHistoryItem, CustomerPriceListInfo } from '../../api/priceList';
import { formatDate } from '../../utils/formatters';
import PriceListDialog from './components/PriceListDialog';
import PriceListItemsGrid from './components/PriceListItemsGrid';
import ExcelImportDialog from './components/ExcelImportDialog';
import AddItemDialog from './components/AddItemDialog';

function PriceListDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();

    const [loading, setLoading] = useState(true);
    const [priceList, setPriceList] = useState<PriceList | null>(null);
    const [currentTab, setCurrentTab] = useState(0);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [importDialogOpen, setImportDialogOpen] = useState(false);
    const [addItemDialogOpen, setAddItemDialogOpen] = useState(false);
    const [history, setHistory] = useState<PriceHistoryItem[]>([]);
    const [customers, setCustomers] = useState<CustomerPriceListInfo[]>([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [loadingCustomers, setLoadingCustomers] = useState(false);

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isAdmin = user.role === 'Admin';

    // Fetch price list
    const fetchPriceList = async () => {
        if (!id) return;

        setLoading(true);
        try {
            const data = await priceListAPI.getById(parseInt(id));
            setPriceList(data);
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load price list', { variant: 'error' });
            navigate('/outward/price-lists');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPriceList();
    }, [id]);

    // Load tab data when switching tabs
    useEffect(() => {
        if (!priceList) return;

        if (currentTab === 1 && customers.length === 0) {
            fetchCustomers();
        } else if (currentTab === 2 && history.length === 0) {
            fetchHistory();
        }
    }, [currentTab, priceList]);

    // Fetch customers assigned to this price list
    const fetchCustomers = async () => {
        if (!id) return;
        setLoadingCustomers(true);
        try {
            const response = await priceListAPI.getAssignedCustomers(parseInt(id));
            setCustomers(response.customers);
        } catch (error: any) {
            enqueueSnackbar('Failed to load customers', { variant: 'error' });
        } finally {
            setLoadingCustomers(false);
        }
    };

    // Fetch price list history
    const fetchHistory = async () => {
        if (!id) return;
        setLoadingHistory(true);
        try {
            const response = await priceListAPI.getHistory(parseInt(id));
            setHistory(response.history);
        } catch (error: any) {
            enqueueSnackbar('Failed to load history', { variant: 'error' });
        } finally {
            setLoadingHistory(false);
        }
    };

    // Handle export
    const handleExport = async () => {
        if (!priceList) return;

        try {
            const blob = await priceListAPI.exportToExcel(priceList.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `price_list_${priceList.price_list_name.replace(/ /g, '_')}.xlsx`;
            a.click();
            window.URL.revokeObjectURL(url);
            enqueueSnackbar('Exported successfully', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar('Failed to export', { variant: 'error' });
        }
    };

    // Handle template download
    const handleDownloadTemplate = async () => {
        try {
            const blob = await priceListAPI.downloadTemplate();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'price_list_template.xlsx';
            a.click();
            window.URL.revokeObjectURL(url);
            enqueueSnackbar('Template downloaded', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar('Failed to download template', { variant: 'error' });
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (!priceList) {
        return null;
    }

    // Status badge
    const getStatusBadge = () => {
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
                label={labels[priceList.status] || priceList.status}
                color={colors[priceList.status] || 'default'}
            />
        );
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <IconButton onClick={() => navigate('/outward/price-lists')}>
                    <BackIcon />
                </IconButton>
                <Box sx={{ ml: 2, flex: 1 }}>
                    <Typography variant="h4">
                        {priceList.price_list_name}
                    </Typography>
                    {priceList.description && (
                        <Typography variant="body2" color="text.secondary">
                            {priceList.description}
                        </Typography>
                    )}
                </Box>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    {getStatusBadge()}
                    {isAdmin && (
                        <Tooltip title="Edit">
                            <IconButton onClick={() => setEditDialogOpen(true)}>
                                <EditIcon />
                            </IconButton>
                        </Tooltip>
                    )}
                </Box>
            </Box>

            {/* Info Cards */}
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Paper sx={{ p: 2, flex: 1 }}>
                    <Typography variant="caption" color="text.secondary">Valid From</Typography>
                    <Typography variant="h6">
                        {formatDate(priceList.valid_from)}
                    </Typography>
                </Paper>
                <Paper sx={{ p: 2, flex: 1 }}>
                    <Typography variant="caption" color="text.secondary">Valid To</Typography>
                    <Typography variant="h6">
                        {(priceList.valid_to ? formatDate(priceList.valid_to) : 'Indefinite')}
                    </Typography>
                </Paper>
                <Paper sx={{ p: 2, flex: 1 }}>
                    <Typography variant="caption" color="text.secondary">Items</Typography>
                    <Typography variant="h6">{priceList.items_count}</Typography>
                </Paper>
                <Paper sx={{ p: 2, flex: 1 }}>
                    <Typography variant="caption" color="text.secondary">Customers</Typography>
                    <Typography variant="h6">{priceList.customers_count}</Typography>
                </Paper>
            </Box>

            {/* Tabs */}
            <Paper>
                <Tabs value={currentTab} onChange={(_, v) => setCurrentTab(v)}>
                    <Tab label="📦 Items" />
                    <Tab label="👥 Customers" />
                    <Tab label="📜 History" />
                </Tabs>

                {/* Items Tab */}
                {currentTab === 0 && (
                    <Box sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                            {isAdmin && (
                                <>
                                    <Button
                                        variant="contained"
                                        startIcon={<AddIcon />}
                                        onClick={() => setAddItemDialogOpen(true)}
                                    >
                                        Add Item
                                    </Button>
                                    <Button
                                        variant="outlined"
                                        startIcon={<UploadIcon />}
                                        onClick={() => setImportDialogOpen(true)}
                                    >
                                        Import from Excel
                                    </Button>
                                    <Button
                                        variant="outlined"
                                        onClick={handleDownloadTemplate}
                                    >
                                        Download Template
                                    </Button>
                                </>
                            )}
                            <Button
                                variant="outlined"
                                startIcon={<DownloadIcon />}
                                onClick={handleExport}
                            >
                                Export to Excel
                            </Button>
                        </Box>

                        <PriceListItemsGrid priceListId={priceList.id} isAdmin={isAdmin} />
                    </Box>
                )}

                {/* Customers Tab */}
                {currentTab === 1 && (
                    <Box sx={{ p: 3 }}>
                        {loadingCustomers ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                                <CircularProgress />
                            </Box>
                        ) : customers.length === 0 ? (
                            <Alert severity="info">
                                No customers assigned to this price list.
                            </Alert>
                        ) : (
                            <Box>
                                <Typography variant="body2" gutterBottom>
                                    {customers.length} customer{customers.length !== 1 ? 's' : ''} using this price list
                                </Typography>
                                <Box sx={{ mt: 2 }}>
                                    {customers.map((customer) => (
                                        <Paper key={customer.customer_id} sx={{ p: 2, mb: 1 }}>
                                            <Typography variant="body1" fontWeight="bold">
                                                {customer.company_name}
                                            </Typography>
                                            {customer.contact_name && (
                                                <Typography variant="body2" color="text.secondary">
                                                    Contact: {customer.contact_name}
                                                </Typography>
                                            )}
                                        </Paper>
                                    ))}
                                </Box>
                            </Box>
                        )}
                    </Box>
                )}

                {/* History Tab */}
                {currentTab === 2 && (
                    <Box sx={{ p: 3 }}>
                        {loadingHistory ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                                <CircularProgress />
                            </Box>
                        ) : history.length === 0 ? (
                            <Alert severity="info">
                                No changes recorded yet.
                            </Alert>
                        ) : (
                            <Box>
                                <Typography variant="body2" gutterBottom>
                                    {history.length} change{history.length !== 1 ? 's' : ''} recorded
                                </Typography>
                                <Box sx={{ mt: 2 }}>
                                    {history.map((h) => (
                                        <Paper key={h.id} sx={{ p: 2, mb: 1 }}>
                                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <Box>
                                                    <Typography variant="body2" fontWeight="bold">
                                                        {h.field_changed}
                                                        {h.item_name && ` - ${h.item_name}`}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {h.old_value ? `${h.old_value} → ${h.new_value}` : h.new_value}
                                                    </Typography>
                                                </Box>
                                                <Box sx={{ textAlign: 'right' }}>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {new Date(h.changed_at).toLocaleString()}
                                                    </Typography>
                                                    {h.changed_by && (
                                                        <Typography variant="caption" display="block">
                                                            by {h.changed_by}
                                                        </Typography>
                                                    )}
                                                </Box>
                                            </Box>
                                        </Paper>
                                    ))}
                                </Box>
                            </Box>
                        )}
                    </Box>
                )}
            </Paper>

            {/* Dialogs */}
            <PriceListDialog
                open={editDialogOpen}
                priceList={priceList}
                onClose={(refresh?: boolean) => {
                    setEditDialogOpen(false);
                    if (refresh) fetchPriceList();
                }}
            />

            <ExcelImportDialog
                open={importDialogOpen}
                priceListId={priceList.id}
                onClose={(refresh?: boolean) => {
                    setImportDialogOpen(false);
                    if (refresh) fetchPriceList();
                }}
            />

            <AddItemDialog
                open={addItemDialogOpen}
                priceListId={priceList.id}
                onClose={(refresh?: boolean) => {
                    setAddItemDialogOpen(false);
                    if (refresh) fetchPriceList();
                }}
            />
        </Box>
    );
}

export default PriceListDetail;

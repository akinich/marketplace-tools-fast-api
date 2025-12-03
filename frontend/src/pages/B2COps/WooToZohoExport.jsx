import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    TextField,
    Button,
    Tab,
    Tabs,
    Alert,
    CircularProgress,
    Divider,
    Paper
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useSnackbar } from 'notistack';
import { format, subDays } from 'date-fns';
import DownloadIcon from '@mui/icons-material/Download';
import PreviewIcon from '@mui/icons-material/Visibility';
import HistoryIcon from '@mui/icons-material/History';
import RefreshIcon from '@mui/icons-material/Refresh';

import { wooToZohoAPI } from '../../api/wooToZoho';

const WooToZohoExport = () => {
    const { enqueueSnackbar } = useSnackbar();
    const [tabValue, setTabValue] = useState(0);

    // Export State
    const [startDate, setStartDate] = useState(subDays(new Date(), 7));
    const [endDate, setEndDate] = useState(new Date());
    const [invoicePrefix, setInvoicePrefix] = useState('ECHE/2526/');
    const [startSequence, setStartSequence] = useState('');
    const [loadingSequence, setLoadingSequence] = useState(false);

    const [previewData, setPreviewData] = useState(null);
    const [loadingPreview, setLoadingPreview] = useState(false);
    const [exporting, setExporting] = useState(false);

    // History State
    const [historyData, setHistoryData] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [historyStartDate, setHistoryStartDate] = useState(subDays(new Date(), 30));
    const [historyEndDate, setHistoryEndDate] = useState(new Date());

    // Fetch suggested sequence on mount and when prefix changes
    useEffect(() => {
        const fetchSequence = async () => {
            if (!invoicePrefix) return;
            setLoadingSequence(true);
            try {
                const data = await wooToZohoAPI.getLastSequence(invoicePrefix);
                setStartSequence(data.suggested_sequence.toString());
            } catch (error) {
                console.error('Error fetching sequence:', error);
            } finally {
                setLoadingSequence(false);
            }
        };

        // Debounce slightly
        const timer = setTimeout(fetchSequence, 500);
        return () => clearTimeout(timer);
    }, [invoicePrefix]);

    // Fetch history when tab changes to history
    useEffect(() => {
        if (tabValue === 1) {
            fetchHistory();
        }
    }, [tabValue, historyStartDate, historyEndDate]);

    const fetchHistory = async () => {
        setLoadingHistory(true);
        try {
            const data = await wooToZohoAPI.getHistory({
                start_date: format(historyStartDate, 'yyyy-MM-dd'),
                end_date: format(historyEndDate, 'yyyy-MM-dd')
            });
            setHistoryData(data);
        } catch (error) {
            enqueueSnackbar('Failed to fetch history', { variant: 'error' });
        } finally {
            setLoadingHistory(false);
        }
    };

    const handlePreview = async () => {
        if (!startSequence) {
            enqueueSnackbar('Please enter a start sequence', { variant: 'warning' });
            return;
        }

        setLoadingPreview(true);
        setPreviewData(null);

        try {
            const data = await wooToZohoAPI.previewExport({
                start_date: format(startDate, 'yyyy-MM-dd'),
                end_date: format(endDate, 'yyyy-MM-dd'),
                invoice_prefix: invoicePrefix,
                start_sequence: parseInt(startSequence)
            });

            if (data.total_orders === 0) {
                enqueueSnackbar('No completed orders found in this date range', { variant: 'info' });
            } else {
                setPreviewData(data);
                enqueueSnackbar(`Found ${data.total_orders} orders`, { variant: 'success' });
            }
        } catch (error) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to fetch preview', { variant: 'error' });
        } finally {
            setLoadingPreview(false);
        }
    };

    const handleExport = async () => {
        if (!previewData) return;

        setExporting(true);
        try {
            const blob = await wooToZohoAPI.exportOrders({
                start_date: format(startDate, 'yyyy-MM-dd'),
                end_date: format(endDate, 'yyyy-MM-dd'),
                invoice_prefix: invoicePrefix,
                start_sequence: parseInt(startSequence)
            });

            // Create download link
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `orders_export_${format(startDate, 'yyyyMMdd')}_${format(endDate, 'yyyyMMdd')}.zip`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);

            enqueueSnackbar('Export downloaded successfully', { variant: 'success' });

            // Refresh sequence for next time
            const seqData = await wooToZohoAPI.getLastSequence(invoicePrefix);
            setStartSequence(seqData.suggested_sequence.toString());
            setPreviewData(null); // Clear preview

        } catch (error) {
            enqueueSnackbar('Export failed', { variant: 'error' });
        } finally {
            setExporting(false);
        }
    };

    const previewColumns = [
        { field: 'Invoice Number', headerName: 'Invoice #', width: 150 },
        { field: 'Invoice Date', headerName: 'Date', width: 120 },
        { field: 'Customer Name', headerName: 'Customer', width: 200 },
        { field: 'Item Name', headerName: 'Item', width: 250 },
        { field: 'Quantity', headerName: 'Qty', width: 80 },
        { field: 'Item Price', headerName: 'Price', width: 100 },
        { field: 'HSN/SAC', headerName: 'HSN', width: 120 },
    ];

    const historyColumns = [
        { field: 'invoice_number', headerName: 'Invoice #', width: 150 },
        {
            field: 'order_date', headerName: 'Order Date', width: 180,
            valueFormatter: (params) => params.value ? format(new Date(params.value), 'yyyy-MM-dd HH:mm') : ''
        },
        { field: 'customer_name', headerName: 'Customer', width: 200 },
        {
            field: 'order_total', headerName: 'Total', width: 120,
            valueFormatter: (params) => `₹${parseFloat(params.value).toFixed(2)}`
        },
        { field: 'total_orders_in_export', headerName: 'Orders in Batch', width: 150 },
        { field: 'exported_by_email', headerName: 'Exported By', width: 200 },
        {
            field: 'created_at', headerName: 'Exported At', width: 180,
            valueFormatter: (params) => params.value ? format(new Date(params.value), 'yyyy-MM-dd HH:mm') : ''
        },
    ];

    return (
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Box sx={{ p: 3 }}>
                <Typography variant="h4" gutterBottom>
                    WooCommerce to Zoho Export
                </Typography>

                <Paper sx={{ width: '100%', mb: 2 }}>
                    <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
                        <Tab label="Export Orders" icon={<DownloadIcon />} iconPosition="start" />
                        <Tab label="Export History" icon={<HistoryIcon />} iconPosition="start" />
                    </Tabs>
                </Paper>

                {tabValue === 0 && (
                    <Grid container spacing={3}>
                        <Grid item xs={12}>
                            <Card>
                                <CardContent>
                                    <Grid container spacing={3} alignItems="center">
                                        <Grid item xs={12} md={3}>
                                            <DatePicker
                                                label="Start Date"
                                                value={startDate}
                                                onChange={(newValue) => setStartDate(newValue)}
                                                renderInput={(params) => <TextField {...params} fullWidth />}
                                            />
                                        </Grid>
                                        <Grid item xs={12} md={3}>
                                            <DatePicker
                                                label="End Date"
                                                value={endDate}
                                                onChange={(newValue) => setEndDate(newValue)}
                                                renderInput={(params) => <TextField {...params} fullWidth />}
                                            />
                                        </Grid>
                                        <Grid item xs={12} md={3}>
                                            <TextField
                                                label="Invoice Prefix"
                                                value={invoicePrefix}
                                                onChange={(e) => setInvoicePrefix(e.target.value)}
                                                fullWidth
                                                helperText="e.g. ECHE/2526/"
                                            />
                                        </Grid>
                                        <Grid item xs={12} md={3}>
                                            <TextField
                                                label="Start Sequence"
                                                value={startSequence}
                                                onChange={(e) => setStartSequence(e.target.value)}
                                                fullWidth
                                                type="number"
                                                disabled={loadingSequence}
                                                InputProps={{
                                                    endAdornment: loadingSequence && <CircularProgress size={20} />
                                                }}
                                            />
                                        </Grid>
                                        <Grid item xs={12}>
                                            <Button
                                                variant="contained"
                                                startIcon={<PreviewIcon />}
                                                onClick={handlePreview}
                                                disabled={loadingPreview || exporting}
                                                sx={{ mr: 2 }}
                                            >
                                                {loadingPreview ? 'Fetching...' : 'Fetch & Preview'}
                                            </Button>

                                            <Button
                                                variant="contained"
                                                color="success"
                                                startIcon={<DownloadIcon />}
                                                onClick={handleExport}
                                                disabled={!previewData || exporting}
                                            >
                                                {exporting ? 'Exporting...' : 'Export & Download ZIP'}
                                            </Button>
                                        </Grid>
                                    </Grid>
                                </CardContent>
                            </Card>
                        </Grid>

                        {previewData && (
                            <Grid item xs={12}>
                                <Card sx={{ mb: 3 }}>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Summary
                                        </Typography>
                                        <Grid container spacing={2}>
                                            <Grid item xs={3}>
                                                <Typography variant="subtitle2" color="textSecondary">Total Orders</Typography>
                                                <Typography variant="h6">{previewData.summary.total_orders}</Typography>
                                            </Grid>
                                            <Grid item xs={3}>
                                                <Typography variant="subtitle2" color="textSecondary">Date Range</Typography>
                                                <Typography variant="body1">{previewData.summary.date_range}</Typography>
                                            </Grid>
                                            <Grid item xs={3}>
                                                <Typography variant="subtitle2" color="textSecondary">Invoice Range</Typography>
                                                <Typography variant="body1">{previewData.summary.invoice_range}</Typography>
                                            </Grid>
                                        </Grid>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Line Items Preview (First 50 rows)
                                        </Typography>
                                        <Box sx={{ height: 400, width: '100%' }}>
                                            <DataGrid
                                                rows={previewData.csv_rows}
                                                columns={previewColumns}
                                                getRowId={(row) => `${row['Invoice Number']}-${row['Item Name']}`}
                                                pageSize={50}
                                                rowsPerPageOptions={[50]}
                                                disableSelectionOnClick
                                                density="compact"
                                            />
                                        </Box>
                                    </CardContent>
                                </Card>
                            </Grid>
                        )}
                    </Grid>
                )}

                {tabValue === 1 && (
                    <Grid container spacing={3}>
                        <Grid item xs={12}>
                            <Card>
                                <CardContent>
                                    <Grid container spacing={2} alignItems="center">
                                        <Grid item xs={12} md={4}>
                                            <DatePicker
                                                label="From Date"
                                                value={historyStartDate}
                                                onChange={(newValue) => setHistoryStartDate(newValue)}
                                                renderInput={(params) => <TextField {...params} fullWidth />}
                                            />
                                        </Grid>
                                        <Grid item xs={12} md={4}>
                                            <DatePicker
                                                label="To Date"
                                                value={historyEndDate}
                                                onChange={(newValue) => setHistoryEndDate(newValue)}
                                                renderInput={(params) => <TextField {...params} fullWidth />}
                                            />
                                        </Grid>
                                        <Grid item xs={12} md={4}>
                                            <Button
                                                variant="outlined"
                                                startIcon={<RefreshIcon />}
                                                onClick={fetchHistory}
                                                disabled={loadingHistory}
                                            >
                                                Refresh
                                            </Button>
                                        </Grid>
                                    </Grid>
                                </CardContent>
                            </Card>
                        </Grid>

                        <Grid item xs={12}>
                            <Card>
                                <CardContent>
                                    <Box sx={{ height: 600, width: '100%' }}>
                                        <DataGrid
                                            rows={historyData}
                                            columns={historyColumns}
                                            pageSize={20}
                                            rowsPerPageOptions={[20, 50, 100]}
                                            disableSelectionOnClick
                                            loading={loadingHistory}
                                            getRowId={(row) => row.id}
                                        />
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>
                    </Grid>
                )}
            </Box>
        </LocalizationProvider>
    );
};

export default WooToZohoExport;

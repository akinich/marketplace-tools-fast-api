/**
 * WooCommerce to Zoho Export Component
 * Version: 1.1.0
 * Last Updated: 2025-12-01
 *
 * Description:
 *   Export WooCommerce orders to Zoho Books compatible format
 *   - Fetches orders from Woo
 *   - Maps products/customers to Zoho IDs
 *   - Generates CSV/Excel for import
 *   - Maintains export history
 */

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
    CircularProgress,
    Paper
} from '@mui/material';
import { DataGrid, GridColDef, useGridApiRef } from '@mui/x-data-grid';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useSnackbar } from 'notistack';
import { format, subDays } from 'date-fns';
import DownloadIcon from '@mui/icons-material/Download';
import PreviewIcon from '@mui/icons-material/Visibility';
import HistoryIcon from '@mui/icons-material/History';
import RefreshIcon from '@mui/icons-material/Refresh';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';

import { wooToZohoAPI } from '../../api/wooToZoho';

interface ExportPreviewData {
    total_orders: number;
    summary: {
        total_orders: number;
        date_range: string;
        invoice_range: string;
    };
    csv_rows: any[];
}

interface ExportHistoryItem {
    id: number;
    invoice_number: string;
    order_date: string;
    customer_name: string;
    order_total: number;
    total_orders_in_export: number;
    exported_by_email: string;
    created_at: string;
}

const WooToZohoExport: React.FC = () => {
    const { enqueueSnackbar } = useSnackbar();
    const previewGridRef = useGridApiRef();
    const historyGridRef = useGridApiRef();
    const [tabValue, setTabValue] = useState(0);

    // Export State
    const [startDate, setStartDate] = useState<Date | null>(subDays(new Date(), 7));
    const [endDate, setEndDate] = useState<Date | null>(new Date());
    const [invoicePrefix, setInvoicePrefix] = useState('ECHE/2526/');
    const [startSequence, setStartSequence] = useState('');
    const [loadingSequence, setLoadingSequence] = useState(false);

    const [previewData, setPreviewData] = useState<ExportPreviewData | null>(null);
    const [loadingPreview, setLoadingPreview] = useState(false);
    const [exporting, setExporting] = useState(false);
    const [isPreviewFullscreen, setIsPreviewFullscreen] = useState(false);

    // History State
    const [historyData, setHistoryData] = useState<ExportHistoryItem[]>([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [historyStartDate, setHistoryStartDate] = useState<Date | null>(subDays(new Date(), 30));
    const [historyEndDate, setHistoryEndDate] = useState<Date | null>(new Date());
    const [isHistoryFullscreen, setIsHistoryFullscreen] = useState(false);

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
        if (!historyStartDate || !historyEndDate) return;
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
        if (!startDate || !endDate) {
            enqueueSnackbar('Please select starte and end dates', { variant: 'warning' });
            return;
        }
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
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to fetch preview', { variant: 'error' });
        } finally {
            setLoadingPreview(false);
        }
    };

    const handleExport = async () => {
        if (!previewData || !startDate || !endDate) return;

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
            link.parentNode?.removeChild(link);

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

    const previewColumns: GridColDef[] = [
        { field: 'Invoice Number', headerName: 'Invoice #', width: 150 },
        { field: 'Invoice Date', headerName: 'Date', width: 120 },
        { field: 'Customer Name', headerName: 'Customer', width: 200 },
        { field: 'Item Name', headerName: 'Item', width: 250 },
        { field: 'Quantity', headerName: 'Qty', width: 80 },
        { field: 'Item Price', headerName: 'Price', width: 100 },
        { field: 'HSN/SAC', headerName: 'HSN', width: 120 },
    ];

    const historyColumns: GridColDef[] = [
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
                    <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
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
                                                slotProps={{ textField: { fullWidth: true } }}
                                            />
                                        </Grid>
                                        <Grid item xs={12} md={3}>
                                            <DatePicker
                                                label="End Date"
                                                value={endDate}
                                                onChange={(newValue) => setEndDate(newValue)}
                                                slotProps={{ textField: { fullWidth: true } }}
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
                                        <Box sx={{
                                            height: isPreviewFullscreen ? '100vh' : 400,
                                            width: '100%',
                                            ...(isPreviewFullscreen && {
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
                                                apiRef={previewGridRef}
                                                rows={previewData.csv_rows}
                                                columns={previewColumns}
                                                getRowId={(row) => `${row['Invoice Number']}-${row['Item Name']}`}
                                                initialState={{
                                                    pagination: { paginationModel: { pageSize: 50, page: 0 } },
                                                }}
                                                pageSizeOptions={[50]}
                                                disableRowSelectionOnClick
                                                density="compact"
                                                slots={{
                                                    toolbar: () => (
                                                        <Box sx={{ p: 1, display: 'flex', gap: 1, alignItems: 'center', borderBottom: '1px solid #e0e0e0' }}>
                                                            <Box sx={{ flexGrow: 1 }} />
                                                            <Button
                                                                startIcon={isPreviewFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                                                                onClick={() => setIsPreviewFullscreen(!isPreviewFullscreen)}
                                                                size="small"
                                                            >
                                                                {isPreviewFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
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
                                                }}
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
                                                slotProps={{ textField: { fullWidth: true } }}
                                            />
                                        </Grid>
                                        <Grid item xs={12} md={4}>
                                            <DatePicker
                                                label="To Date"
                                                value={historyEndDate}
                                                onChange={(newValue) => setHistoryEndDate(newValue)}
                                                slotProps={{ textField: { fullWidth: true } }}
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
                                    <Box sx={{
                                        height: isHistoryFullscreen ? '100vh' : 600,
                                        width: '100%',
                                        ...(isHistoryFullscreen && {
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
                                            apiRef={historyGridRef}
                                            rows={historyData}
                                            columns={historyColumns}
                                            initialState={{
                                                pagination: { paginationModel: { pageSize: 20, page: 0 } },
                                            }}
                                            pageSizeOptions={[20, 50, 100]}
                                            disableRowSelectionOnClick
                                            loading={loadingHistory}
                                            getRowId={(row) => row.id}
                                            slots={{
                                                toolbar: () => (
                                                    <Box sx={{ p: 1, display: 'flex', gap: 1, alignItems: 'center', borderBottom: '1px solid #e0e0e0' }}>
                                                        <Box sx={{ flexGrow: 1 }} />
                                                        <Button
                                                            startIcon={isHistoryFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                                                            onClick={() => setIsHistoryFullscreen(!isHistoryFullscreen)}
                                                            size="small"
                                                        >
                                                            {isHistoryFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
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
                                            }}
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

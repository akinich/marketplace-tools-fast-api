/**
 * Stock Reports Page
 * Version: 1.0.0
 * Created: 2024-12-12
 *
 * Generate and export inventory reports
 */

import React, { useState } from 'react';
import {
    Box,
    Card,
    Typography,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    TextField,
    CircularProgress,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Alert,
} from '@mui/material';
import {
    Download as DownloadIcon,
    Assessment as ReportIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { inventoryAPI } from '../../../api/inventory';
import { formatDateForDisplay } from '../../../utils/dateUtils';

type ReportType = 'current_stock' | 'movements' | 'batch_age';

const ReportsPage: React.FC = () => {
    const { enqueueSnackbar } = useSnackbar();

    const [reportType, setReportType] = useState<ReportType>('current_stock');
    const [loading, setLoading] = useState(false);
    const [reportData, setReportData] = useState<any>(null);

    // Current Stock filters
    const [stockFilters, setStockFilters] = useState({
        location: '',
        status: '',
        include_zero_stock: false,
    });

    // Movement filters
    const [movementFilters, setMovementFilters] = useState({
        date_from: '',
        date_to: '',
        movement_type: '',
        location: '',
    });

    // Location options
    const locations = [
        { value: '', label: 'All Locations' },
        { value: 'receiving_area', label: 'Receiving Area' },
        { value: 'processing_area', label: 'Processing Area' },
        { value: 'packed_warehouse', label: 'Packed Warehouse' },
        { value: 'delivery_vehicles', label: 'Delivery Vehicles' },
        { value: 'quality_hold', label: 'Quality Hold' },
    ];

    // Generate report
    const handleGenerateReport = async () => {
        setLoading(true);
        try {
            let response;

            if (reportType === 'current_stock') {
                response = await inventoryAPI.generateCurrentStockReport(stockFilters);
            } else if (reportType === 'movements') {
                response = await inventoryAPI.generateMovementReport(movementFilters);
            } else if (reportType === 'batch_age') {
                response = await inventoryAPI.generateBatchAgeReport();
            }

            setReportData(response);
            enqueueSnackbar('Report generated successfully', { variant: 'success' });
        } catch (error: any) {
            console.error('Failed to generate report:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to generate report', {
                variant: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    // Export to CSV
    const handleExportCSV = () => {
        if (!reportData) {
            enqueueSnackbar('Please generate a report first', { variant: 'warning' });
            return;
        }

        try {
            let csvContent = '';
            let filename = '';

            if (reportType === 'current_stock') {
                filename = 'current_stock_report.csv';
                csvContent = 'Item,Location,Grade,Status,Quantity,Batches,Earliest Expiry\n';
                reportData.report.forEach((row: any) => {
                    csvContent += `"${row.item_name}","${row.location}","${row.grade || ''}","${row.status}",${row.total_quantity},${row.batch_count},"${row.earliest_expiry || ''}"\n`;
                });
            } else if (reportType === 'movements') {
                filename = 'movements_report.csv';
                csvContent = 'Date,Type,Item,Batch,Quantity,From,To,Notes\n';
                reportData.movements.forEach((row: any) => {
                    csvContent += `"${row.created_at}","${row.movement_type}","${row.item_name}","${row.batch_number}",${row.quantity},"${row.from_location || ''}","${row.to_location || ''}","${row.notes || ''}"\n`;
                });
            } else if (reportType === 'batch_age') {
                filename = 'batch_age_report.csv';
                csvContent = 'Batch,Item,Location,Quantity,Entry Date,Age (Days),Status\n';
                reportData.batches.forEach((row: any) => {
                    csvContent += `"${row.batch_number}","${row.item_name}","${row.location}",${row.quantity},"${row.entry_date}",${row.age_days},"${row.status}"\n`;
                });
            }

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            enqueueSnackbar('Report exported successfully', { variant: 'success' });
        } catch (error) {
            console.error('Failed to export report:', error);
            enqueueSnackbar('Failed to export report', { variant: 'error' });
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" gutterBottom>
                    Inventory Reports
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Generate and export inventory reports
                </Typography>
            </Box>

            {/* Report Selection */}
            <Card sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Select Report Type
                </Typography>

                <FormControl fullWidth sx={{ mb: 3 }}>
                    <InputLabel>Report Type</InputLabel>
                    <Select
                        value={reportType}
                        label="Report Type"
                        onChange={(e) => {
                            setReportType(e.target.value as ReportType);
                            setReportData(null);
                        }}
                    >
                        <MenuItem value="current_stock">Current Stock Report</MenuItem>
                        <MenuItem value="movements">Stock Movement Report</MenuItem>
                        <MenuItem value="batch_age">Batch Age Report</MenuItem>
                    </Select>
                </FormControl>

                {/* Current Stock Filters */}
                {reportType === 'current_stock' && (
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                        <FormControl sx={{ minWidth: 200 }}>
                            <InputLabel>Location</InputLabel>
                            <Select
                                value={stockFilters.location}
                                label="Location"
                                onChange={(e) => setStockFilters({ ...stockFilters, location: e.target.value })}
                            >
                                {locations.map(loc => (
                                    <MenuItem key={loc.value} value={loc.value}>{loc.label}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>

                        <FormControl sx={{ minWidth: 180 }}>
                            <InputLabel>Status</InputLabel>
                            <Select
                                value={stockFilters.status}
                                label="Status"
                                onChange={(e) => setStockFilters({ ...stockFilters, status: e.target.value })}
                            >
                                <MenuItem value="">All Statuses</MenuItem>
                                <MenuItem value="available">Available</MenuItem>
                                <MenuItem value="allocated">Allocated</MenuItem>
                                <MenuItem value="hold">Hold</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                )}

                {/* Movement Filters */}
                {reportType === 'movements' && (
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                        <TextField
                            label="From Date"
                            type="date"
                            value={movementFilters.date_from}
                            onChange={(e) => setMovementFilters({ ...movementFilters, date_from: e.target.value })}
                            InputLabelProps={{ shrink: true }}
                            sx={{ minWidth: 180 }}
                        />

                        <TextField
                            label="To Date"
                            type="date"
                            value={movementFilters.date_to}
                            onChange={(e) => setMovementFilters({ ...movementFilters, date_to: e.target.value })}
                            InputLabelProps={{ shrink: true }}
                            sx={{ minWidth: 180 }}
                        />

                        <FormControl sx={{ minWidth: 200 }}>
                            <InputLabel>Movement Type</InputLabel>
                            <Select
                                value={movementFilters.movement_type}
                                label="Movement Type"
                                onChange={(e) => setMovementFilters({ ...movementFilters, movement_type: e.target.value })}
                            >
                                <MenuItem value="">All Types</MenuItem>
                                <MenuItem value="stock_in">Stock In</MenuItem>
                                <MenuItem value="stock_out">Stock Out</MenuItem>
                                <MenuItem value="location_transfer">Location Transfer</MenuItem>
                                <MenuItem value="adjustment">Adjustment</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                )}

                {/* Batch Age - No filters needed */}
                {reportType === 'batch_age' && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                        This report shows all batches currently in inventory sorted by age (oldest first)
                    </Alert>
                )}

                {/* Generate Button */}
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                        variant="contained"
                        startIcon={loading ? <CircularProgress size={20} /> : <ReportIcon />}
                        onClick={handleGenerateReport}
                        disabled={loading}
                    >
                        {loading ? 'Generating...' : 'Generate Report'}
                    </Button>

                    {reportData && (
                        <Button
                            variant="outlined"
                            startIcon={<DownloadIcon />}
                            onClick={handleExportCSV}
                        >
                            Export CSV
                        </Button>
                    )}
                </Box>
            </Card>

            {/* Report Data */}
            {reportData && (
                <Card>
                    <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
                        <Typography variant="h6">
                            Report Results ({reportData.report?.length || reportData.movements?.length || reportData.batches?.length || 0} rows)
                        </Typography>
                    </Box>
                    <Box sx={{ maxHeight: 600, overflow: 'auto' }}>
                        <Table size="small" stickyHeader>
                            <TableHead>
                                <TableRow>
                                    {reportType === 'current_stock' && (
                                        <>
                                            <TableCell>Item</TableCell>
                                            <TableCell>Location</TableCell>
                                            <TableCell>Grade</TableCell>
                                            <TableCell>Status</TableCell>
                                            <TableCell align="right">Quantity</TableCell>
                                            <TableCell align="right">Batches</TableCell>
                                            <TableCell>Earliest Expiry</TableCell>
                                        </>
                                    )}
                                    {reportType === 'movements' && (
                                        <>
                                            <TableCell>Date</TableCell>
                                            <TableCell>Type</TableCell>
                                            <TableCell>Item</TableCell>
                                            <TableCell>Batch</TableCell>
                                            <TableCell align="right">Quantity</TableCell>
                                            <TableCell>From</TableCell>
                                            <TableCell>To</TableCell>
                                            <TableCell>Notes</TableCell>
                                        </>
                                    )}
                                    {reportType === 'batch_age' && (
                                        <>
                                            <TableCell>Batch</TableCell>
                                            <TableCell>Item</TableCell>
                                            <TableCell>Location</TableCell>
                                            <TableCell align="right">Quantity</TableCell>
                                            <TableCell>Entry Date</TableCell>
                                            <TableCell align="right">Age (Days)</TableCell>
                                            <TableCell>Status</TableCell>
                                        </>
                                    )}
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {reportType === 'current_stock' && reportData.report?.map((row: any, index: number) => (
                                    <TableRow key={index}>
                                        <TableCell>{row.item_name}</TableCell>
                                        <TableCell>{row.location}</TableCell>
                                        <TableCell>{row.grade || '-'}</TableCell>
                                        <TableCell>{row.status}</TableCell>
                                        <TableCell align="right">{row.total_quantity.toFixed(2)}</TableCell>
                                        <TableCell align="right">{row.batch_count}</TableCell>
                                        <TableCell>{row.earliest_expiry ? formatDateForDisplay(row.earliest_expiry) : '-'}</TableCell>
                                    </TableRow>
                                ))}
                                {reportType === 'movements' && reportData.movements?.map((row: any, index: number) => (
                                    <TableRow key={index}>
                                        <TableCell>{formatDateForDisplay(row.created_at)}</TableCell>
                                        <TableCell>{row.movement_type}</TableCell>
                                        <TableCell>{row.item_name}</TableCell>
                                        <TableCell>{row.batch_number}</TableCell>
                                        <TableCell align="right">{row.quantity.toFixed(2)}</TableCell>
                                        <TableCell>{row.from_location || '-'}</TableCell>
                                        <TableCell>{row.to_location || '-'}</TableCell>
                                        <TableCell>{row.notes || '-'}</TableCell>
                                    </TableRow>
                                ))}
                                {reportType === 'batch_age' && reportData.batches?.map((row: any, index: number) => (
                                    <TableRow key={index}>
                                        <TableCell>{row.batch_number}</TableCell>
                                        <TableCell>{row.item_name}</TableCell>
                                        <TableCell>{row.location}</TableCell>
                                        <TableCell align="right">{row.quantity.toFixed(2)}</TableCell>
                                        <TableCell>{formatDateForDisplay(row.entry_date)}</TableCell>
                                        <TableCell align="right">{row.age_days}</TableCell>
                                        <TableCell>{row.status}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </Box>
                </Card>
            )}
        </Box>
    );
};

export default ReportsPage;

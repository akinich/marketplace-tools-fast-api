import React, { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Tabs,
    Tab,
    Typography,
    CircularProgress,
    Alert
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';
import AllocationGrid from './components/AllocationGrid';
import StatisticsDashboard from './components/StatisticsDashboard';
import InvoiceStatusList from './components/InvoiceStatusList';
import { allocationApi } from '../../../api';

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

function TabPanel(props: TabPanelProps) {
    const { children, value, index, ...other } = props;
    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`allocation-tabpanel-${index}`}
            aria-labelledby={`allocation-tab-${index}`}
            {...other}
        >
            {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
        </div>
    );
}

export default function OrderAllocation() {
    const [selectedDate, setSelectedDate] = useState<Dayjs | null>(dayjs());
    const [activeTab, setActiveTab] = useState(0);
    const [sheetData, setSheetData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load sheet data when date changes
    useEffect(() => {
        if (selectedDate) {
            loadSheetData(selectedDate.format('YYYY-MM-DD'));
        }
    }, [selectedDate]);

    const loadSheetData = async (date: string) => {
        setLoading(true);
        setError(null);
        try {
            const data = await allocationApi.getSheet(date);
            setSheetData(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load allocation sheet');
            setSheetData(null);
        } finally {
            setLoading(false);
        }
    };

    const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
        setActiveTab(newValue);
    };

    const handleDateChange = (newDate: Dayjs | null) => {
        setSelectedDate(newDate);
    };

    const handleRefresh = () => {
        if (selectedDate) {
            loadSheetData(selectedDate.format('YYYY-MM-DD'));
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h4" component="h1">
                    Order Allocation
                </Typography>

                {/* Date Picker */}
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                    <DatePicker
                        label="Delivery Date"
                        value={selectedDate}
                        onChange={handleDateChange}
                        format="DD/MM/YYYY"
                        slotProps={{
                            textField: {
                                size: 'small',
                                sx: { width: 200 }
                            }
                        }}
                    />
                </LocalizationProvider>
            </Box>

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* Loading State */}
            {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
                    <CircularProgress />
                </Box>
            )}

            {/* Main Content */}
            {!loading && sheetData && (
                <Paper sx={{ width: '100%' }}>
                    {/* Tabs */}
                    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                        <Tabs value={activeTab} onChange={handleTabChange} aria-label="allocation tabs">
                            <Tab label="Allocation Grid" id="allocation-tab-0" />
                            <Tab label="Statistics" id="allocation-tab-1" />
                            <Tab label="Invoice Status" id="allocation-tab-2" />
                        </Tabs>
                    </Box>

                    {/* Tab Panels */}
                    <TabPanel value={activeTab} index={0}>
                        <AllocationGrid
                            sheetData={sheetData}
                            onRefresh={handleRefresh}
                        />
                    </TabPanel>

                    <TabPanel value={activeTab} index={1}>
                        <StatisticsDashboard sheetId={sheetData.sheet_id} />
                    </TabPanel>

                    <TabPanel value={activeTab} index={2}>
                        <InvoiceStatusList sheetId={sheetData.sheet_id} onRefresh={handleRefresh} />
                    </TabPanel>
                </Paper>
            )}

            {/* Empty State */}
            {!loading && !sheetData && !error && selectedDate && (
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                    <Typography variant="h6" color="text.secondary">
                        No sales orders found for {selectedDate.format('MMMM D, YYYY')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        Create a sales order with this delivery date to start allocating stock.
                    </Typography>
                </Paper>
            )}
        </Box>
    );
}

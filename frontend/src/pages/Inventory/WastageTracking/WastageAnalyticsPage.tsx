/**
 * ================================================================================
 * Wastage Analytics Page
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Detailed analytics and reports with multiple views and export functionality.
 * ================================================================================
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    Paper,
    Tabs,
    Tab,
    Button,
    TextField,
    MenuItem,
    Grid,
} from '@mui/material';
import {
    ArrowBack as BackIcon,
    Download as DownloadIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import { wastageTrackingAPI } from '../../../api/wastageTracking';
import WastageChart from './components/WastageChart';
import { format, subDays } from 'date-fns';

export default function WastageAnalyticsPage() {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const [loading, setLoading] = useState(false);
    const [currentTab, setCurrentTab] = useState(0);
    const [dateRange, setDateRange] = useState('30');
    const [granularity, setGranularity] = useState<'daily' | 'weekly' | 'monthly'>('daily');

    const [farmData, setFarmData] = useState<any[]>([]);
    const [stageData, setStageData] = useState<any[]>([]);
    const [productData, setProductData] = useState<any[]>([]);
    const [trendData, setTrendData] = useState<any[]>([]);

    useEffect(() => {
        loadAnalytics();
    }, [dateRange, granularity]);

    const loadAnalytics = async () => {
        setLoading(true);
        try {
            const dateFrom = format(subDays(new Date(), parseInt(dateRange)), 'yyyy-MM-dd');
            const dateTo = format(new Date(), 'yyyy-MM-dd');

            const [farms, stages, products, trends] = await Promise.all([
                wastageTrackingAPI.getAnalyticsByFarm({ date_from: dateFrom, date_to: dateTo }),
                wastageTrackingAPI.getAnalyticsByStage({ date_from: dateFrom, date_to: dateTo }),
                wastageTrackingAPI.getAnalyticsByProduct({ date_from: dateFrom, date_to: dateTo }),
                wastageTrackingAPI.getTrends({ date_from: dateFrom, date_to: dateTo, granularity }),
            ]);

            setFarmData(farms.farms);
            setStageData(stages.stages);
            setProductData(products.products);
            setTrendData(trends.data_points);
        } catch (error: any) {
            enqueueSnackbar(
                error.response?.data?.detail || 'Failed to load analytics',
                { variant: 'error' }
            );
        } finally {
            setLoading(false);
        }
    };

    const handleExport = () => {
        enqueueSnackbar('Export functionality coming soon', { variant: 'info' });
    };

    const farmColumns: GridColDef[] = [
        { field: 'farm_name', headerName: 'Farm', width: 200 },
        { field: 'total_wastage_kg', headerName: 'Wastage (kg)', width: 150 },
        { field: 'total_cost', headerName: 'Cost (₹)', width: 150 },
        { field: 'wastage_percentage', headerName: 'Percentage', width: 120, valueFormatter: (params) => `${params.value}%` },
    ];

    const stageColumns: GridColDef[] = [
        { field: 'stage_name', headerName: 'Stage', width: 150 },
        { field: 'total_wastage_kg', headerName: 'Wastage (kg)', width: 150 },
        { field: 'total_cost', headerName: 'Cost (₹)', width: 150 },
        { field: 'event_count', headerName: 'Events', width: 100 },
        { field: 'percentage_of_total', headerName: '%', width: 100, valueFormatter: (params) => `${params.value}%` },
    ];

    const productColumns: GridColDef[] = [
        { field: 'item_name', headerName: 'Product', width: 200 },
        { field: 'total_wastage_kg', headerName: 'Wastage (kg)', width: 150 },
        { field: 'total_cost', headerName: 'Cost (₹)', width: 150 },
        { field: 'wastage_percentage', headerName: 'Percentage', width: 120, valueFormatter: (params) => `${params.value}%` },
    ];

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                    <Button
                        startIcon={<BackIcon />}
                        onClick={() => navigate('/inventory/wastage-tracking')}
                        sx={{ mb: 1 }}
                    >
                        Back to Dashboard
                    </Button>
                    <Typography variant="h4" fontWeight="bold">
                        📊 Wastage Analytics & Reports
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                        select
                        label="Date Range"
                        value={dateRange}
                        onChange={(e) => setDateRange(e.target.value)}
                        size="small"
                        sx={{ width: 150 }}
                    >
                        <MenuItem value="7">Last 7 days</MenuItem>
                        <MenuItem value="30">Last 30 days</MenuItem>
                        <MenuItem value="90">Last 90 days</MenuItem>
                    </TextField>
                    <Button
                        variant="outlined"
                        startIcon={<DownloadIcon />}
                        onClick={handleExport}
                    >
                        Export CSV
                    </Button>
                </Box>
            </Box>

            {/* Tabs */}
            <Paper sx={{ mb: 3 }}>
                <Tabs value={currentTab} onChange={(_, v) => setCurrentTab(v)}>
                    <Tab label="By Farm" />
                    <Tab label="By Stage" />
                    <Tab label="By Product" />
                    <Tab label="Trends" />
                </Tabs>
            </Paper>

            {/* Tab Content */}
            {currentTab === 0 && (
                <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                        <WastageChart
                            type="bar"
                            data={farmData.map((f) => ({ name: f.farm_name, value: f.total_wastage_kg }))}
                            title="Wastage by Farm"
                            xKey="name"
                            yKey="value"
                            height={350}
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Paper sx={{ p: 2, height: 400 }}>
                            <DataGrid
                                rows={farmData}
                                columns={farmColumns}
                                loading={loading}
                                getRowId={(row) => row.farm_name}
                            />
                        </Paper>
                    </Grid>
                </Grid>
            )}

            {currentTab === 1 && (
                <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                        <WastageChart
                            type="pie"
                            data={stageData.map((s) => ({ name: s.stage_name, value: s.total_wastage_kg }))}
                            title="Wastage by Stage"
                            nameKey="name"
                            yKey="value"
                            height={350}
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Paper sx={{ p: 2, height: 400 }}>
                            <DataGrid
                                rows={stageData}
                                columns={stageColumns}
                                loading={loading}
                                getRowId={(row) => row.stage}
                            />
                        </Paper>
                    </Grid>
                </Grid>
            )}

            {currentTab === 2 && (
                <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                        <WastageChart
                            type="bar"
                            data={productData.map((p) => ({ name: p.item_name, value: p.total_wastage_kg }))}
                            title="Wastage by Product"
                            xKey="name"
                            yKey="value"
                            height={350}
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Paper sx={{ p: 2, height: 400 }}>
                            <DataGrid
                                rows={productData}
                                columns={productColumns}
                                loading={loading}
                                getRowId={(row) => row.item_name}
                            />
                        </Paper>
                    </Grid>
                </Grid>
            )}

            {currentTab === 3 && (
                <Box>
                    <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
                        <TextField
                            select
                            label="Granularity"
                            value={granularity}
                            onChange={(e) => setGranularity(e.target.value as any)}
                            size="small"
                            sx={{ width: 150 }}
                        >
                            <MenuItem value="daily">Daily</MenuItem>
                            <MenuItem value="weekly">Weekly</MenuItem>
                            <MenuItem value="monthly">Monthly</MenuItem>
                        </TextField>
                    </Box>
                    <WastageChart
                        type="line"
                        data={trendData.map((d) => ({
                            name: format(new Date(d.date), granularity === 'daily' ? 'MMM dd' : 'MMM yyyy'),
                            value: d.total_wastage_kg,
                        }))}
                        title="Wastage Trend Over Time"
                        xKey="name"
                        yKey="value"
                        height={400}
                    />
                </Box>
            )}
        </Box>
    );
}

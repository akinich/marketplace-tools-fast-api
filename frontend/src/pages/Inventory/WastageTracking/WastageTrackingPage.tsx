/**
 * ================================================================================
 * Wastage Tracking Dashboard Page
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Main dashboard for wastage tracking with summary cards, charts, and recent events.
 * ================================================================================
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    Button,
    Paper,
    Grid,
    Card,
    CardContent,
    MenuItem,
    TextField,
    Chip,
} from '@mui/material';
import {
    Add as AddIcon,
    TrendingUp as TrendingUpIcon,
    Warning as WarningIcon,
    AttachMoney as MoneyIcon,
    Fullscreen as FullscreenIcon,
    FullscreenExit as FullscreenExitIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, useGridApiRef } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import { wastageTrackingAPI } from '../../../api/wastageTracking';
import WastageChart from './components/WastageChart';
import WastageLogModal from './components/WastageLogModal';
import { format, subDays } from 'date-fns';

export default function WastageTrackingPage() {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const gridRef = useGridApiRef();
    const [loading, setLoading] = useState(false);
    const [logModalOpen, setLogModalOpen] = useState(false);
    const [dateRange, setDateRange] = useState('30'); // days
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Summary data
    const [summary, setSummary] = useState({
        totalWastage: 0,
        totalCost: 0,
        activeAlerts: 0,
    });

    // Charts data
    const [stageData, setStageData] = useState<any[]>([]);
    const [trendData, setTrendData] = useState<any[]>([]);

    // Recent events
    const [recentEvents, setRecentEvents] = useState<any[]>([]);

    useEffect(() => {
        loadDashboardData();
    }, [dateRange]);

    const loadDashboardData = async () => {
        setLoading(true);
        try {
            const dateFrom = format(subDays(new Date(), parseInt(dateRange)), 'yyyy-MM-dd');
            const dateTo = format(new Date(), 'yyyy-MM-dd');

            // Load analytics by stage
            const stageAnalytics = await wastageTrackingAPI.getAnalyticsByStage({
                date_from: dateFrom,
                date_to: dateTo,
            });

            // Load trends
            const trends = await wastageTrackingAPI.getTrends({
                date_from: dateFrom,
                date_to: dateTo,
                granularity: 'daily',
            });

            // Load alerts
            const alerts = await wastageTrackingAPI.getAlerts();

            // Process stage data for chart
            const chartData = stageAnalytics.stages.map((s) => ({
                name: s.stage_name,
                value: s.total_wastage_kg,
                cost: s.total_cost,
            }));
            setStageData(chartData);

            // Process trend data
            const trendChartData = trends.data_points.map((d) => ({
                name: format(new Date(d.date), 'MMM dd'),
                value: d.total_wastage_kg,
                cost: d.total_cost,
            }));
            setTrendData(trendChartData);

            // Calculate summary
            const totalWastage = stageAnalytics.stages.reduce((sum, s) => sum + s.total_wastage_kg, 0);
            const totalCost = stageAnalytics.stages.reduce((sum, s) => sum + s.total_cost, 0);
            setSummary({
                totalWastage,
                totalCost,
                activeAlerts: alerts.alerts.length,
            });

            // Mock recent events (in real app, would have separate endpoint)
            setRecentEvents([]);
        } catch (error: any) {
            enqueueSnackbar(
                error.response?.data?.detail || 'Failed to load dashboard data',
                { variant: 'error' }
            );
        } finally {
            setLoading(false);
        }
    };

    const columns: GridColDef[] = [
        {
            field: 'batch_number',
            headerName: 'Batch',
            width: 150,
        },
        {
            field: 'stage',
            headerName: 'Stage',
            width: 120,
        },
        {
            field: 'wastage_type',
            headerName: 'Type',
            width: 120,
        },
        {
            field: 'quantity',
            headerName: 'Quantity',
            width: 100,
            valueFormatter: (params) => `${params.value} kg`,
        },
        {
            field: 'cost_allocation',
            headerName: 'Cost',
            width: 100,
            renderCell: (params) => (
                <Chip
                    label={params.value.toUpperCase()}
                    color={params.value === 'farm' ? 'error' : 'primary'}
                    size="small"
                />
            ),
        },
        {
            field: 'created_at',
            headerName: 'Date',
            width: 150,
            valueFormatter: (params) => format(new Date(params.value), 'MMM dd, yyyy'),
        },
    ];

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                    <Typography variant="h4" gutterBottom fontWeight="bold">
                        🗑️ Wastage Tracking & Analytics
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Monitor and analyze wastage across the supply chain
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
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => setLogModalOpen(true)}
                    >
                        Log Wastage
                    </Button>
                </Box>
            </Box>

            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={4}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <Box>
                                    <Typography variant="body2" color="text.secondary">
                                        Total Wastage
                                    </Typography>
                                    <Typography variant="h4" fontWeight="bold">
                                        {summary.totalWastage.toFixed(2)} kg
                                    </Typography>
                                </Box>
                                <TrendingUpIcon sx={{ fontSize: 48, color: 'warning.main' }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={4}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <Box>
                                    <Typography variant="body2" color="text.secondary">
                                        Total Cost Impact
                                    </Typography>
                                    <Typography variant="h4" fontWeight="bold">
                                        ₹{summary.totalCost.toFixed(2)}
                                    </Typography>
                                </Box>
                                <MoneyIcon sx={{ fontSize: 48, color: 'error.main' }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={4}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <Box>
                                    <Typography variant="body2" color="text.secondary">
                                        Active Alerts
                                    </Typography>
                                    <Typography variant="h4" fontWeight="bold">
                                        {summary.activeAlerts}
                                    </Typography>
                                </Box>
                                <WarningIcon sx={{ fontSize: 48, color: 'warning.main' }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Charts */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                    <WastageChart
                        type="pie"
                        data={stageData}
                        title="Wastage by Stage"
                        nameKey="name"
                        yKey="value"
                        height={300}
                    />
                </Grid>
                <Grid item xs={12} md={6}>
                    <WastageChart
                        type="line"
                        data={trendData}
                        title="Wastage Trend"
                        xKey="name"
                        yKey="value"
                        height={300}
                    />
                </Grid>
            </Grid>

            {/* Recent Events */}
            <Paper sx={{ p: 3 }}>
                <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6">Recent Wastage Events</Typography>
                    <Button
                        variant="outlined"
                        size="small"
                        onClick={() => navigate('/inventory/wastage-tracking/analytics')}
                    >
                        View Analytics
                    </Button>
                </Box>
                <Box sx={{
                    height: isFullscreen ? '100vh' : 400,
                    width: '100%',
                    ...(isFullscreen && {
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
                        apiRef={gridRef}
                        rows={recentEvents}
                        columns={columns}
                        loading={loading}
                        getRowId={(row) => row.event_id || Math.random()}
                        pageSizeOptions={[10, 25, 50]}
                        initialState={{
                            pagination: { paginationModel: { pageSize: 10 } },
                        }}
                        slots={{
                            toolbar: () => (
                                <Box sx={{ p: 1, display: 'flex', gap: 1, alignItems: 'center', borderBottom: '1px solid #e0e0e0' }}>
                                    <Box sx={{ flexGrow: 1 }} />
                                    <Button
                                        startIcon={isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                                        onClick={() => setIsFullscreen(!isFullscreen)}
                                        size="small"
                                    >
                                        {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
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
            </Paper>

            {/* Log Wastage Modal */}
            <WastageLogModal
                open={logModalOpen}
                onClose={() => setLogModalOpen(false)}
                onSuccess={() => {
                    loadDashboardData();
                    setLogModalOpen(false);
                }}
            />
        </Box>
    );
}

/**
 * ================================================================================
 * Wastage Alerts Page
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Alert management and threshold configuration (Admin only).
 * ================================================================================
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    Paper,
    Button,
    Alert,
    AlertTitle,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    MenuItem,
} from '@mui/material';
import {
    ArrowBack as BackIcon,
    Warning as WarningIcon,
    Settings as SettingsIcon,
    Fullscreen as FullscreenIcon,
    FullscreenExit as FullscreenExitIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridActionsCellItem, useGridApiRef } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import { wastageTrackingAPI, WastageAlert, WastageThreshold, AlertLevel } from '../../../api/wastageTracking';
import useAuthStore from '../../../store/authStore';

export default function WastageAlertsPage() {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const { user } = useAuthStore();
    const gridRef = useGridApiRef();
    const [loading, setLoading] = useState(false);
    const [alerts, setAlerts] = useState<WastageAlert[]>([]);
    const [thresholds, setThresholds] = useState<WastageThreshold[]>([]);
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [selectedThreshold, setSelectedThreshold] = useState<WastageThreshold | null>(null);
    const [isFullscreen, setIsFullscreen] = useState(false);

    const isAdmin = user?.role === 'admin';

    useEffect(() => {
        loadAlerts();
        if (isAdmin) {
            loadThresholds();
        }
    }, [isAdmin]);

    const loadAlerts = async () => {
        setLoading(true);
        try {
            const response = await wastageTrackingAPI.getAlerts();
            setAlerts(response.alerts);
        } catch (error: any) {
            enqueueSnackbar(
                error.response?.data?.detail || 'Failed to load alerts',
                { variant: 'error' }
            );
        } finally {
            setLoading(false);
        }
    };

    const loadThresholds = async () => {
        try {
            const response = await wastageTrackingAPI.getThresholds();
            setThresholds(response.thresholds);
        } catch (error: any) {
            console.error('Failed to load thresholds:', error);
        }
    };

    const handleEditThreshold = (threshold: WastageThreshold) => {
        setSelectedThreshold(threshold);
        setEditModalOpen(true);
    };

    const handleSaveThreshold = async () => {
        if (!selectedThreshold) return;

        try {
            await wastageTrackingAPI.updateThreshold(selectedThreshold.id, {
                threshold_percentage: selectedThreshold.threshold_percentage,
                alert_level: selectedThreshold.alert_level,
                is_active: selectedThreshold.is_active,
            });

            enqueueSnackbar('Threshold updated successfully', { variant: 'success' });
            setEditModalOpen(false);
            loadThresholds();
        } catch (error: any) {
            enqueueSnackbar(
                error.response?.data?.detail || 'Failed to update threshold',
                { variant: 'error' }
            );
        }
    };

    const getAlertSeverity = (level: string): 'error' | 'warning' | 'info' => {
        switch (level) {
            case 'critical':
                return 'error';
            case 'warning':
                return 'warning';
            default:
                return 'info';
        }
    };

    const thresholdColumns: GridColDef[] = [
        { field: 'scope_type', headerName: 'Scope', width: 120 },
        { field: 'stage', headerName: 'Stage', width: 150 },
        { field: 'threshold_percentage', headerName: 'Threshold %', width: 130 },
        { field: 'alert_level', headerName: 'Alert Level', width: 120 },
        {
            field: 'is_active',
            headerName: 'Status',
            width: 100,
            valueFormatter: (params) => params.value ? 'Active' : 'Inactive',
        },
        {
            field: 'actions',
            type: 'actions',
            headerName: 'Actions',
            width: 100,
            getActions: (params) => [
                <GridActionsCellItem
                    icon={<SettingsIcon />}
                    label="Edit"
                    onClick={() => handleEditThreshold(params.row)}
                />,
            ],
        },
    ];

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Button
                    startIcon={<BackIcon />}
                    onClick={() => navigate('/inventory/wastage-tracking')}
                    sx={{ mb: 1 }}
                >
                    Back to Dashboard
                </Button>
                <Typography variant="h4" fontWeight="bold">
                    ⚠️ Wastage Alerts & Thresholds
                </Typography>
            </Box>

            {/* Current Alerts */}
            <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Current Alerts ({alerts.length})
                </Typography>
                {alerts.length === 0 ? (
                    <Alert severity="success">
                        <AlertTitle>No Active Alerts</AlertTitle>
                        All wastage levels are within acceptable thresholds.
                    </Alert>
                ) : (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {alerts.map((alert, index) => (
                            <Alert
                                key={index}
                                severity={getAlertSeverity(alert.alert_level)}
                                icon={<WarningIcon />}
                            >
                                <AlertTitle>{alert.message}</AlertTitle>
                                <Typography variant="body2">
                                    {alert.farm && `Farm: ${alert.farm} • `}
                                    {alert.stage && `Stage: ${alert.stage} • `}
                                    Current: {alert.current_percentage}% • Threshold: {alert.threshold}% • Period: {alert.period}
                                </Typography>
                            </Alert>
                        ))}
                    </Box>
                )}
            </Paper>

            {/* Threshold Configuration (Admin Only) */}
            {isAdmin && (
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Threshold Configuration
                    </Typography>
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
                            rows={thresholds}
                            columns={thresholdColumns}
                            loading={loading}
                            getRowId={(row) => row.id}
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
            )}

            {!isAdmin && (
                <Alert severity="info">
                    <AlertTitle>Admin Access Required</AlertTitle>
                    Threshold configuration is only available to administrators.
                </Alert>
            )}

            {/* Edit Threshold Modal */}
            <Dialog open={editModalOpen} onClose={() => setEditModalOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Edit Threshold</DialogTitle>
                <DialogContent>
                    {selectedThreshold && (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                            <TextField
                                label="Threshold Percentage"
                                type="number"
                                value={selectedThreshold.threshold_percentage}
                                onChange={(e) =>
                                    setSelectedThreshold({
                                        ...selectedThreshold,
                                        threshold_percentage: parseFloat(e.target.value),
                                    })
                                }
                                inputProps={{ min: 0, max: 100, step: 0.1 }}
                                fullWidth
                            />
                            <TextField
                                select
                                label="Alert Level"
                                value={selectedThreshold.alert_level}
                                onChange={(e) =>
                                    setSelectedThreshold({
                                        ...selectedThreshold,
                                        alert_level: e.target.value,
                                    })
                                }
                                fullWidth
                            >
                                <MenuItem value={AlertLevel.INFO}>Info</MenuItem>
                                <MenuItem value={AlertLevel.WARNING}>Warning</MenuItem>
                                <MenuItem value={AlertLevel.CRITICAL}>Critical</MenuItem>
                            </TextField>
                            <TextField
                                select
                                label="Status"
                                value={selectedThreshold.is_active ? 'active' : 'inactive'}
                                onChange={(e) =>
                                    setSelectedThreshold({
                                        ...selectedThreshold,
                                        is_active: e.target.value === 'active',
                                    })
                                }
                                fullWidth
                            >
                                <MenuItem value="active">Active</MenuItem>
                                <MenuItem value="inactive">Inactive</MenuItem>
                            </TextField>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setEditModalOpen(false)}>Cancel</Button>
                    <Button onClick={handleSaveThreshold} variant="contained">
                        Save Changes
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}

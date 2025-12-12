/**
 * Batch Inventory Page
 * Version: 1.0.0
 * Created: 2024-12-12
 *
 * Complete inventory breakdown for a specific batch
 */

import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    Typography,
    Chip,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Alert,
    CircularProgress,
    Button,
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { ArrowBack as BackIcon } from '@mui/icons-material';
import { inventoryAPI, BatchInventoryResponse } from '../../../api/inventory';
import { formatDateForDisplay } from '../../../utils/dateUtils';

const BatchInventoryPage: React.FC = () => {
    const { batchId } = useParams<{ batchId: string }>();
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();

    const [batch, setBatch] = useState<BatchInventoryResponse | null>(null);
    const [loading, setLoading] = useState(true);

    // Load batch inventory
    useEffect(() => {
        const loadBatch = async () => {
            if (!batchId) return;

            setLoading(true);
            try {
                const response = await inventoryAPI.getBatchInventory(parseInt(batchId));
                setBatch(response);
            } catch (error: any) {
                console.error('Failed to load batch:', error);
                enqueueSnackbar(error.response?.data?.detail || 'Failed to load batch inventory', {
                    variant: 'error',
                });
            } finally {
                setLoading(false);
            }
        };

        loadBatch();
    }, [batchId, enqueueSnackbar]);

    // Format location
    const formatLocation = (location: string): string => {
        return location.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
                <CircularProgress />
            </Box>
        );
    }

    if (!batch) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">Batch not found</Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Button
                    startIcon={<BackIcon />}
                    onClick={() => navigate('/inventory/stock')}
                >
                    Back to Inventory
                </Button>
                <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h4">
                        Batch {batch.batch_number}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        {batch.item_name}
                    </Typography>
                </Box>
            </Box>

            {/* Summary Card */}
            <Card sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Inventory Summary
                </Typography>
                <Box sx={{ display: 'flex', gap: 4, mt: 2 }}>
                    <Box>
                        <Typography variant="caption" color="text.secondary">
                            Total Quantity
                        </Typography>
                        <Typography variant="h4">
                            {batch.total_quantity.toFixed(2)}
                        </Typography>
                    </Box>
                    <Box>
                        <Typography variant="caption" color="text.secondary">
                            Locations
                        </Typography>
                        <Typography variant="h4">
                            {batch.locations.length}
                        </Typography>
                    </Box>
                </Box>
            </Card>

            {/* Location Breakdown */}
            <Card sx={{ mb: 3 }}>
                <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
                    <Typography variant="h6">Location Breakdown</Typography>
                </Box>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Location</TableCell>
                            <TableCell>Quantity</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Grade</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {batch.locations.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} align="center">
                                    <Typography color="text.secondary">No inventory at any location</Typography>
                                </TableCell>
                            </TableRow>
                        ) : (
                            batch.locations.map((loc, index) => (
                                <TableRow key={index}>
                                    <TableCell>
                                        <Chip label={formatLocation(loc.location)} size="small" />
                                    </TableCell>
                                    <TableCell>{loc.quantity.toFixed(2)}</TableCell>
                                    <TableCell>
                                        <Chip
                                            label={loc.status.replace(/_/g, ' ').toUpperCase()}
                                            color={loc.status === 'available' ? 'success' : 'default'}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>
                                        {loc.grade ? (
                                            <Chip label={`Grade ${loc.grade}`} size="small" variant="outlined" />
                                        ) : (
                                            '-'
                                        )}
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </Card>

            {/* Movement History */}
            <Card>
                <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
                    <Typography variant="h6">Movement History</Typography>
                </Box>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Date/Time</TableCell>
                            <TableCell>Type</TableCell>
                            <TableCell>Quantity</TableCell>
                            <TableCell>From</TableCell>
                            <TableCell>To</TableCell>
                            <TableCell>Notes</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {batch.movements.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} align="center">
                                    <Typography color="text.secondary">No movements recorded</Typography>
                                </TableCell>
                            </TableRow>
                        ) : (
                            batch.movements.map((movement) => (
                                <TableRow key={movement.id}>
                                    <TableCell>
                                        {formatDateForDisplay(movement.created_at)}
                                    </TableCell>
                                    <TableCell>
                                        <Chip
                                            label={movement.movement_type.replace(/_/g, ' ').toUpperCase()}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>{movement.quantity.toFixed(2)}</TableCell>
                                    <TableCell>
                                        {movement.from_location ? formatLocation(movement.from_location) : '-'}
                                    </TableCell>
                                    <TableCell>
                                        {movement.to_location ? formatLocation(movement.to_location) : '-'}
                                    </TableCell>
                                    <TableCell>{movement.notes || '-'}</TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </Card>
        </Box>
    );
};

export default BatchInventoryPage;

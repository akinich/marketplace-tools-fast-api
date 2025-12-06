/**
 * Batch Detail Page
 * Version: 1.0.0
 * Created: 2024-12-04
 *
 * Description:
 *   Detailed view of a single batch with complete information
 *   - Batch header with status and dates
 *   - Parent/child batch links (if repacked)
 *   - Document links (PO, GRN, SO)
 *   - Timeline component
 *   - Repack and Archive actions
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    Button,
    Paper,
    Grid,
    Chip,
    Divider,
    CircularProgress,
    Alert,
    Card,
    CardContent,
} from '@mui/material';
import {
    ArrowBack as BackIcon,
    Recycling as RepackIcon,
    Archive as ArchiveIcon,
    Description as DocumentIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { batchTrackingAPI, BatchDetailResponse, BatchTimelineResponse } from '../../api/batchTracking';
import BatchTimeline from './BatchTimeline';
import RepackingModal from './RepackingModal';
import useAuthStore from '../../store/authStore';

export default function BatchDetailPage() {
    const { batchNumber: encodedBatchNumber } = useParams<{ batchNumber: string }>();
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const { user } = useAuthStore();

    // Decode the batch number from URL (it comes encoded from the route)
    const batchNumber = encodedBatchNumber ? decodeURIComponent(encodedBatchNumber) : undefined;

    const [batch, setBatch] = useState<BatchDetailResponse | null>(null);
    const [timeline, setTimeline] = useState<BatchTimelineResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [repackModalOpen, setRepackModalOpen] = useState(false);
    const [archiving, setArchiving] = useState(false);

    // Fetch batch details
    const fetchBatchDetails = async () => {
        if (!batchNumber) return;

        setLoading(true);
        try {
            const [batchData, timelineData] = await Promise.all([
                batchTrackingAPI.getBatchDetails(batchNumber),
                batchTrackingAPI.getBatchTimeline(batchNumber),
            ]);

            setBatch(batchData);
            setTimeline(timelineData);
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to fetch batch details', { variant: 'error' });
            navigate('/inventory/batch-tracking');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBatchDetails();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [batchNumber]);

    // Handle archive
    const handleArchive = async () => {
        if (!batchNumber || !user || user.role !== 'admin') return;

        if (!window.confirm(`Are you sure you want to archive batch ${batchNumber}?`)) {
            return;
        }

        setArchiving(true);
        try {
            await batchTrackingAPI.archiveBatch(batchNumber);
            enqueueSnackbar(`Batch ${batchNumber} archived successfully`, { variant: 'success' });
            fetchBatchDetails(); // Refresh
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to archive batch', { variant: 'error' });
        } finally {
            setArchiving(false);
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
                <CircularProgress />
            </Box>
        );
    }

    if (!batch || !timeline) {
        return (
            <Alert severity="error">Batch not found</Alert>
        );
    }

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Button
                    startIcon={<BackIcon />}
                    onClick={() => navigate('/inventory/batch-tracking')}
                    sx={{ mb: 2 }}
                >
                    Back to Batch List
                </Button>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box>
                        <Typography variant="h4" gutterBottom fontWeight="bold">
                            Batch {batch.batch_number}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            <Chip
                                label={batch.status.replace('_', ' ').toUpperCase()}
                                color={batch.status === 'archived' ? 'default' : 'primary'}
                            />
                            {batch.is_repacked && (
                                <Chip label="REPACKED" color="warning" variant="outlined" />
                            )}
                        </Box>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 2 }}>
                        {!batch.is_repacked && batch.status !== 'archived' && (
                            <Button
                                variant="outlined"
                                startIcon={<RepackIcon />}
                                onClick={() => setRepackModalOpen(true)}
                            >
                                Repack
                            </Button>
                        )}
                        {user?.role === 'admin' && batch.status !== 'archived' && (
                            <Button
                                variant="outlined"
                                color="error"
                                startIcon={archiving ? <CircularProgress size={20} /> : <ArchiveIcon />}
                                onClick={handleArchive}
                                disabled={archiving}
                            >
                                Archive
                            </Button>
                        )}
                    </Box>
                </Box>
            </Box>

            <Grid container spacing={3}>
                {/* Batch Information */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Batch Information
                        </Typography>
                        <Divider sx={{ mb: 2 }} />

                        <Grid container spacing={2}>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Batch Number
                                </Typography>
                                <Typography variant="body1" fontWeight="bold">
                                    {batch.batch_number}
                                </Typography>
                            </Grid>

                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Status
                                </Typography>
                                <Typography variant="body1">
                                    {batch.status.replace('_', ' ').toUpperCase()}
                                </Typography>
                            </Grid>

                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Created At
                                </Typography>
                                <Typography variant="body1">
                                    {new Date(batch.created_at).toLocaleString()}
                                </Typography>
                            </Grid>

                            {batch.archived_at && (
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">
                                        Archived At
                                    </Typography>
                                    <Typography variant="body1">
                                        {new Date(batch.archived_at).toLocaleString()}
                                    </Typography>
                                </Grid>
                            )}

                            {batch.parent_batch_number && (
                                <Grid item xs={12}>
                                    <Typography variant="body2" color="text.secondary">
                                        Parent Batch
                                    </Typography>
                                    <Button
                                        variant="text"
                                        onClick={() => navigate(`/inventory/batch-tracking/${batch.parent_batch_number}`)}
                                    >
                                        {batch.parent_batch_number}
                                    </Button>
                                </Grid>
                            )}

                            {batch.child_batch_number && (
                                <Grid item xs={12}>
                                    <Typography variant="body2" color="text.secondary">
                                        Child Batch (Repacked)
                                    </Typography>
                                    <Button
                                        variant="text"
                                        onClick={() => navigate(`/inventory/batch-tracking/${batch.child_batch_number}`)}
                                    >
                                        {batch.child_batch_number}
                                    </Button>
                                </Grid>
                            )}
                        </Grid>
                    </Paper>
                </Grid>

                {/* Linked Documents */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Linked Documents
                        </Typography>
                        <Divider sx={{ mb: 2 }} />

                        {batch.documents.length === 0 ? (
                            <Typography variant="body2" color="text.secondary">
                                No documents linked yet
                            </Typography>
                        ) : (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                {batch.documents.map((doc, index) => (
                                    <Card key={index} variant="outlined">
                                        <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <DocumentIcon color="action" />
                                                <Box>
                                                    <Typography variant="body2" fontWeight="bold">
                                                        {doc.document_type.toUpperCase()}
                                                    </Typography>
                                                    {doc.document_number && (
                                                        <Typography variant="caption" color="text.secondary">
                                                            {doc.document_number}
                                                        </Typography>
                                                    )}
                                                </Box>
                                            </Box>
                                        </CardContent>
                                    </Card>
                                ))}
                            </Box>
                        )}
                    </Paper>
                </Grid>

                {/* Timeline */}
                <Grid item xs={12}>
                    <BatchTimeline timeline={timeline} />
                </Grid>
            </Grid>

            {/* Repack Modal */}
            <RepackingModal
                open={repackModalOpen}
                onClose={() => setRepackModalOpen(false)}
                batchNumber={batch.batch_number}
                onSuccess={fetchBatchDetails}
            />
        </Box>
    );
}

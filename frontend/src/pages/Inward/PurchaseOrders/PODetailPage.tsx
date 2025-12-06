/**
 * Purchase Order Detail Page
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Complete view of a single purchase order with history
 */

import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Card,
    Chip,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    IconButton,
    CircularProgress,
    Grid,
    Divider,
    List,
    ListItem,
} from '@mui/material';
import {
    ArrowBack,
    Send as SendIcon,
    PictureAsPdf as PdfIcon,
    Circle as CircleIcon,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { purchaseOrdersAPI, PODetailResponse } from '../../../api/purchaseOrders';
import { grnAPI, GRNResponse } from '../../../api/grn';
import { formatDateForDisplay } from '../../../utils/dateUtils';
import GRNGenerationModal from '../GRN/GRNGenerationModal';

const PODetailPage: React.FC = () => {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const { poId } = useParams<{ poId: string }>();

    const [po, setPO] = useState<PODetailResponse | null>(null);
    const [grns, setGRNs] = useState<GRNResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [showGenerateModal, setShowGenerateModal] = useState(false);

    // Load PO details
    useEffect(() => {
        const loadPO = async () => {
            if (!poId) return;

            setLoading(true);
            try {
                const [poData, grnResponse] = await Promise.all([
                    purchaseOrdersAPI.getById(parseInt(poId)),
                    grnAPI.getByPO(parseInt(poId)).catch(() => ({ data: [] })) // Handle case where GRN API fails or returns 404 if no GRNs
                ]);
                setPO(poData);
                setGRNs(grnResponse.data || []);
            } catch (error: any) {
                console.error('Failed to load PO:', error);
                enqueueSnackbar(error.response?.data?.detail || 'Failed to load PO details', {
                    variant: 'error',
                });
            } finally {
                setLoading(false);
            }
        };

        loadPO();
    }, [poId, enqueueSnackbar]);

    // Status color mapping
    const getStatusColor = (status: string): 'default' | 'info' | 'warning' | 'success' | 'secondary' => {
        const colors: Record<string, 'default' | 'info' | 'warning' | 'success' | 'secondary'> = {
            draft: 'default',
            sent_to_farm: 'info',
            grn_generated: 'warning',
            completed: 'success',
            exported_to_zoho: 'secondary',
            closed: 'default',
        };
        return colors[status] || 'default';
    };

    // Price source color mapping
    const getPriceSourceColor = (source: string): 'success' | 'info' | 'warning' => {
        const colors: Record<string, 'success' | 'info' | 'warning'> = {
            vendor: 'success',
            zoho: 'info',
            manual: 'warning',
        };
        return colors[source] || 'warning';
    };

    // Format status for display
    const formatStatus = (status: string): string => {
        return status.replace(/_/g, ' ').toUpperCase();
    };

    // Handle send to farm
    const handleSendToFarm = async () => {
        if (!po) return;

        try {
            await purchaseOrdersAPI.send(po.id);
            enqueueSnackbar('PO sent to farm successfully', { variant: 'success' });
            // Reload PO
            const updated = await purchaseOrdersAPI.getById(po.id);
            setPO(updated);
        } catch (error: any) {
            console.error('Failed to send PO:', error);
            enqueueSnackbar(error.response?.data?.detail || 'Failed to send PO', { variant: 'error' });
        }
    };

    // Handle PDF download
    const handleDownloadPDF = async () => {
        if (!po) return;

        try {
            const blob = await purchaseOrdersAPI.generatePDF(po.id);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${po.po_number}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            enqueueSnackbar('PDF downloaded successfully', { variant: 'success' });
        } catch (error: any) {
            console.error('Failed to download PDF:', error);
            enqueueSnackbar('Failed to download PDF', { variant: 'error' });
        }
    };

    const handleGRNGenerated = async (newGRN: GRNResponse) => {
        setGRNs([...grns, newGRN]);
        // Reload PO to update status if it changed
        if (po) {
            const updated = await purchaseOrdersAPI.getById(po.id);
            setPO(updated);
        }
        enqueueSnackbar('GRN Generated Successfully', { variant: 'success' });
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
                <CircularProgress />
            </Box>
        );
    }

    if (!po) {
        return (
            <Box sx={{ p: 3 }}>
                <Typography variant="h6">Purchase order not found</Typography>
            </Box>
        );
    }

    const canSend = po.status === 'draft';

    return (
        <>
            <Box sx={{ p: 3 }}>
                {/* Header */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <IconButton onClick={() => navigate('/inward/purchase-orders')}>
                            <ArrowBack />
                        </IconButton>
                        <Typography variant="h4" component="h1">
                            {po.po_number}
                        </Typography>
                        <Chip label={formatStatus(po.status)} color={getStatusColor(po.status)} />
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1 }}>
                        {canSend && (
                            <Button variant="contained" startIcon={<SendIcon />} onClick={handleSendToFarm}>
                                Send to Farm
                            </Button>
                        )}
                        <Button variant="outlined" startIcon={<PdfIcon />} onClick={handleDownloadPDF}>
                            Download PDF
                        </Button>

                        {/* GRN Actions */}
                        {po.status === 'sent_to_farm' && (
                            <Button
                                variant="contained"
                                color="warning"
                                onClick={() => setShowGenerateModal(true)}
                            >
                                Generate GRN
                            </Button>
                        )}

                        {grns.length > 0 && (
                            <Button
                                variant="outlined"
                                color="info"
                                onClick={() => navigate(`/inward/grn/${grns[0].id}`)}
                            >
                                View GRN ({grns.length})
                            </Button>
                        )}
                    </Box>
                </Box>

                <Grid container spacing={3}>
                    {/* PO Details */}
                    <Grid item xs={12} md={8}>
                        <Card sx={{ p: 3, mb: 3 }}>
                            <Typography variant="h6" gutterBottom>
                                Purchase Order Details
                            </Typography>
                            <Divider sx={{ mb: 2 }} />

                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">
                                        Vendor
                                    </Typography>
                                    <Typography variant="body1" fontWeight={500}>
                                        {po.vendor_name}
                                    </Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">
                                        Total Amount
                                    </Typography>
                                    <Typography variant="h6" color="primary">
                                        ₹{Number(po.total_amount).toFixed(2)}
                                    </Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">
                                        Dispatch Date
                                    </Typography>
                                    <Typography variant="body1">{formatDateForDisplay(po.dispatch_date)}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">
                                        Delivery Date
                                    </Typography>
                                    <Typography variant="body1">{formatDateForDisplay(po.delivery_date)}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">
                                        Created At
                                    </Typography>
                                    <Typography variant="body1">
                                        {new Date(po.created_at).toLocaleString()}
                                    </Typography>
                                </Grid>
                                {po.exported_at && (
                                    <Grid item xs={6}>
                                        <Typography variant="body2" color="text.secondary">
                                            Exported At
                                        </Typography>
                                        <Typography variant="body1">
                                            {new Date(po.exported_at).toLocaleString()}
                                        </Typography>
                                    </Grid>
                                )}
                                {po.notes && (
                                    <Grid item xs={12}>
                                        <Typography variant="body2" color="text.secondary">
                                            Notes
                                        </Typography>
                                        <Typography variant="body1">{po.notes}</Typography>
                                    </Grid>
                                )}
                            </Grid>
                        </Card>

                        {/* Items Table */}
                        <Card sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom>
                                Items
                            </Typography>
                            <Divider sx={{ mb: 2 }} />

                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Item</TableCell>
                                        <TableCell>Quantity</TableCell>
                                        <TableCell>Unit Price</TableCell>
                                        <TableCell>Source</TableCell>
                                        <TableCell>Total</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {po.items.map((item) => (
                                        <TableRow key={item.id}>
                                            <TableCell>
                                                <Box>
                                                    <Typography variant="body2">{item.item_name}</Typography>
                                                    {item.added_from_grn && (
                                                        <Chip label="Added from GRN" size="small" color="warning" sx={{ mt: 0.5 }} />
                                                    )}
                                                </Box>
                                            </TableCell>
                                            <TableCell>{Number(item.quantity).toFixed(2)}</TableCell>
                                            <TableCell>₹{Number(item.unit_price).toFixed(2)}</TableCell>
                                            <TableCell>
                                                <Chip
                                                    label={item.price_source.toUpperCase()}
                                                    color={getPriceSourceColor(item.price_source)}
                                                    size="small"
                                                />
                                            </TableCell>
                                            <TableCell>₹{Number(item.total_price).toFixed(2)}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </Card>
                    </Grid>

                    {/* Status History */}
                    <Grid item xs={12} md={4}>
                        <Card sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom>
                                Status History
                            </Typography>
                            <Divider sx={{ mb: 2 }} />

                            <List>
                                {po.status_history.map((change, index) => (
                                    <ListItem
                                        key={index}
                                        sx={{
                                            flexDirection: 'column',
                                            alignItems: 'flex-start',
                                            borderLeft: '2px solid',
                                            borderColor: `${getStatusColor(change.to_status)}.main`,
                                            pl: 2,
                                            mb: 1,
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                            <CircleIcon
                                                sx={{
                                                    fontSize: 12,
                                                    color: `${getStatusColor(change.to_status)}.main`,
                                                }}
                                            />
                                            <Typography variant="body2" fontWeight={500}>
                                                {formatStatus(change.to_status)}
                                            </Typography>
                                        </Box>
                                        <Typography variant="caption" color="text.secondary">
                                            {new Date(change.changed_at).toLocaleString()}
                                        </Typography>
                                        {change.changed_by && (
                                            <Typography variant="caption" color="text.secondary">
                                                by {change.changed_by}
                                            </Typography>
                                        )}
                                        {change.notes && (
                                            <Typography variant="caption" color="text.secondary">
                                                {change.notes}
                                            </Typography>
                                        )}
                                    </ListItem>
                                ))}
                            </List>
                        </Card>
                    </Grid>
                </Grid>
            </Box>

            {po && (
                <GRNGenerationModal
                    open={showGenerateModal}
                    onClose={() => setShowGenerateModal(false)}
                    poId={po.id}
                    poNumber={po.po_number}
                    onSuccess={handleGRNGenerated}
                />
            )}
        </>
    );
};

export default PODetailPage;

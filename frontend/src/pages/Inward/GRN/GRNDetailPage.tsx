import React, { useState, useEffect } from 'react';
import {
    Box, Button, Card, Grid, Typography, Chip, Table, TableBody, TableCell, TableHead, TableRow
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { grnAPI, GRNDetailResponse } from '../../../api/grn';
import { CircularProgress } from '@mui/material';

const GRNDetailPage: React.FC = () => {
    const { grnId } = useParams<{ grnId: string }>();
    const navigate = useNavigate();
    const [grn, setGRN] = useState<GRNDetailResponse | null>(null);
    const [loading, setLoading] = useState(true);

    const loadGRN = async () => {
        if (!grnId) return;
        try {
            setLoading(true);
            const response = await grnAPI.getById(parseInt(grnId));
            setGRN(response.data);
        } catch (error) {
            console.error('Failed to load GRN:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadGRN();
    }, [grnId]);

    const handlePrintBlank = async () => {
        if (!grn) return;
        try {
            const response = await grnAPI.generateBlankPDF(grn.id);
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            window.open(url);
        } catch (error) {
            console.error('Failed to generate PDF:', error);
            alert('Failed to generate PDF');
        }
    };

    if (loading || !grn) {
        return <Box sx={{ p: 5, textAlign: 'center' }}><CircularProgress /></Box>;
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'draft': return 'warning';
            case 'completed': return 'success';
            default: return 'default';
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Box>
                    <Typography variant="h4">GRN {grn.grn_number}</Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        <Chip label={grn.status.toUpperCase()} color={getStatusColor(grn.status) as any} />
                        <Chip label={`Batch: ${grn.batch_number}`} variant="outlined" />
                        <Chip label={`PO: ${grn.po_number}`} variant="outlined" />
                    </Box>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button variant="outlined" onClick={() => navigate('/inward/grn')}>Back to List</Button>
                    {grn.status === 'draft' && (
                        <Button variant="contained" onClick={() => navigate(`/inward/grn/${grn.id}/edit`)}>Edit / Enter Data</Button>
                    )}
                    <Button variant="outlined" onClick={handlePrintBlank}>Print Blank</Button>
                </Box>
            </Box>

            <Grid container spacing={3}>
                {/* Main Info */}
                <Grid item xs={12} md={8}>
                    <Card sx={{ p: 3, mb: 3 }}>
                        <Typography variant="h6" gutterBottom>items</Typography>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Item</TableCell>
                                    <TableCell align="right">Expected</TableCell>
                                    <TableCell align="right">Gross</TableCell>
                                    <TableCell align="right">Damage</TableCell>
                                    <TableCell align="right">Reject</TableCell>
                                    <TableCell align="right">Accepted</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {grn.items.map(item => (
                                    <TableRow key={item.id}>
                                        <TableCell>{item.item_name}</TableCell>
                                        <TableCell align="right">{item.expected_quantity}</TableCell>
                                        <TableCell align="right">{item.gross_received}</TableCell>
                                        <TableCell align="right">{item.damage}</TableCell>
                                        <TableCell align="right">{item.reject}</TableCell>
                                        <TableCell align="right">{item.final_accepted}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </Card>

                    {/* Photos */}
                    <Card sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>Photos</Typography>
                        {grn.photos.length === 0 ? (
                            <Typography color="textSecondary">No photos uploaded</Typography>
                        ) : (
                            <Grid container spacing={2}>
                                {grn.photos.map(photo => (
                                    <Grid item xs={6} sm={4} md={3} key={photo.id}>
                                        <Box sx={{ border: '1px solid #ddd', borderRadius: 1, overflow: 'hidden' }}>
                                            <img
                                                src={photo.photo_url}
                                                alt={photo.photo_type}
                                                style={{ width: '100%', height: 150, objectFit: 'cover' }}
                                            />
                                            <Box sx={{ p: 1 }}>
                                                <Typography variant="caption" display="block" fontWeight="bold">{photo.item_name}</Typography>
                                                <Chip
                                                    label={photo.photo_type}
                                                    size="small"
                                                    color={photo.photo_type === 'damage' ? 'error' : 'secondary'}
                                                    sx={{ mt: 0.5 }}
                                                />
                                            </Box>
                                        </Box>
                                    </Grid>
                                ))}
                            </Grid>
                        )}
                    </Card>
                </Grid>

                {/* Sidebar */}
                <Grid item xs={12} md={4}>
                    <Card sx={{ p: 3, mb: 3 }}>
                        <Typography variant="h6" gutterBottom>Info</Typography>
                        <Box sx={{ display: 'grid', gap: 2 }}>
                            <Box>
                                <Typography variant="caption" color="textSecondary">Vendor</Typography>
                                <Typography>{grn.vendor_name}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" color="textSecondary">Receiving Date</Typography>
                                <Typography>{grn.receiving_date}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" color="textSecondary">Time</Typography>
                                <Typography>{grn.receiving_time || 'N/A'}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" color="textSecondary">Transport</Typography>
                                <Typography>{grn.transport_method || 'N/A'}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" color="textSecondary">Boxes</Typography>
                                <Typography>{grn.number_of_boxes || 0}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" color="textSecondary">Receiver</Typography>
                                <Typography>{grn.receiver_name || 'N/A'}</Typography>
                            </Box>
                        </Box>
                    </Card>

                    {/* Edit History */}
                    {grn.edit_history && grn.edit_history.length > 0 && (
                        <Card sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom>History</Typography>
                            <Box sx={{ maxHeight: 300, overflowY: 'auto' }}>
                                {grn.edit_history.map((edit, index) => (
                                    <Box key={index} sx={{ mb: 2, borderLeft: '2px solid #eee', pl: 2 }}>
                                        <Typography variant="subtitle2">{edit.field_name}</Typography>
                                        <Typography variant="caption" color="textSecondary" display="block">
                                            {new Date(edit.edited_at).toLocaleString()} by {edit.edited_by_name}
                                        </Typography>
                                        <Typography variant="body2">
                                            {edit.old_value ? `${edit.old_value} -> ` : ''} {edit.new_value}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                        </Card>
                    )}
                </Grid>
            </Grid>
        </Box>
    );
};

export default GRNDetailPage;

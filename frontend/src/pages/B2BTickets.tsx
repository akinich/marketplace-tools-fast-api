/**
 * B2B Tickets Management Page
 * Full ticket list and creation for B2B customer issues
 */

import React, { useState, useEffect } from 'react';
import {
    Box,
    Container,
    Typography,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    MenuItem,
    CircularProgress,
    Alert,
} from '@mui/material';
import { Add as AddIcon, Business as B2BIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { ticketsAPI } from '../api';

interface Ticket {
    id: number;
    title: string;
    ticket_type: string;
    status: string;
    priority: string | null;
    customer_name: string | null;
    batch_number: string | null;
    created_at: string;
}

const ticketTypes = [
    { value: 'quality_issue', label: 'Quality Issue' },
    { value: 'delivery_issue', label: 'Delivery Issue' },
    { value: 'order_issue', label: 'Order Issue' },
    { value: 'return_request', label: 'Return Request' },
    { value: 'general', label: 'General' },
];

const statusColors: Record<string, 'default' | 'info' | 'warning' | 'success' | 'error'> = {
    open: 'info',
    in_progress: 'warning',
    resolved: 'success',
    closed: 'default',
};

export default function B2BTickets() {
    const { enqueueSnackbar } = useSnackbar();
    const [tickets, setTickets] = useState<Ticket[]>([]);
    const [loading, setLoading] = useState(true);
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        ticket_type: 'quality_issue',
        customer_name: '',
        sales_order_id: '',
        batch_number: '',
    });

    useEffect(() => {
        fetchTickets();
    }, []);

    const fetchTickets = async () => {
        try {
            const data = await ticketsAPI.getTickets({ ticket_category: 'b2b' });
            setTickets(data.tickets || []);
        } catch (error) {
            console.error('Failed to fetch B2B tickets:', error);
            enqueueSnackbar('Failed to load B2B tickets', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const handleCreateTicket = async () => {
        try {
            await ticketsAPI.createTicket({
                ...formData,
                ticket_category: 'b2b',
                sales_order_id: formData.sales_order_id ? parseInt(formData.sales_order_id) : null,
            });

            enqueueSnackbar('B2B ticket created successfully', { variant: 'success' });
            setCreateDialogOpen(false);
            setFormData({
                title: '',
                description: '',
                ticket_type: 'quality_issue',
                customer_name: '',
                sales_order_id: '',
                batch_number: '',
            });
            fetchTickets();
        } catch (error) {
            console.error('Failed to create B2B ticket:', error);
            enqueueSnackbar('Failed to create B2B ticket', { variant: 'error' });
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Container maxWidth="xl">
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <B2BIcon sx={{ fontSize: 40, mr: 2, color: '#2e7d32' }} />
                    <Box>
                        <Typography variant="h4" gutterBottom>
                            B2B Tickets
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Customer issues for hotels and restaurants
                        </Typography>
                    </Box>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setCreateDialogOpen(true)}
                >
                    Create B2B Ticket
                </Button>
            </Box>

            {tickets.length === 0 ? (
                <Alert severity="info">
                    No B2B tickets found. Click "Create B2B Ticket" to create your first one.
                </Alert>
            ) : (
                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>ID</TableCell>
                                <TableCell>Title</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Customer</TableCell>
                                <TableCell>Batch</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Priority</TableCell>
                                <TableCell>Created</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {tickets.map((ticket) => (
                                <TableRow
                                    key={ticket.id}
                                    hover
                                >
                                    <TableCell>#{ticket.id}</TableCell>
                                    <TableCell>{ticket.title}</TableCell>
                                    <TableCell>
                                        {ticketTypes.find(t => t.value === ticket.ticket_type)?.label || ticket.ticket_type}
                                    </TableCell>
                                    <TableCell>{ticket.customer_name || '-'}</TableCell>
                                    <TableCell>{ticket.batch_number || '-'}</TableCell>
                                    <TableCell>
                                        <Chip
                                            label={ticket.status.replace('_', ' ')}
                                            color={statusColors[ticket.status]}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>
                                        {ticket.priority ? (
                                            <Chip label={ticket.priority} size="small" />
                                        ) : (
                                            '-'
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        {new Date(ticket.created_at).toLocaleDateString()}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            {/* Create Ticket Dialog */}
            <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Create B2B Ticket</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                        <TextField
                            label="Title"
                            value={formData.title}
                            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            required
                            fullWidth
                        />
                        <TextField
                            label="Description"
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            required
                            multiline
                            rows={4}
                            fullWidth
                        />
                        <TextField
                            label="Ticket Type"
                            value={formData.ticket_type}
                            onChange={(e) => setFormData({ ...formData, ticket_type: e.target.value })}
                            select
                            required
                            fullWidth
                        >
                            {ticketTypes.map((type) => (
                                <MenuItem key={type.value} value={type.value}>
                                    {type.label}
                                </MenuItem>
                            ))}
                        </TextField>
                        <TextField
                            label="Customer Name"
                            value={formData.customer_name}
                            onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                            fullWidth
                        />
                        <TextField
                            label="Sales Order ID (optional)"
                            value={formData.sales_order_id}
                            onChange={(e) => setFormData({ ...formData, sales_order_id: e.target.value })}
                            type="number"
                            fullWidth
                        />
                        <TextField
                            label="Batch Number (optional)"
                            value={formData.batch_number}
                            onChange={(e) => setFormData({ ...formData, batch_number: e.target.value })}
                            fullWidth
                            helperText="For quality issues, specify the batch number"
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
                    <Button
                        onClick={handleCreateTicket}
                        variant="contained"
                        disabled={!formData.title || !formData.description}
                    >
                        Create Ticket
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
}

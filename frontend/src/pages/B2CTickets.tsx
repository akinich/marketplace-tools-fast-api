/**
 * B2C Tickets Management Page
 * Full ticket list and creation for B2C customer issues
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Add as AddIcon, Home as B2CIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';

interface Ticket {
    id: number;
    title: string;
    ticket_type: string;
    status: string;
    priority: string | null;
    customer_name: string | null;
    customer_email: string | null;
    woocommerce_order_id: string | null;
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

export default function B2CTickets() {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const [tickets, setTickets] = useState<Ticket[]>([]);
    const [loading, setLoading] = useState(true);
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        ticket_type: 'quality_issue',
        customer_name: '',
        customer_email: '',
        customer_phone: '',
        woocommerce_order_id: '',
        delivery_date: '',
    });

    useEffect(() => {
        fetchTickets();
    }, []);

    const fetchTickets = async () => {
        try {
            const response = await fetch('/api/tickets?ticket_category=b2c', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });
            const data = await response.json();
            setTickets(data.tickets || []);
        } catch (error) {
            console.error('Failed to fetch B2C tickets:', error);
            enqueueSnackbar('Failed to load B2C tickets', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const handleCreateTicket = async () => {
        try {
            const response = await fetch('/api/tickets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify({
                    ...formData,
                    ticket_category: 'b2c',
                }),
            });

            if (response.ok) {
                enqueueSnackbar('B2C ticket created successfully', { variant: 'success' });
                setCreateDialogOpen(false);
                setFormData({
                    title: '',
                    description: '',
                    ticket_type: 'quality_issue',
                    customer_name: '',
                    customer_email: '',
                    customer_phone: '',
                    woocommerce_order_id: '',
                    delivery_date: '',
                });
                fetchTickets();
            } else {
                throw new Error('Failed to create ticket');
            }
        } catch (error) {
            console.error('Failed to create B2C ticket:', error);
            enqueueSnackbar('Failed to create B2C ticket', { variant: 'error' });
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
                    <B2CIcon sx={{ fontSize: 40, mr: 2, color: '#ed6c02' }} />
                    <Box>
                        <Typography variant="h4" gutterBottom>
                            B2C Tickets
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Customer issues for direct-to-home customers
                        </Typography>
                    </Box>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setCreateDialogOpen(true)}
                >
                    Create B2C Ticket
                </Button>
            </Box>

            {tickets.length === 0 ? (
                <Alert severity="info">
                    No B2C tickets found. Click "Create B2C Ticket" to create your first one.
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
                                <TableCell>Email</TableCell>
                                <TableCell>WooCommerce Order</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Created</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {tickets.map((ticket) => (
                                <TableRow
                                    key={ticket.id}
                                    hover
                                    sx={{ cursor: 'pointer' }}
                                    onClick={() => navigate(`/tickets/${ticket.id}`)}
                                >
                                    <TableCell>#{ticket.id}</TableCell>
                                    <TableCell>{ticket.title}</TableCell>
                                    <TableCell>
                                        {ticketTypes.find(t => t.value === ticket.ticket_type)?.label || ticket.ticket_type}
                                    </TableCell>
                                    <TableCell>{ticket.customer_name || '-'}</TableCell>
                                    <TableCell>{ticket.customer_email || '-'}</TableCell>
                                    <TableCell>{ticket.woocommerce_order_id || '-'}</TableCell>
                                    <TableCell>
                                        <Chip
                                            label={ticket.status.replace('_', ' ')}
                                            color={statusColors[ticket.status]}
                                            size="small"
                                        />
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
                <DialogTitle>Create B2C Ticket</DialogTitle>
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
                            required
                            fullWidth
                        />
                        <TextField
                            label="Customer Email"
                            value={formData.customer_email}
                            onChange={(e) => setFormData({ ...formData, customer_email: e.target.value })}
                            type="email"
                            fullWidth
                        />
                        <TextField
                            label="Customer Phone"
                            value={formData.customer_phone}
                            onChange={(e) => setFormData({ ...formData, customer_phone: e.target.value })}
                            fullWidth
                        />
                        <TextField
                            label="WooCommerce Order ID"
                            value={formData.woocommerce_order_id}
                            onChange={(e) => setFormData({ ...formData, woocommerce_order_id: e.target.value })}
                            fullWidth
                            helperText="Enter the WooCommerce order number"
                        />
                        <TextField
                            label="Delivery Date"
                            value={formData.delivery_date}
                            onChange={(e) => setFormData({ ...formData, delivery_date: e.target.value })}
                            type="date"
                            fullWidth
                            InputLabelProps={{ shrink: true }}
                            helperText="When was the order delivered?"
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
                    <Button
                        onClick={handleCreateTicket}
                        variant="contained"
                        disabled={!formData.title || !formData.description || !formData.customer_name}
                    >
                        Create Ticket
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
}

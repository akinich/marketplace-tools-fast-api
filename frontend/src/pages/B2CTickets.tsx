/**
 * B2C Tickets Management Page
 * Full ticket list and creation for B2C customer issues
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
    Grid,
    Card,
    CardContent,
} from '@mui/material';
import { Add as AddIcon, Home as B2CIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { ticketsAPI } from '../api';

interface Ticket {
    id: number;
    title: string;
    description: string;
    ticket_type: string;
    status: string;
    priority: string | null;
    customer_name: string | null;
    customer_email: string | null;
    customer_phone: string | null;
    woocommerce_order_id: string | null;
    delivery_date: string | null;
    created_at: string;
    updated_at: string;
}

interface TicketStats {
    total: number;
    open: number;
    in_progress: number;
    resolved: number;
    closed: number;
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
    const { enqueueSnackbar } = useSnackbar();
    const [tickets, setTickets] = useState<Ticket[]>([]);
    const [stats, setStats] = useState<TicketStats>({ total: 0, open: 0, in_progress: 0, resolved: 0, closed: 0 });
    const [loading, setLoading] = useState(true);
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [viewDialogOpen, setViewDialogOpen] = useState(false);
    const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
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

    const calculateStats = (ticketList: Ticket[]): TicketStats => {
        return {
            total: ticketList.length,
            open: ticketList.filter(t => t.status === 'open').length,
            in_progress: ticketList.filter(t => t.status === 'in_progress').length,
            resolved: ticketList.filter(t => t.status === 'resolved').length,
            closed: ticketList.filter(t => t.status === 'closed').length,
        };
    };

    const fetchTickets = async () => {
        try {
            const data = await ticketsAPI.getTickets({ ticket_category: 'b2c' });
            const ticketList = data.tickets || [];
            setTickets(ticketList);
            setStats(calculateStats(ticketList));
        } catch (error) {
            console.error('Failed to fetch B2C tickets:', error);
            enqueueSnackbar('Failed to load B2C tickets', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const handleViewTicket = (ticket: Ticket) => {
        setSelectedTicket(ticket);
        setViewDialogOpen(true);
    };

    const handleCreateTicket = async () => {
        try {
            await ticketsAPI.createTicket({
                ...formData,
                ticket_category: 'b2c',
            });

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

            {/* Stats Cards */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={2.4}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom variant="body2">
                                TOTAL
                            </Typography>
                            <Typography variant="h4">
                                {stats.total}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={2.4}>
                    <Card sx={{ bgcolor: '#e3f2fd' }}>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom variant="body2">
                                OPEN
                            </Typography>
                            <Typography variant="h4" color="primary">
                                {stats.open}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={2.4}>
                    <Card sx={{ bgcolor: '#fff3e0' }}>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom variant="body2">
                                IN PROGRESS
                            </Typography>
                            <Typography variant="h4" color="warning.main">
                                {stats.in_progress}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={2.4}>
                    <Card sx={{ bgcolor: '#e8f5e9' }}>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom variant="body2">
                                RESOLVED
                            </Typography>
                            <Typography variant="h4" color="success.main">
                                {stats.resolved}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={2.4}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom variant="body2">
                                CLOSED
                            </Typography>
                            <Typography variant="h4">
                                {stats.closed}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

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
                                    onClick={() => handleViewTicket(ticket)}
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
                                            color={statusColors[ticket.status] || 'default'}
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
                            label="WooCommerce Order ID *"
                            value={formData.woocommerce_order_id}
                            onChange={(e) => setFormData({ ...formData, woocommerce_order_id: e.target.value })}
                            required
                            fullWidth
                            helperText="Enter the WooCommerce order number"
                        />
                        <TextField
                            label="Delivery Date"
                            value={formData.delivery_date}
                            onChange={(e) => setFormData({ ...formData, delivery_date: e.target.value })}
                            type="date"
                            fullWidth
                            onClick={(e) => {
                                const input = e.currentTarget.querySelector('input');
                                if (input && typeof (input as any).showPicker === 'function') {
                                    (input as any).showPicker();
                                }
                            }}
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
                        disabled={!formData.title || !formData.description || !formData.customer_name || !formData.woocommerce_order_id}
                    >
                        Create Ticket
                    </Button>
                </DialogActions>
            </Dialog>

            {/* View Ticket Dialog */}
            <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>B2C Ticket Details</DialogTitle>
                <DialogContent>
                    {selectedTicket && (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">Ticket ID</Typography>
                                <Typography variant="body1">#{selectedTicket.id}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">Title</Typography>
                                <Typography variant="body1">{selectedTicket.title}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">Description</Typography>
                                <Typography variant="body1">{selectedTicket.description}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', gap: 2 }}>
                                <Box sx={{ flex: 1 }}>
                                    <Typography variant="subtitle2" color="text.secondary">Type</Typography>
                                    <Typography variant="body1">
                                        {ticketTypes.find(t => t.value === selectedTicket.ticket_type)?.label || selectedTicket.ticket_type}
                                    </Typography>
                                </Box>
                                <Box sx={{ flex: 1 }}>
                                    <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                                    <Chip label={selectedTicket.status.replace('_', ' ')} color={statusColors[selectedTicket.status] || 'default'} size="small" />
                                </Box>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">Customer Name</Typography>
                                <Typography variant="body1">{selectedTicket.customer_name || '-'}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', gap: 2 }}>
                                <Box sx={{ flex: 1 }}>
                                    <Typography variant="subtitle2" color="text.secondary">Customer Email</Typography>
                                    <Typography variant="body1">{selectedTicket.customer_email || '-'}</Typography>
                                </Box>
                                <Box sx={{ flex: 1 }}>
                                    <Typography variant="subtitle2" color="text.secondary">Customer Phone</Typography>
                                    <Typography variant="body1">{selectedTicket.customer_phone || '-'}</Typography>
                                </Box>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">WooCommerce Order ID</Typography>
                                <Typography variant="body1">{selectedTicket.woocommerce_order_id || '-'}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">Delivery Date</Typography>
                                <Typography variant="body1">{selectedTicket.delivery_date || '-'}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', gap: 2 }}>
                                <Box sx={{ flex: 1 }}>
                                    <Typography variant="subtitle2" color="text.secondary">Created At</Typography>
                                    <Typography variant="body1">{new Date(selectedTicket.created_at).toLocaleString()}</Typography>
                                </Box>
                                <Box sx={{ flex: 1 }}>
                                    <Typography variant="subtitle2" color="text.secondary">Updated At</Typography>
                                    <Typography variant="body1">{new Date(selectedTicket.updated_at).toLocaleString()}</Typography>
                                </Box>
                            </Box>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
}

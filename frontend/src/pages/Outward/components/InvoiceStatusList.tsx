import { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Button,
    Chip,
    CircularProgress,
    Alert,
    Typography,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogContentText,
    DialogActions
} from '@mui/material';
import {
    CheckCircle,
    Warning,
    Receipt
} from '@mui/icons-material';
import { allocationApi } from '../../../api';
import { toast } from 'react-toastify';

interface InvoiceStatusListProps {
    sheetId: number;
    onRefresh: () => void;
}

export default function InvoiceStatusList({ sheetId, onRefresh }: InvoiceStatusListProps) {
    const [customers, setCustomers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [processingCustomerId, setProcessingCustomerId] = useState<string | null>(null);
    const [confirmDialog, setConfirmDialog] = useState<{ open: boolean, customer: any | null, action: 'mark' | 'invoice' }>({
        open: false,
        customer: null,
        action: 'mark'
    });

    useEffect(() => {
        loadInvoiceStatus();
    }, [sheetId]);

    const loadInvoiceStatus = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await allocationApi.getInvoiceStatus(sheetId);
            setCustomers(data.customers);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load invoice status');
        } finally {
            setLoading(false);
        }
    };

    const handleMarkReady = async (customer: any) => {
        setProcessingCustomerId(customer.customer_id);
        try {
            await allocationApi.markCustomerReady(sheetId, customer.customer_id);
            toast.success(`${customer.customer_name} marked ready for invoice`);
            await loadInvoiceStatus();
            onRefresh();
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Failed to mark ready');
        } finally {
            setProcessingCustomerId(null);
            setConfirmDialog({ open: false, customer: null, action: 'mark' });
        }
    };

    const handleGenerateInvoice = async (customer: any) => {
        setProcessingCustomerId(customer.customer_id);
        try {
            const result = await allocationApi.generateInvoice(sheetId, customer.customer_id);
            toast.success(`Invoice ${result.invoice_number} generated successfully!`);
            await loadInvoiceStatus();
            onRefresh();
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Failed to generate invoice');
        } finally {
            setProcessingCustomerId(null);
            setConfirmDialog({ open: false, customer: null, action: 'invoice' });
        }
    };

    const openConfirmDialog = (customer: any, action: 'mark' | 'invoice') => {
        setConfirmDialog({ open: true, customer, action });
    };

    const closeConfirmDialog = () => {
        setConfirmDialog({ open: false, customer: null, action: 'mark' });
    };

    const handleConfirm = () => {
        if (confirmDialog.customer) {
            if (confirmDialog.action === 'mark') {
                handleMarkReady(confirmDialog.customer);
            } else {
                handleGenerateInvoice(confirmDialog.customer);
            }
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return <Alert severity="error">{error}</Alert>;
    }

    if (customers.length === 0) {
        return (
            <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                    No customers found for this sheet
                </Typography>
            </Box>
        );
    }

    return (
        <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>
                Customer Invoice Status
            </Typography>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell sx={{ fontWeight: 'bold' }}>Customer</TableCell>
                            <TableCell align="center" sx={{ fontWeight: 'bold' }}>Items Count</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 'bold' }}>Total Sent</TableCell>
                            <TableCell align="center" sx={{ fontWeight: 'bold' }}>Shortfall</TableCell>
                            <TableCell align="center" sx={{ fontWeight: 'bold' }}>Invoice Status</TableCell>
                            <TableCell align="center" sx={{ fontWeight: 'bold' }}>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {customers.map((customer) => (
                            <TableRow key={customer.customer_id} hover>
                                <TableCell>{customer.customer_name}</TableCell>
                                <TableCell align="center">{customer.items_count}</TableCell>
                                <TableCell align="right">{Number(customer.total_sent).toFixed(1)} kg</TableCell>
                                <TableCell align="center">
                                    {customer.has_shortfall ? (
                                        <Chip
                                            label="Has Shortfall"
                                            color="warning"
                                            size="small"
                                            icon={<Warning />}
                                        />
                                    ) : (
                                        <Chip
                                            label="Complete"
                                            color="success"
                                            size="small"
                                            icon={<CheckCircle />}
                                        />
                                    )}
                                </TableCell>
                                <TableCell align="center">
                                    <Chip
                                        label={customer.invoice_status.toUpperCase()}
                                        color={
                                            customer.invoice_status === 'invoiced' ? 'success' :
                                                customer.invoice_status === 'ready' ? 'primary' :
                                                    'default'
                                        }
                                        size="small"
                                    />
                                </TableCell>
                                <TableCell align="center">
                                    {customer.invoice_status === 'pending' && (
                                        <Button
                                            variant="outlined"
                                            size="small"
                                            onClick={() => openConfirmDialog(customer, 'mark')}
                                            disabled={processingCustomerId === customer.customer_id}
                                        >
                                            {processingCustomerId === customer.customer_id ?
                                                <CircularProgress size={20} /> : 'Mark Ready'}
                                        </Button>
                                    )}
                                    {customer.invoice_status === 'ready' && (
                                        <Button
                                            variant="contained"
                                            size="small"
                                            startIcon={<Receipt />}
                                            onClick={() => openConfirmDialog(customer, 'invoice')}
                                            disabled={processingCustomerId === customer.customer_id}
                                        >
                                            {processingCustomerId === customer.customer_id ?
                                                <CircularProgress size={20} /> : 'Generate Invoice'}
                                        </Button>
                                    )}
                                    {customer.invoice_status === 'invoiced' && (
                                        <Chip
                                            label="Invoiced"
                                            color="success"
                                            size="small"
                                            icon={<CheckCircle />}
                                        />
                                    )}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Confirmation Dialog */}
            <Dialog
                open={confirmDialog.open}
                onClose={closeConfirmDialog}
            >
                <DialogTitle>
                    {confirmDialog.action === 'mark' ? 'Mark Ready for Invoice?' : 'Generate Invoice?'}
                </DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        {confirmDialog.action === 'mark' ? (
                            <>
                                Are you sure you want to mark <strong>{confirmDialog.customer?.customer_name}</strong> as ready for invoice generation?
                                <br /><br />
                                This will prepare all allocated items for invoicing.
                            </>
                        ) : (
                            <>
                                Are you sure you want to generate invoice for <strong>{confirmDialog.customer?.customer_name}</strong>?
                                <br /><br />
                                This will:
                                <ul>
                                    <li>Create an invoice with SENT quantities</li>
                                    <li>Debit stock from inventory</li>
                                    <li>Mark allocation as invoiced</li>
                                </ul>
                                <strong>This action cannot be undone.</strong>
                            </>
                        )}
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeConfirmDialog} color="inherit">
                        Cancel
                    </Button>
                    <Button onClick={handleConfirm} variant="contained" color="primary" autoFocus>
                        {confirmDialog.action === 'mark' ? 'Mark Ready' : 'Generate Invoice'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}

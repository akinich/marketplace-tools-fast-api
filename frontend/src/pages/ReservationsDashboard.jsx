/**
 * Reservations Dashboard - View and manage inventory reservations
 * Version: 1.1.0
 * Last Updated: 2025-11-21
 * Created: 2025-11-18
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Tooltip,
} from '@mui/material';
import CancelIcon from '@mui/icons-material/Cancel';
import ConfirmIcon from '@mui/icons-material/CheckCircle';
import RefreshIcon from '@mui/icons-material/Refresh';
import { inventoryAPI } from '../api';

const ReservationsDashboard = () => {
  const [reservations, setReservations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [confirmDialog, setConfirmDialog] = useState({ open: false, reservation: null });
  const [cancelDialog, setCancelDialog] = useState({ open: false, reservation: null });

  const fetchReservations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await inventoryAPI.getReservations({ status: statusFilter });
      setReservations(data.reservations || []);
    } catch (err) {
      console.error('Error fetching reservations:', err);
      setError('Failed to load reservations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReservations();
  }, [statusFilter]);

  const handleConfirm = async (reservationId) => {
    try {
      await inventoryAPI.confirmReservation(reservationId);
      setSuccess('Reservation confirmed and stock deducted successfully');
      setConfirmDialog({ open: false, reservation: null });
      fetchReservations();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to confirm reservation');
    }
  };

  const handleCancel = async (reservationId) => {
    try {
      await inventoryAPI.cancelReservation(reservationId);
      setSuccess('Reservation cancelled successfully');
      setCancelDialog({ open: false, reservation: null });
      fetchReservations();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to cancel reservation');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'warning',
      confirmed: 'success',
      cancelled: 'error',
      expired: 'default',
    };
    return colors[status] || 'default';
  };

  const getModuleColor = (module) => {
    const colors = {
      biofloc: 'primary',
      hatchery: 'secondary',
      growout: 'info',
      nursery: 'success',
      general: 'default',
    };
    return colors[module] || 'default';
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Stock Reservations
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchReservations}
        >
          Refresh
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status Filter</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status Filter"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="">All Statuses</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="confirmed">Confirmed</MenuItem>
                  <MenuItem value="cancelled">Cancelled</MenuItem>
                  <MenuItem value="expired">Expired</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={9}>
              <Typography variant="body2" color="text.secondary">
                Showing {reservations.length} reservation(s)
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Reservations Table */}
      <Card>
        <CardContent>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : reservations.length === 0 ? (
            <Alert severity="info">No reservations found</Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Item</TableCell>
                    <TableCell>SKU</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell>Module</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Reserved Until</TableCell>
                    <TableCell>Created By</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reservations.map((reservation) => (
                    <TableRow key={reservation.id}>
                      <TableCell>{reservation.item_name}</TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {reservation.sku || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {parseFloat(reservation.quantity).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={reservation.module_reference}
                          size="small"
                          color={getModuleColor(reservation.module_reference)}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={reservation.status}
                          size="small"
                          color={getStatusColor(reservation.status)}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDateTime(reservation.reserved_until)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {reservation.created_by_name || 'Unknown'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {reservation.status === 'pending' && (
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="Confirm Reservation">
                              <IconButton
                                size="small"
                                color="success"
                                onClick={() => setConfirmDialog({ open: true, reservation })}
                              >
                                <ConfirmIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Cancel Reservation">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => setCancelDialog({ open: true, reservation })}
                              >
                                <CancelIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Confirm Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ open: false, reservation: null })}>
        <DialogTitle>Confirm Reservation</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to confirm this reservation? This will deduct{' '}
            <strong>{confirmDialog.reservation?.quantity}</strong> units of{' '}
            <strong>{confirmDialog.reservation?.item_name}</strong> from stock using FIFO.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, reservation: null })}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="success"
            onClick={() => handleConfirm(confirmDialog.reservation?.id)}
          >
            Confirm & Deduct
          </Button>
        </DialogActions>
      </Dialog>

      {/* Cancel Dialog */}
      <Dialog open={cancelDialog.open} onClose={() => setCancelDialog({ open: false, reservation: null })}>
        <DialogTitle>Cancel Reservation</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to cancel this reservation for{' '}
            <strong>{cancelDialog.reservation?.quantity}</strong> units of{' '}
            <strong>{cancelDialog.reservation?.item_name}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialog({ open: false, reservation: null })}>
            No, Keep It
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => handleCancel(cancelDialog.reservation?.id)}
          >
            Yes, Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ReservationsDashboard;

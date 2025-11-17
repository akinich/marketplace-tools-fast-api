/**
 * Inventory Module - Items, Stock, Purchase Orders, Alerts
 * Version: 1.1.0
 * Last Updated: 2025-11-17
 *
 * Changelog:
 * ----------
 * v1.1.0 (2025-11-17):
 *   - Added Inventory Dashboard page with metrics overview
 *   - Added placeholder dialogs for Add Item and Create PO actions
 *   - Changed default route from items to dashboard
 *   - Improved UX with action button feedback
 *
 * v1.0.0 (2025-11-17):
 *   - Initial inventory module with Items, Stock, POs, and Alerts pages
 */

import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Add as AddIcon, Warning as WarningIcon } from '@mui/icons-material';
import { useQuery } from 'react-query';
import { inventoryAPI } from '../api';

// Items Page
function ItemsPage() {
  const { data, isLoading, error } = useQuery('inventoryItems', () => inventoryAPI.getItems());
  const [openAddDialog, setOpenAddDialog] = useState(false);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load items: {error.message}</Alert>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold">
          Inventory Items
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenAddDialog(true)}>
          Add Item
        </Button>
      </Box>

      {/* Add Item Dialog */}
      <Dialog open={openAddDialog} onClose={() => setOpenAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Item</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mt: 2 }}>
            Item creation form will be implemented here. This will include fields for:
            <ul>
              <li>Item Name</li>
              <li>SKU</li>
              <li>Category</li>
              <li>Unit</li>
              <li>Reorder Threshold</li>
              <li>And more...</li>
            </ul>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Item Name</TableCell>
                  <TableCell>SKU</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Current Stock</TableCell>
                  <TableCell>Unit</TableCell>
                  <TableCell>Reorder Level</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.items?.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.item_name}</TableCell>
                    <TableCell>{item.sku || '-'}</TableCell>
                    <TableCell>{item.category || '-'}</TableCell>
                    <TableCell>
                      {Number(item.current_qty) <= Number(item.reorder_threshold) ? (
                        <Chip
                          label={item.current_qty}
                          color="warning"
                          size="small"
                          icon={<WarningIcon />}
                        />
                      ) : (
                        item.current_qty
                      )}
                    </TableCell>
                    <TableCell>{item.unit}</TableCell>
                    <TableCell>{item.reorder_threshold}</TableCell>
                    <TableCell>
                      <Chip
                        label={item.is_active ? 'Active' : 'Inactive'}
                        color={item.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}

// Purchase Orders Page
function PurchaseOrdersPage() {
  const { data, isLoading, error } = useQuery('purchaseOrders', () =>
    inventoryAPI.getPurchaseOrders({ status: 'All', days_back: 30 })
  );
  const [openCreatePODialog, setOpenCreatePODialog] = useState(false);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load purchase orders: {error.message}</Alert>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold">
          Purchase Orders
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenCreatePODialog(true)}>
          Create PO
        </Button>
      </Box>

      {/* Create PO Dialog */}
      <Dialog open={openCreatePODialog} onClose={() => setOpenCreatePODialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Purchase Order</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mt: 2 }}>
            Purchase Order creation form will be implemented here. This will include:
            <ul>
              <li>Supplier Selection</li>
              <li>PO Date & Expected Delivery</li>
              <li>Items Selection (with quantities and costs)</li>
              <li>Notes</li>
              <li>Total Cost Calculation</li>
            </ul>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreatePODialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>PO Number</TableCell>
                  <TableCell>Supplier</TableCell>
                  <TableCell>PO Date</TableCell>
                  <TableCell>Expected Delivery</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Total Cost</TableCell>
                  <TableCell>Items</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.pos?.map((po) => (
                  <TableRow key={po.id}>
                    <TableCell>{po.po_number}</TableCell>
                    <TableCell>{po.supplier_name}</TableCell>
                    <TableCell>{new Date(po.po_date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      {po.expected_delivery ? new Date(po.expected_delivery).toLocaleDateString() : '-'}
                    </TableCell>
                    <TableCell>
                      <Chip label={po.status} size="small" />
                    </TableCell>
                    <TableCell>${Number(po.total_cost).toFixed(2)}</TableCell>
                    <TableCell>{po.items_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}

// Alerts Page
function AlertsPage() {
  const { data: lowStockData, isLoading: lowStockLoading } = useQuery('lowStockAlerts', () =>
    inventoryAPI.getLowStockAlerts()
  );
  const { data: expiryData, isLoading: expiryLoading } = useQuery('expiryAlerts', () =>
    inventoryAPI.getExpiryAlerts(30)
  );

  if (lowStockLoading || expiryLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Inventory Alerts
      </Typography>

      <Grid container spacing={3}>
        {/* Low Stock Alerts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom color="warning.main">
                Low Stock Items ({lowStockData?.total || 0})
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Item</TableCell>
                      <TableCell>Current</TableCell>
                      <TableCell>Threshold</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {lowStockData?.items?.slice(0, 10).map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.item_name}</TableCell>
                        <TableCell>{Number(item.current_qty).toFixed(2)}</TableCell>
                        <TableCell>{Number(item.reorder_threshold).toFixed(2)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Expiry Alerts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom color="error.main">
                Expiring Soon ({expiryData?.total || 0})
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Item</TableCell>
                      <TableCell>Expiry Date</TableCell>
                      <TableCell>Days Left</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {expiryData?.items?.slice(0, 10).map((item) => (
                      <TableRow key={item.batch_id}>
                        <TableCell>{item.item_name}</TableCell>
                        <TableCell>{new Date(item.expiry_date).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Chip
                            label={`${item.days_until_expiry} days`}
                            color={item.days_until_expiry < 7 ? 'error' : 'warning'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

// Inventory Dashboard Page
function InventoryDashboardPage() {
  const { data, isLoading, error } = useQuery('inventoryDashboard', () => inventoryAPI.getDashboard());

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load inventory dashboard: {error.message}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Inventory Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Overview of your inventory metrics
      </Typography>

      <Grid container spacing={3}>
        {/* Total Items */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">
                Total Items
              </Typography>
              <Typography variant="h4">{data?.total_items || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Low Stock Items */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderLeft: 4, borderColor: 'warning.main' }}>
            <CardContent>
              <Typography color="textSecondary" variant="overline">
                Low Stock Items
              </Typography>
              <Typography variant="h4" color="warning.main">
                {data?.low_stock_items || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Expiring Soon */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderLeft: 4, borderColor: 'error.main' }}>
            <CardContent>
              <Typography color="textSecondary" variant="overline">
                Expiring Soon
              </Typography>
              <Typography variant="h4" color="error.main">
                {data?.expiring_soon_items || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Pending POs */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="overline">
                Pending POs
              </Typography>
              <Typography variant="h4">{data?.pending_pos || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Total Stock Value */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Stock Value
              </Typography>
              <Typography variant="h3" color="primary">
                ${Number(data?.total_stock_value || 0).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Stats
              </Typography>
              <Typography variant="body2">
                Total Categories: {data?.total_categories || 0}
              </Typography>
              <Typography variant="body2">
                Active Suppliers: {data?.active_suppliers || 0}
              </Typography>
              <Typography variant="body2">
                Recent Transactions (7d): {data?.recent_transactions_7d || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

// Stock Operations Page (Placeholder)
function StockOperationsPage() {
  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Stock Operations
      </Typography>
      <Alert severity="info">
        Add Stock and Use Stock operations will be available here.
      </Alert>
    </Box>
  );
}

// Main Inventory Module Component
export default function InventoryModule() {
  return (
    <Routes>
      <Route index element={<InventoryDashboardPage />} />
      <Route path="items" element={<ItemsPage />} />
      <Route path="stock" element={<StockOperationsPage />} />
      <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
      <Route path="alerts" element={<AlertsPage />} />
    </Routes>
  );
}

/**
 * Inventory Module - Items, Stock, Purchase Orders, Alerts
 * Version: 1.0.0
 */

import React from 'react';
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
} from '@mui/material';
import { Add as AddIcon, Warning as WarningIcon } from '@mui/icons-material';
import { useQuery } from 'react-query';
import { inventoryAPI } from '../api';

// Items Page
function ItemsPage() {
  const { data, isLoading, error } = useQuery('inventoryItems', () => inventoryAPI.getItems());

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
        <Button variant="contained" startIcon={<AddIcon />}>
          Add Item
        </Button>
      </Box>

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
        <Button variant="contained" startIcon={<AddIcon />}>
          Create PO
        </Button>
      </Box>

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
      <Route index element={<Navigate to="items" replace />} />
      <Route path="items" element={<ItemsPage />} />
      <Route path="stock" element={<StockOperationsPage />} />
      <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
      <Route path="alerts" element={<AlertsPage />} />
    </Routes>
  );
}

/**
 * Inventory Module - Items, Stock, Purchase Orders, Alerts
 * Version: 1.9.1
 * Last Updated: 2025-11-21
 *
 * Changelog:
 * ----------
 * v1.9.1 (2025-11-21):
 *   - FEATURE: Added reactivate functionality for inactive items
 *   - Added "Show Status" filter dropdown (Active Only / All Items)
 *   - Inactive items now show Reactivate button instead of Delete
 *   - Enhanced UX with status filtering and reactivation capability
 *
 * v1.9.0 (2025-11-21):
 *   - BREAKING: Removed custom category input - categories must be selected from dropdown only
 *   - FEATURE: Added default_price field (optional, 2 decimal precision)
 *   - FEATURE: Added delete item functionality with stock validation
 *   - Updated AddItemDialog to require category selection from existing categories
 *   - Added delete button to items table with confirmation dialog
 *   - Updated items table to display default_price column
 *
 * v1.8.0 (2025-11-18):
 *   - FIXED: PO item dropdown now shows items properly with unique query keys
 *   - FIXED: Add Stock item dropdown loading states
 *   - FEATURE: Auto-fill supplier from item's default supplier in PO dialog
 *   - FEATURE: Auto-fill supplier from item's default supplier in Add Stock dialog
 *   - Enhanced loading states for all dropdowns (suppliers, items)
 *   - Better UX with "Loading..." and "No items available" messages
 *
 * v1.7.0 (2025-11-18):
 *   - IMPLEMENTED: Complete Purchase Order creation dialog
 *   - Dynamic items list with add/remove functionality
 *   - Real-time total cost calculation
 *   - Form validation for PO details and items
 *   - Supplier and item dropdowns with data fetching
 *   - Support for PO number, dates, notes, and multiple items
 *   - Each item includes: item selection, quantity, unit cost, line total
 *   - Full integration with backend API
 *
 * v1.6.0 (2025-11-18):
 *   - Added FULL CRUD functionality to Categories page
 *   - Added FULL CRUD functionality to Suppliers page
 *   - CategoryDialog: Create/Edit dialog with validation
 *   - SupplierDialog: Create/Edit dialog with email validation
 *   - Both pages now have Create, Edit, Delete actions
 *   - Added IconButton imports for action icons
 *   - Enhanced UX with inline edit/delete buttons
 *   - Confirmation dialogs before delete operations
 *
 * v1.5.0 (2025-11-18):
 *   - CRITICAL FIX: Implemented 3 previously placeholder pages
 *   - Stock Operations: Full Add Stock and Use Stock forms with FIFO logic
 *   - Stock Adjustments: Create adjustment form + history table with audit trail
 *   - Transaction History: Complete transaction log with filters (item, type, period)
 *   - All 11 inventory modules now fully functional and integrated with backend
 *   - Fixed placeholder issue - all pages now have real functional code
 *
 * v1.4.0 (2025-11-17):
 *   - PHASE 4: Implemented all 6 missing inventory pages
 *   - Categories Management: Full CRUD with item count
 *   - Suppliers Management: Full CRUD with contact info
 *   - Current Stock: Real-time stock levels with filters
 *   - Stock Adjustments: Record adjustments with reasons
 *   - Transaction History: Complete audit trail
 *   - Analytics & Reports: Stock movement and insights
 *   - All pages fully functional and integrated with backend API
 *
 * v1.3.0 (2025-11-17):
 *   - Added placeholder routes for all new sub-modules
 *   - Added PlaceholderPage component for Coming Soon pages
 *   - New routes: current-stock, adjustments, history, categories, suppliers, analytics
 *   - All sub-modules now have proper route handling
 *
 * v1.2.0 (2025-11-17):
 *   - Implemented complete Add Item form with validation
 *   - Added category and supplier dropdown selections
 *   - Added custom category entry support
 *   - Integrated with inventory API for item creation
 *   - Added form state management and error handling
 *   - Added loading states and success/error notifications
 *
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
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Warning as WarningIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Restore as RestoreIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useSnackbar } from 'notistack';
import { inventoryAPI } from '../api';
import { formatCurrency } from '../utils/formatters';

// Add Item Dialog Component
function AddItemDialog({ open, onClose, onSuccess }) {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  const [formData, setFormData] = useState({
    item_name: '',
    sku: '',
    category: '',
    unit: '',
    default_supplier_id: '',
    default_price: '',
    reorder_threshold: '0',
    min_stock_level: '0',
  });

  const [errors, setErrors] = useState({});

  // Fetch categories and suppliers for dropdowns
  const { data: categoriesData } = useQuery('categories', inventoryAPI.getCategories);
  const { data: suppliersData } = useQuery('suppliers', inventoryAPI.getSuppliers);

  const createItemMutation = useMutation(
    (data) => inventoryAPI.createItem(data),
    {
      onSuccess: () => {
        enqueueSnackbar('Item created successfully', { variant: 'success' });
        queryClient.invalidateQueries('inventoryItems');
        queryClient.invalidateQueries('inventoryDashboard');
        handleClose();
        if (onSuccess) onSuccess();
      },
      onError: (error) => {
        enqueueSnackbar(
          `Failed to create item: ${error.response?.data?.detail || error.message}`,
          { variant: 'error' }
        );
      },
    }
  );

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
    // Clear error for this field
    if (errors[field]) {
      setErrors({ ...errors, [field]: null });
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.item_name.trim()) {
      newErrors.item_name = 'Item name is required';
    }

    if (!formData.unit.trim()) {
      newErrors.unit = 'Unit is required';
    }

    if (formData.reorder_threshold && Number(formData.reorder_threshold) < 0) {
      newErrors.reorder_threshold = 'Must be 0 or greater';
    }

    if (formData.min_stock_level && Number(formData.min_stock_level) < 0) {
      newErrors.min_stock_level = 'Must be 0 or greater';
    }

    if (formData.default_price && Number(formData.default_price) < 0) {
      newErrors.default_price = 'Must be 0 or greater';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;

    // Prepare data for API
    const submitData = {
      item_name: formData.item_name.trim(),
      unit: formData.unit.trim(),
      reorder_threshold: formData.reorder_threshold || '0',
      min_stock_level: formData.min_stock_level || '0',
    };

    // Add optional fields if provided
    if (formData.sku?.trim()) submitData.sku = formData.sku.trim();
    if (formData.category?.trim()) submitData.category = formData.category.trim();
    if (formData.default_supplier_id) submitData.default_supplier_id = Number(formData.default_supplier_id);
    if (formData.default_price) submitData.default_price = Number(formData.default_price);

    createItemMutation.mutate(submitData);
  };

  const handleClose = () => {
    setFormData({
      item_name: '',
      sku: '',
      category: '',
      unit: '',
      default_supplier_id: '',
      default_price: '',
      reorder_threshold: '0',
      min_stock_level: '0',
    });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add New Inventory Item</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            label="Item Name"
            required
            fullWidth
            value={formData.item_name}
            onChange={handleChange('item_name')}
            error={!!errors.item_name}
            helperText={errors.item_name}
            placeholder="e.g., Fish Feed Premium"
          />

          <TextField
            label="SKU"
            fullWidth
            value={formData.sku}
            onChange={handleChange('sku')}
            placeholder="e.g., FF-001"
            helperText="Stock Keeping Unit (optional)"
          />

          <FormControl fullWidth>
            <InputLabel>Category</InputLabel>
            <Select
              value={formData.category}
              onChange={handleChange('category')}
              label="Category"
            >
              <MenuItem value="">
                <em>None</em>
              </MenuItem>
              {categoriesData?.categories?.map((cat) => (
                <MenuItem key={cat.category} value={cat.category}>
                  {cat.category}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>Select from existing categories. Create new categories in the Categories sub-module first.</FormHelperText>
          </FormControl>

          <TextField
            label="Unit of Measurement"
            required
            fullWidth
            value={formData.unit}
            onChange={handleChange('unit')}
            error={!!errors.unit}
            helperText={errors.unit || 'e.g., kg, liters, pieces, bags'}
            placeholder="e.g., kg"
          />

          <FormControl fullWidth>
            <InputLabel>Default Supplier</InputLabel>
            <Select
              value={formData.default_supplier_id}
              onChange={handleChange('default_supplier_id')}
              label="Default Supplier"
            >
              <MenuItem value="">
                <em>None</em>
              </MenuItem>
              {suppliersData?.suppliers?.map((supplier) => (
                <MenuItem key={supplier.id} value={supplier.id}>
                  {supplier.supplier_name}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>Optional - Preferred supplier for this item</FormHelperText>
          </FormControl>

          <TextField
            label="Default Price"
            type="number"
            fullWidth
            value={formData.default_price}
            onChange={handleChange('default_price')}
            error={!!errors.default_price}
            helperText={errors.default_price || 'Optional - Default unit price for this item'}
            inputProps={{ min: 0, step: 0.01 }}
          />

          <TextField
            label="Reorder Threshold"
            type="number"
            fullWidth
            value={formData.reorder_threshold}
            onChange={handleChange('reorder_threshold')}
            error={!!errors.reorder_threshold}
            helperText={errors.reorder_threshold || 'Alert when stock falls below this level'}
            inputProps={{ min: 0, step: 0.01 }}
          />

          <TextField
            label="Minimum Stock Level"
            type="number"
            fullWidth
            value={formData.min_stock_level}
            onChange={handleChange('min_stock_level')}
            error={!!errors.min_stock_level}
            helperText={errors.min_stock_level || 'Ideal minimum quantity to maintain'}
            inputProps={{ min: 0, step: 0.01 }}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={createItemMutation.isLoading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={createItemMutation.isLoading}
          startIcon={createItemMutation.isLoading ? <CircularProgress size={20} /> : <AddIcon />}
        >
          Create Item
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// Items Page
function ItemsPage() {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const { data, isLoading, error } = useQuery('inventoryItems', () => inventoryAPI.getItems());
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState({ open: false, item: null });
  const [showInactive, setShowInactive] = useState(false);

  const deleteItemMutation = useMutation(
    (itemId) => inventoryAPI.deleteItem(itemId),
    {
      onSuccess: () => {
        enqueueSnackbar('Item deactivated successfully', { variant: 'success' });
        queryClient.invalidateQueries('inventoryItems');
        queryClient.invalidateQueries('inventoryDashboard');
        setDeleteConfirmDialog({ open: false, item: null });
      },
      onError: (error) => {
        enqueueSnackbar(
          `Failed to deactivate item: ${error.response?.data?.detail || error.message}`,
          { variant: 'error' }
        );
      },
    }
  );

  const reactivateItemMutation = useMutation(
    ({ itemId, itemName }) => inventoryAPI.updateItem(itemId, { is_active: true }),
    {
      onSuccess: (data, variables) => {
        enqueueSnackbar(`Item "${variables.itemName}" reactivated successfully`, { variant: 'success' });
        queryClient.invalidateQueries('inventoryItems');
        queryClient.invalidateQueries('inventoryDashboard');
      },
      onError: (error) => {
        enqueueSnackbar(
          `Failed to reactivate item: ${error.response?.data?.detail || error.message}`,
          { variant: 'error' }
        );
      },
    }
  );

  const handleDeleteClick = (item) => {
    setDeleteConfirmDialog({ open: true, item });
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirmDialog.item) {
      deleteItemMutation.mutate(deleteConfirmDialog.item.id);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmDialog({ open: false, item: null });
  };

  const handleReactivateClick = (item) => {
    reactivateItemMutation.mutate({ itemId: item.id, itemName: item.item_name });
  };

  // Filter items based on showInactive toggle
  const filteredItems = showInactive
    ? data?.items
    : data?.items?.filter(item => item.is_active);

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
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl>
            <FormHelperText sx={{ mt: 0, mb: 0.5 }}>Show Status</FormHelperText>
            <Select
              size="small"
              value={showInactive}
              onChange={(e) => setShowInactive(e.target.value)}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value={false}>Active Only</MenuItem>
              <MenuItem value={true}>All Items</MenuItem>
            </Select>
          </FormControl>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenAddDialog(true)}>
            Add Item
          </Button>
        </Box>
      </Box>

      {/* Add Item Dialog */}
      <AddItemDialog
        open={openAddDialog}
        onClose={() => setOpenAddDialog(false)}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmDialog.open} onClose={handleDeleteCancel}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete <strong>{deleteConfirmDialog.item?.item_name}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This item will be marked as inactive. You cannot delete items with existing stock.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={deleteItemMutation.isLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleteItemMutation.isLoading}
            startIcon={deleteItemMutation.isLoading ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            Delete
          </Button>
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
                  <TableCell>Default Price</TableCell>
                  <TableCell>Current Stock</TableCell>
                  <TableCell>Unit</TableCell>
                  <TableCell>Reorder Level</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredItems?.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.item_name}</TableCell>
                    <TableCell>{item.sku || '-'}</TableCell>
                    <TableCell>{item.category || '-'}</TableCell>
                    <TableCell>{item.default_price ? formatCurrency(item.default_price) : '-'}</TableCell>
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
                    <TableCell>
                      {item.is_active ? (
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteClick(item)}
                          color="error"
                          title="Deactivate item"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      ) : (
                        <IconButton
                          size="small"
                          onClick={() => handleReactivateClick(item)}
                          color="success"
                          title="Reactivate item"
                          disabled={reactivateItemMutation.isLoading}
                        >
                          <RestoreIcon fontSize="small" />
                        </IconButton>
                      )}
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
// Purchase Order Dialog Component
function CreatePODialog({ open, onClose }) {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  const [formData, setFormData] = useState({
    po_number: '',
    supplier_id: '',
    po_date: new Date().toISOString().split('T')[0],
    expected_delivery: '',
    notes: '',
  });

  const [items, setItems] = useState([
    { item_master_id: '', ordered_qty: '', unit_cost: '' }
  ]);

  const [errors, setErrors] = useState({});

  // Fetch suppliers and items for dropdowns (use unique keys for this dialog)
  const { data: suppliersData, isLoading: suppliersLoading } = useQuery(
    'po-dialog-suppliers',
    inventoryAPI.getSuppliers
  );
  const { data: itemsData, isLoading: itemsLoading } = useQuery('po-dialog-items', () =>
    inventoryAPI.getItems({ page: 1, limit: 100 })
  );

  const suppliers = suppliersData?.suppliers || [];
  const availableItems = itemsData?.items || [];

  const createPOMutation = useMutation(
    (data) => inventoryAPI.createPurchaseOrder(data),
    {
      onSuccess: () => {
        enqueueSnackbar('Purchase Order created successfully', { variant: 'success' });
        queryClient.invalidateQueries('purchaseOrders');
        handleClose();
      },
      onError: (error) => {
        enqueueSnackbar(
          error.response?.data?.detail || 'Failed to create Purchase Order',
          { variant: 'error' }
        );
      },
    }
  );

  const handleClose = () => {
    setFormData({
      po_number: '',
      supplier_id: '',
      po_date: new Date().toISOString().split('T')[0],
      expected_delivery: '',
      notes: '',
    });
    setItems([{ item_master_id: '', ordered_qty: '', unit_cost: '' }]);
    setErrors({});
    onClose();
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);

    // Auto-fill supplier from item's default supplier (if not already set)
    if (field === 'item_master_id' && value && !formData.supplier_id) {
      const selectedItem = availableItems.find((item) => item.id === parseInt(value));
      if (selectedItem && selectedItem.default_supplier_id) {
        setFormData({ ...formData, supplier_id: selectedItem.default_supplier_id });
      }
    }
  };

  const addItem = () => {
    setItems([...items, { item_master_id: '', ordered_qty: '', unit_cost: '' }]);
  };

  const removeItem = (index) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const calculateTotal = () => {
    return items.reduce((total, item) => {
      const qty = parseFloat(item.ordered_qty) || 0;
      const cost = parseFloat(item.unit_cost) || 0;
      return total + (qty * cost);
    }, 0);
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.po_number.trim()) {
      newErrors.po_number = 'PO Number is required';
    }

    if (!formData.supplier_id) {
      newErrors.supplier_id = 'Supplier is required';
    }

    if (!formData.po_date) {
      newErrors.po_date = 'PO Date is required';
    }

    if (formData.expected_delivery && formData.expected_delivery < formData.po_date) {
      newErrors.expected_delivery = 'Expected delivery cannot be before PO date';
    }

    // Validate items
    const validItems = items.filter(
      item => item.item_master_id && item.ordered_qty && item.unit_cost
    );

    if (validItems.length === 0) {
      newErrors.items = 'At least one item is required';
    }

    items.forEach((item, index) => {
      if (item.item_master_id || item.ordered_qty || item.unit_cost) {
        if (!item.item_master_id) {
          newErrors[`item_${index}_item`] = 'Select item';
        }
        if (!item.ordered_qty || parseFloat(item.ordered_qty) <= 0) {
          newErrors[`item_${index}_qty`] = 'Enter valid quantity';
        }
        if (!item.unit_cost || parseFloat(item.unit_cost) < 0) {
          newErrors[`item_${index}_cost`] = 'Enter valid cost';
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    // Filter out empty items
    const validItems = items
      .filter(item => item.item_master_id && item.ordered_qty && item.unit_cost)
      .map(item => ({
        item_master_id: parseInt(item.item_master_id),
        ordered_qty: parseFloat(item.ordered_qty),
        unit_cost: parseFloat(item.unit_cost),
      }));

    const payload = {
      po_number: formData.po_number.trim(),
      supplier_id: parseInt(formData.supplier_id),
      po_date: formData.po_date,
      expected_delivery: formData.expected_delivery || null,
      notes: formData.notes.trim() || null,
      items: validItems,
    };

    createPOMutation.mutate(payload);
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>Create Purchase Order</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {/* PO Number */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="PO Number"
                name="po_number"
                value={formData.po_number}
                onChange={handleChange}
                error={!!errors.po_number}
                helperText={errors.po_number}
                required
              />
            </Grid>

            {/* Supplier */}
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth error={!!errors.supplier_id} required>
                <InputLabel>Supplier</InputLabel>
                <Select
                  name="supplier_id"
                  value={formData.supplier_id}
                  onChange={handleChange}
                  label="Supplier"
                  disabled={suppliersLoading}
                >
                  {suppliersLoading ? (
                    <MenuItem disabled>Loading suppliers...</MenuItem>
                  ) : suppliers.length === 0 ? (
                    <MenuItem disabled>No suppliers available</MenuItem>
                  ) : (
                    suppliers.map((supplier) => (
                      <MenuItem key={supplier.id} value={supplier.id}>
                        {supplier.supplier_name}
                      </MenuItem>
                    ))
                  )}
                </Select>
                {errors.supplier_id && <FormHelperText>{errors.supplier_id}</FormHelperText>}
              </FormControl>
            </Grid>

            {/* PO Date */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="PO Date"
                name="po_date"
                type="date"
                value={formData.po_date}
                onChange={handleChange}
                error={!!errors.po_date}
                helperText={errors.po_date}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>

            {/* Expected Delivery */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Expected Delivery"
                name="expected_delivery"
                type="date"
                value={formData.expected_delivery}
                onChange={handleChange}
                error={!!errors.expected_delivery}
                helperText={errors.expected_delivery}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            {/* Notes */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                multiline
                rows={2}
              />
            </Grid>

            {/* Items Section */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" fontWeight="bold" sx={{ mt: 2, mb: 1 }}>
                Items
              </Typography>
              {errors.items && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {errors.items}
                </Alert>
              )}
            </Grid>

            {items.map((item, index) => (
              <React.Fragment key={index}>
                <Grid item xs={12} sm={5}>
                  <FormControl fullWidth error={!!errors[`item_${index}_item`]} size="small">
                    <InputLabel>Item</InputLabel>
                    <Select
                      value={item.item_master_id}
                      onChange={(e) => handleItemChange(index, 'item_master_id', e.target.value)}
                      label="Item"
                      disabled={itemsLoading}
                    >
                      {itemsLoading ? (
                        <MenuItem disabled>Loading items...</MenuItem>
                      ) : availableItems.length === 0 ? (
                        <MenuItem disabled>No items available</MenuItem>
                      ) : (
                        availableItems.map((availItem) => (
                          <MenuItem key={availItem.id} value={availItem.id}>
                            {availItem.item_name} ({availItem.unit})
                          </MenuItem>
                        ))
                      )}
                    </Select>
                    {errors[`item_${index}_item`] && (
                      <FormHelperText>{errors[`item_${index}_item`]}</FormHelperText>
                    )}
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={2}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Quantity"
                    type="number"
                    value={item.ordered_qty}
                    onChange={(e) => handleItemChange(index, 'ordered_qty', e.target.value)}
                    error={!!errors[`item_${index}_qty`]}
                    helperText={errors[`item_${index}_qty`]}
                    inputProps={{ min: 0, step: '0.01' }}
                  />
                </Grid>

                <Grid item xs={12} sm={2}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Unit Cost"
                    type="number"
                    value={item.unit_cost}
                    onChange={(e) => handleItemChange(index, 'unit_cost', e.target.value)}
                    error={!!errors[`item_${index}_cost`]}
                    helperText={errors[`item_${index}_cost`]}
                    inputProps={{ min: 0, step: '0.01' }}
                  />
                </Grid>

                <Grid item xs={12} sm={2}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Line Total"
                    value={(
                      (parseFloat(item.ordered_qty) || 0) * (parseFloat(item.unit_cost) || 0)
                    ).toFixed(2)}
                    InputProps={{ readOnly: true }}
                  />
                </Grid>

                <Grid item xs={12} sm={1}>
                  <IconButton
                    color="error"
                    onClick={() => removeItem(index)}
                    disabled={items.length === 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Grid>
              </React.Fragment>
            ))}

            <Grid item xs={12}>
              <Button startIcon={<AddIcon />} onClick={addItem} size="small">
                Add Item
              </Button>
            </Grid>

            {/* Total Cost */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Typography variant="h6">
                  Total Cost: {formatCurrency(calculateTotal())}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={createPOMutation.isLoading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={createPOMutation.isLoading}
          >
            {createPOMutation.isLoading ? 'Creating...' : 'Create Purchase Order'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

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
      <CreatePODialog
        open={openCreatePODialog}
        onClose={() => setOpenCreatePODialog(false)}
      />

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
                    <TableCell>{formatCurrency(po.total_cost)}</TableCell>
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
                {formatCurrency(data?.total_stock_value || 0)}
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

// Add Stock Dialog Component
function AddStockDialog({ open, onClose }) {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const [formData, setFormData] = useState({
    item_master_id: '',
    quantity: '',
    unit_cost: '',
    purchase_date: new Date().toISOString().split('T')[0],
    supplier_id: '',
    batch_number: '',
    expiry_date: '',
    po_number: '',
    notes: '',
  });
  const [errors, setErrors] = useState({});

  const { data: itemsData, isLoading: itemsLoading } = useQuery('addstock-dialog-items', () =>
    inventoryAPI.getItems({ page: 1, limit: 100 })
  );
  const { data: suppliersData, isLoading: suppliersLoading } = useQuery('addstock-dialog-suppliers', () =>
    inventoryAPI.getSuppliers()
  );

  const addStockMutation = useMutation((data) => inventoryAPI.addStock(data), {
    onSuccess: () => {
      enqueueSnackbar('Stock added successfully', { variant: 'success' });
      queryClient.invalidateQueries('inventoryItems');
      queryClient.invalidateQueries('inventoryDashboard');
      handleClose();
    },
    onError: (error) => {
      enqueueSnackbar(`Failed to add stock: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
    },
  });

  const handleChange = (field) => (event) => {
    const value = event.target.value;
    setFormData({ ...formData, [field]: value });
    if (errors[field]) setErrors({ ...errors, [field]: null });

    // Auto-fill supplier from item's default supplier (if selecting item and supplier not yet set)
    if (field === 'item_master_id' && value && !formData.supplier_id) {
      const selectedItem = itemsData?.items?.find((item) => item.id === parseInt(value));
      if (selectedItem && selectedItem.default_supplier_id) {
        setFormData((prev) => ({ ...prev, [field]: value, supplier_id: selectedItem.default_supplier_id }));
      }
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.item_master_id) newErrors.item_master_id = 'Item is required';
    if (!formData.quantity || Number(formData.quantity) <= 0) newErrors.quantity = 'Quantity must be greater than 0';
    if (!formData.unit_cost || Number(formData.unit_cost) < 0) newErrors.unit_cost = 'Unit cost is required';
    if (!formData.purchase_date) newErrors.purchase_date = 'Purchase date is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    const submitData = {
      item_master_id: Number(formData.item_master_id),
      quantity: Number(formData.quantity),
      unit_cost: Number(formData.unit_cost),
      purchase_date: formData.purchase_date,
    };
    if (formData.supplier_id) submitData.supplier_id = Number(formData.supplier_id);
    if (formData.batch_number) submitData.batch_number = formData.batch_number;
    if (formData.expiry_date) submitData.expiry_date = formData.expiry_date;
    if (formData.po_number) submitData.po_number = formData.po_number;
    if (formData.notes) submitData.notes = formData.notes;
    addStockMutation.mutate(submitData);
  };

  const handleClose = () => {
    setFormData({ item_master_id: '', quantity: '', unit_cost: '', purchase_date: new Date().toISOString().split('T')[0], supplier_id: '', batch_number: '', expiry_date: '', po_number: '', notes: '' });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Stock</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <FormControl fullWidth required error={!!errors.item_master_id}>
            <InputLabel>Item</InputLabel>
            <Select value={formData.item_master_id} onChange={handleChange('item_master_id')} label="Item" disabled={itemsLoading}>
              {itemsLoading ? (
                <MenuItem disabled>Loading items...</MenuItem>
              ) : !itemsData?.items || itemsData.items.length === 0 ? (
                <MenuItem disabled>No items available</MenuItem>
              ) : (
                itemsData.items.map((item) => (
                  <MenuItem key={item.id} value={item.id}>
                    {item.item_name} ({item.unit})
                  </MenuItem>
                ))
              )}
            </Select>
            {errors.item_master_id && <FormHelperText>{errors.item_master_id}</FormHelperText>}
          </FormControl>
          <TextField label="Quantity" required type="number" fullWidth value={formData.quantity} onChange={handleChange('quantity')} error={!!errors.quantity} helperText={errors.quantity} inputProps={{ min: 0, step: 0.01 }} />
          <TextField label="Unit Cost (₹)" required type="number" fullWidth value={formData.unit_cost} onChange={handleChange('unit_cost')} error={!!errors.unit_cost} helperText={errors.unit_cost} inputProps={{ min: 0, step: 0.01 }} />
          <TextField label="Purchase Date" required type="date" fullWidth value={formData.purchase_date} onChange={handleChange('purchase_date')} error={!!errors.purchase_date} helperText={errors.purchase_date} InputLabelProps={{ shrink: true }} />
          <FormControl fullWidth>
            <InputLabel>Supplier</InputLabel>
            <Select value={formData.supplier_id} onChange={handleChange('supplier_id')} label="Supplier" disabled={suppliersLoading}>
              <MenuItem value=""><em>None</em></MenuItem>
              {suppliersLoading ? (
                <MenuItem disabled>Loading suppliers...</MenuItem>
              ) : suppliersData?.suppliers && suppliersData.suppliers.length > 0 ? (
                suppliersData.suppliers.map((supplier) => (
                  <MenuItem key={supplier.id} value={supplier.id}>
                    {supplier.supplier_name}
                  </MenuItem>
                ))
              ) : null}
            </Select>
          </FormControl>
          <TextField label="Batch Number" fullWidth value={formData.batch_number} onChange={handleChange('batch_number')} placeholder="e.g., BATCH-2024-001" />
          <TextField label="Expiry Date" type="date" fullWidth value={formData.expiry_date} onChange={handleChange('expiry_date')} InputLabelProps={{ shrink: true }} />
          <TextField label="PO Number" fullWidth value={formData.po_number} onChange={handleChange('po_number')} placeholder="Optional" />
          <TextField label="Notes" fullWidth multiline rows={2} value={formData.notes} onChange={handleChange('notes')} placeholder="Additional notes..." />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={addStockMutation.isLoading}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" disabled={addStockMutation.isLoading} startIcon={addStockMutation.isLoading ? <CircularProgress size={20} /> : <AddIcon />}>Add Stock</Button>
      </DialogActions>
    </Dialog>
  );
}

// Use Stock Dialog Component
function UseStockDialog({ open, onClose }) {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const [formData, setFormData] = useState({
    item_master_id: '',
    quantity: '',
    purpose: '',
    module_reference: '',
    tank_id: '',
    notes: '',
  });
  const [errors, setErrors] = useState({});

  const { data: itemsData } = useQuery('inventoryItems', () => inventoryAPI.getItems());

  const useStockMutation = useMutation((data) => inventoryAPI.useStock(data), {
    onSuccess: (response) => {
      enqueueSnackbar(`Stock used successfully. Cost: ${formatCurrency(response.total_cost)}`, { variant: 'success' });
      queryClient.invalidateQueries('inventoryItems');
      queryClient.invalidateQueries('inventoryDashboard');
      handleClose();
    },
    onError: (error) => {
      enqueueSnackbar(`Failed to use stock: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
    },
  });

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
    if (errors[field]) setErrors({ ...errors, [field]: null });
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.item_master_id) newErrors.item_master_id = 'Item is required';
    if (!formData.quantity || Number(formData.quantity) <= 0) newErrors.quantity = 'Quantity must be greater than 0';
    if (!formData.purpose.trim()) newErrors.purpose = 'Purpose is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    const submitData = {
      item_master_id: Number(formData.item_master_id),
      quantity: Number(formData.quantity),
      purpose: formData.purpose.trim(),
    };
    if (formData.module_reference) submitData.module_reference = formData.module_reference;
    if (formData.tank_id) submitData.tank_id = Number(formData.tank_id);
    if (formData.notes) submitData.notes = formData.notes;
    useStockMutation.mutate(submitData);
  };

  const handleClose = () => {
    setFormData({ item_master_id: '', quantity: '', purpose: '', module_reference: '', tank_id: '', notes: '' });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Use Stock (FIFO)</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <FormControl fullWidth required error={!!errors.item_master_id}>
            <InputLabel>Item</InputLabel>
            <Select value={formData.item_master_id} onChange={handleChange('item_master_id')} label="Item">
              {itemsData?.items?.map((item) => (
                <MenuItem key={item.id} value={item.id}>{item.item_name} (Available: {Number(item.current_qty).toFixed(2)} {item.unit})</MenuItem>
              ))}
            </Select>
            {errors.item_master_id && <FormHelperText>{errors.item_master_id}</FormHelperText>}
          </FormControl>
          <TextField label="Quantity to Use" required type="number" fullWidth value={formData.quantity} onChange={handleChange('quantity')} error={!!errors.quantity} helperText={errors.quantity} inputProps={{ min: 0, step: 0.01 }} />
          <TextField label="Purpose" required fullWidth value={formData.purpose} onChange={handleChange('purpose')} error={!!errors.purpose} helperText={errors.purpose || 'Why is this stock being used?'} placeholder="e.g., Tank 1 feeding, Production use" />
          <TextField label="Module Reference" fullWidth value={formData.module_reference} onChange={handleChange('module_reference')} placeholder="e.g., biofloc, processing" />
          <TextField label="Tank ID" type="number" fullWidth value={formData.tank_id} onChange={handleChange('tank_id')} placeholder="Optional" />
          <TextField label="Notes" fullWidth multiline rows={2} value={formData.notes} onChange={handleChange('notes')} placeholder="Additional notes..." />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={useStockMutation.isLoading}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" color="warning" disabled={useStockMutation.isLoading} startIcon={useStockMutation.isLoading ? <CircularProgress size={20} /> : <TrendingDownIcon />}>Use Stock</Button>
      </DialogActions>
    </Dialog>
  );
}

// Stock Operations Page
function StockOperationsPage() {
  const [addStockOpen, setAddStockOpen] = useState(false);
  const [useStockOpen, setUseStockOpen] = useState(false);

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Stock Operations
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Add new stock batches or use existing stock (FIFO)
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📦 Add Stock
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Record new stock purchases or additions to inventory
              </Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => setAddStockOpen(true)} sx={{ mt: 2 }}>
                Add Stock
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📤 Use Stock
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Deduct stock from inventory using FIFO (First In, First Out) method
              </Typography>
              <Button variant="contained" color="warning" startIcon={<TrendingDownIcon />} onClick={() => setUseStockOpen(true)} sx={{ mt: 2 }}>
                Use Stock
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Alert severity="info">
            <Typography variant="body2">
              <strong>FIFO Method:</strong> When using stock, the system automatically uses the oldest batches first (First In, First Out) to ensure proper inventory rotation and accurate costing.
            </Typography>
          </Alert>
        </Grid>
      </Grid>

      <AddStockDialog open={addStockOpen} onClose={() => setAddStockOpen(false)} />
      <UseStockDialog open={useStockOpen} onClose={() => setUseStockOpen(false)} />
    </Box>
  );
}

// ============================================================================
// PHASE 4: NEW INVENTORY PAGES - Full Implementations
// ============================================================================

// Category Create/Edit Dialog Component
function CategoryDialog({ open, onClose, category = null }) {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const isEdit = Boolean(category);

  const [formData, setFormData] = useState({
    category_name: category?.category || '',
    description: category?.description || '',
  });
  const [errors, setErrors] = useState({});

  React.useEffect(() => {
    if (category) {
      setFormData({ category_name: category.category, description: category.description || '' });
    }
  }, [category]);

  const saveMutation = useMutation(
    (data) => isEdit ? inventoryAPI.updateCategory(category.id, data) : inventoryAPI.createCategory(data),
    {
      onSuccess: () => {
        enqueueSnackbar(`Category ${isEdit ? 'updated' : 'created'} successfully`, { variant: 'success' });
        queryClient.invalidateQueries('categories');
        handleClose();
      },
      onError: (error) => {
        enqueueSnackbar(`Failed to ${isEdit ? 'update' : 'create'} category: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
      },
    }
  );

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
    if (errors[field]) setErrors({ ...errors, [field]: null });
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.category_name.trim()) newErrors.category_name = 'Category name is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    saveMutation.mutate(formData);
  };

  const handleClose = () => {
    setFormData({ category_name: '', description: '' });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{isEdit ? 'Edit Category' : 'Create New Category'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            label="Category Name"
            required
            fullWidth
            value={formData.category_name}
            onChange={handleChange('category_name')}
            error={!!errors.category_name}
            helperText={errors.category_name}
            autoFocus
          />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={formData.description}
            onChange={handleChange('description')}
            placeholder="Optional description..."
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={saveMutation.isLoading}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={saveMutation.isLoading}
          startIcon={saveMutation.isLoading ? <CircularProgress size={20} /> : isEdit ? <EditIcon /> : <AddIcon />}
        >
          {isEdit ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// Categories Management Page
function CategoriesPage() {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const { data, isLoading, error } = useQuery('categories', inventoryAPI.getCategories);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);

  const deleteMutation = useMutation(
    (categoryId) => inventoryAPI.deleteCategory(categoryId),
    {
      onSuccess: () => {
        enqueueSnackbar('Category deleted successfully', { variant: 'success' });
        queryClient.invalidateQueries('categories');
      },
      onError: (error) => {
        enqueueSnackbar(`Failed to delete category: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
      },
    }
  );

  const handleCreate = () => {
    setSelectedCategory(null);
    setDialogOpen(true);
  };

  const handleEdit = (cat) => {
    setSelectedCategory(cat);
    setDialogOpen(true);
  };

  const handleDelete = (cat) => {
    if (window.confirm(`Delete category "${cat.category}"? This will fail if items are using this category.`)) {
      deleteMutation.mutate(cat.id);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load categories: {error.message}</Alert>;
  }

  const filteredCategories = data?.categories?.filter((cat) =>
    cat.category.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold">
          Manage Categories
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          New Category
        </Button>
      </Box>

      <Box sx={{ mb: 3 }}>
        <TextField
          placeholder="Search categories..."
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ minWidth: 300 }}
        />
      </Box>

      <Grid container spacing={3}>
        {filteredCategories.map((cat) => (
          <Grid item xs={12} sm={6} md={4} key={cat.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" gutterBottom>
                      🏷️ {cat.category}
                    </Typography>
                    {cat.description && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {cat.description}
                      </Typography>
                    )}
                    <Typography variant="body2" color="text.secondary">
                      {cat.item_count} item{cat.item_count !== 1 ? 's' : ''}
                    </Typography>
                  </Box>
                  <Box>
                    <IconButton size="small" onClick={() => handleEdit(cat)} title="Edit">
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(cat)} title="Delete">
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {filteredCategories.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {searchTerm ? 'No categories match your search' : 'No categories yet. Click "New Category" to create one.'}
        </Alert>
      )}

      <CategoryDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        category={selectedCategory}
      />
    </Box>
  );
}

// Supplier Create/Edit Dialog Component
function SupplierDialog({ open, onClose, supplier = null }) {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const isEdit = Boolean(supplier);

  const [formData, setFormData] = useState({
    supplier_name: supplier?.supplier_name || '',
    contact_person: supplier?.contact_person || '',
    phone: supplier?.phone || '',
    email: supplier?.email || '',
    address: supplier?.address || '',
  });
  const [errors, setErrors] = useState({});

  React.useEffect(() => {
    if (supplier) {
      setFormData({
        supplier_name: supplier.supplier_name,
        contact_person: supplier.contact_person || '',
        phone: supplier.phone || '',
        email: supplier.email || '',
        address: supplier.address || '',
      });
    }
  }, [supplier]);

  const saveMutation = useMutation(
    (data) => isEdit ? inventoryAPI.updateSupplier(supplier.id, data) : inventoryAPI.createSupplier(data),
    {
      onSuccess: () => {
        enqueueSnackbar(`Supplier ${isEdit ? 'updated' : 'created'} successfully`, { variant: 'success' });
        queryClient.invalidateQueries('suppliers');
        handleClose();
      },
      onError: (error) => {
        enqueueSnackbar(`Failed to ${isEdit ? 'update' : 'create'} supplier: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
      },
    }
  );

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
    if (errors[field]) setErrors({ ...errors, [field]: null });
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.supplier_name.trim()) newErrors.supplier_name = 'Supplier name is required';
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    saveMutation.mutate(formData);
  };

  const handleClose = () => {
    setFormData({ supplier_name: '', contact_person: '', phone: '', email: '', address: '' });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{isEdit ? 'Edit Supplier' : 'Create New Supplier'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            label="Supplier Name"
            required
            fullWidth
            value={formData.supplier_name}
            onChange={handleChange('supplier_name')}
            error={!!errors.supplier_name}
            helperText={errors.supplier_name}
            autoFocus
          />
          <TextField
            label="Contact Person"
            fullWidth
            value={formData.contact_person}
            onChange={handleChange('contact_person')}
          />
          <TextField
            label="Email"
            type="email"
            fullWidth
            value={formData.email}
            onChange={handleChange('email')}
            error={!!errors.email}
            helperText={errors.email}
          />
          <TextField
            label="Phone"
            fullWidth
            value={formData.phone}
            onChange={handleChange('phone')}
          />
          <TextField
            label="Address"
            fullWidth
            multiline
            rows={2}
            value={formData.address}
            onChange={handleChange('address')}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={saveMutation.isLoading}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={saveMutation.isLoading}
          startIcon={saveMutation.isLoading ? <CircularProgress size={20} /> : isEdit ? <EditIcon /> : <AddIcon />}
        >
          {isEdit ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// Suppliers Management Page
function SuppliersPage() {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const { data, isLoading, error } = useQuery('suppliers', inventoryAPI.getSuppliers);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);

  const deleteMutation = useMutation(
    (supplierId) => inventoryAPI.deleteSupplier(supplierId),
    {
      onSuccess: () => {
        enqueueSnackbar('Supplier deleted successfully', { variant: 'success' });
        queryClient.invalidateQueries('suppliers');
      },
      onError: (error) => {
        enqueueSnackbar(`Failed to delete supplier: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
      },
    }
  );

  const handleCreate = () => {
    setSelectedSupplier(null);
    setDialogOpen(true);
  };

  const handleEdit = (supplier) => {
    setSelectedSupplier(supplier);
    setDialogOpen(true);
  };

  const handleDelete = (supplier) => {
    if (window.confirm(`Delete supplier "${supplier.supplier_name}"? This will fail if items are using this supplier.`)) {
      deleteMutation.mutate(supplier.id);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load suppliers: {error.message}</Alert>;
  }

  const filteredSuppliers = data?.suppliers?.filter((supplier) =>
    supplier.supplier_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (supplier.email && supplier.email.toLowerCase().includes(searchTerm.toLowerCase()))
  ) || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold">
          Manage Suppliers
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          New Supplier
        </Button>
      </Box>

      <Box sx={{ mb: 3 }}>
        <TextField
          placeholder="Search suppliers..."
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ minWidth: 300 }}
        />
      </Box>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Supplier Name</TableCell>
                  <TableCell>Contact Person</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Phone</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredSuppliers.map((supplier) => (
                  <TableRow key={supplier.id}>
                    <TableCell>
                      <Typography variant="body1" fontWeight="medium">
                        🏢 {supplier.supplier_name}
                      </Typography>
                    </TableCell>
                    <TableCell>{supplier.contact_person || '-'}</TableCell>
                    <TableCell>{supplier.email || '-'}</TableCell>
                    <TableCell>{supplier.phone || '-'}</TableCell>
                    <TableCell>
                      <Chip
                        label={supplier.is_active ? 'Active' : 'Inactive'}
                        color={supplier.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => handleEdit(supplier)} title="Edit">
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDelete(supplier)} title="Delete">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {filteredSuppliers.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {searchTerm ? 'No suppliers match your search' : 'No suppliers yet. Click "New Supplier" to create one.'}
        </Alert>
      )}

      <SupplierDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        supplier={selectedSupplier}
      />
    </Box>
  );
}

// Current Stock Page
function CurrentStockPage() {
  const { data, isLoading, error } = useQuery('inventoryItems', () => inventoryAPI.getItems());
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load stock: {error.message}</Alert>;
  }

  const filteredItems = data?.items?.filter((item) => {
    const matchesSearch = item.item_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.sku && item.sku.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = !categoryFilter || item.category === categoryFilter;
    return matchesSearch && matchesCategory;
  }) || [];

  const categories = [...new Set(data?.items?.map((item) => item.category).filter(Boolean))];

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Current Stock Levels
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          placeholder="Search items..."
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ flexGrow: 1, maxWidth: 400 }}
        />
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Category</InputLabel>
          <Select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            label="Category"
          >
            <MenuItem value="">All Categories</MenuItem>
            {categories.map((cat) => (
              <MenuItem key={cat} value={cat}>{cat}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Item</TableCell>
                  <TableCell>SKU</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell align="right">Current Stock</TableCell>
                  <TableCell align="right">Min Level</TableCell>
                  <TableCell>Unit</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredItems.map((item) => {
                  const isLowStock = Number(item.current_qty) <= Number(item.reorder_threshold);
                  return (
                    <TableRow key={item.id}>
                      <TableCell>{item.item_name}</TableCell>
                      <TableCell>{item.sku || '-'}</TableCell>
                      <TableCell>{item.category || '-'}</TableCell>
                      <TableCell align="right">
                        <Typography
                          fontWeight="bold"
                          color={isLowStock ? 'warning.main' : 'text.primary'}
                        >
                          {Number(item.current_qty).toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{Number(item.min_stock_level).toFixed(2)}</TableCell>
                      <TableCell>{item.unit}</TableCell>
                      <TableCell>
                        {isLowStock ? (
                          <Chip label="Low Stock" color="warning" size="small" icon={<WarningIcon />} />
                        ) : (
                          <Chip label="OK" color="success" size="small" />
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {filteredItems.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No items match your filters
        </Alert>
      )}
    </Box>
  );
}

// Create Adjustment Dialog Component
function CreateAdjustmentDialog({ open, onClose }) {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const [formData, setFormData] = useState({
    item_master_id: '',
    adjustment_type: 'increase',
    quantity_change: '',
    reason: '',
    notes: '',
  });
  const [errors, setErrors] = useState({});

  const { data: itemsData } = useQuery('inventoryItems', () => inventoryAPI.getItems());

  const adjustStockMutation = useMutation((data) => inventoryAPI.adjustStock(data), {
    onSuccess: () => {
      enqueueSnackbar('Stock adjustment recorded successfully', { variant: 'success' });
      queryClient.invalidateQueries('inventoryItems');
      queryClient.invalidateQueries('stockAdjustments');
      queryClient.invalidateQueries('inventoryDashboard');
      handleClose();
    },
    onError: (error) => {
      enqueueSnackbar(`Failed to adjust stock: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
    },
  });

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
    if (errors[field]) setErrors({ ...errors, [field]: null });
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.item_master_id) newErrors.item_master_id = 'Item is required';
    if (!formData.quantity_change || Number(formData.quantity_change) === 0) newErrors.quantity_change = 'Quantity must be non-zero';
    if (!formData.reason.trim()) newErrors.reason = 'Reason is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    const submitData = {
      item_master_id: Number(formData.item_master_id),
      adjustment_type: formData.adjustment_type,
      quantity_change: Number(formData.quantity_change),
      reason: formData.reason.trim(),
    };
    if (formData.notes) submitData.notes = formData.notes;
    adjustStockMutation.mutate(submitData);
  };

  const handleClose = () => {
    setFormData({ item_master_id: '', adjustment_type: 'increase', quantity_change: '', reason: '', notes: '' });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create Stock Adjustment</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <FormControl fullWidth required error={!!errors.item_master_id}>
            <InputLabel>Item</InputLabel>
            <Select value={formData.item_master_id} onChange={handleChange('item_master_id')} label="Item">
              {itemsData?.items?.map((item) => (
                <MenuItem key={item.id} value={item.id}>{item.item_name} (Current: {Number(item.current_qty).toFixed(2)} {item.unit})</MenuItem>
              ))}
            </Select>
            {errors.item_master_id && <FormHelperText>{errors.item_master_id}</FormHelperText>}
          </FormControl>

          <FormControl fullWidth required>
            <InputLabel>Adjustment Type</InputLabel>
            <Select value={formData.adjustment_type} onChange={handleChange('adjustment_type')} label="Adjustment Type">
              <MenuItem value="increase">Increase (Add to stock)</MenuItem>
              <MenuItem value="decrease">Decrease (Remove from stock)</MenuItem>
              <MenuItem value="recount">Recount (Set exact quantity)</MenuItem>
            </Select>
            <FormHelperText>
              {formData.adjustment_type === 'recount' ? 'Enter the actual counted quantity' : 'Enter the change amount'}
            </FormHelperText>
          </FormControl>

          <TextField
            label={formData.adjustment_type === 'recount' ? 'Actual Quantity' : 'Quantity Change'}
            required
            type="number"
            fullWidth
            value={formData.quantity_change}
            onChange={handleChange('quantity_change')}
            error={!!errors.quantity_change}
            helperText={errors.quantity_change}
            inputProps={{ step: 0.01 }}
          />

          <TextField
            label="Reason"
            required
            fullWidth
            value={formData.reason}
            onChange={handleChange('reason')}
            error={!!errors.reason}
            helperText={errors.reason || 'Why is this adjustment needed?'}
            placeholder="e.g., Damage, Loss, Physical count correction"
          />

          <TextField
            label="Notes"
            fullWidth
            multiline
            rows={2}
            value={formData.notes}
            onChange={handleChange('notes')}
            placeholder="Additional details..."
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={adjustStockMutation.isLoading}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={adjustStockMutation.isLoading}
          startIcon={adjustStockMutation.isLoading ? <CircularProgress size={20} /> : <EditIcon />}
        >
          Record Adjustment
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// Stock Adjustments Page
function StockAdjustmentsPage() {
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const { data, isLoading, error } = useQuery('stockAdjustments', () => inventoryAPI.getStockAdjustments({ days_back: 30 }));

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight="bold">
            Stock Adjustments
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Record inventory adjustments and corrections
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenCreateDialog(true)}>
          New Adjustment
        </Button>
      </Box>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">Failed to load adjustments: {error.message}</Alert>
      ) : (
        <Card>
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Item</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Change</TableCell>
                    <TableCell align="right">Previous</TableCell>
                    <TableCell align="right">New</TableCell>
                    <TableCell>Reason</TableCell>
                    <TableCell>Adjusted By</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data?.adjustments?.map((adj) => (
                    <TableRow key={adj.id}>
                      <TableCell>{new Date(adj.adjustment_date).toLocaleString()}</TableCell>
                      <TableCell>{adj.item_name}</TableCell>
                      <TableCell>
                        <Chip
                          label={adj.adjustment_type}
                          color={adj.adjustment_type === 'increase' ? 'success' : adj.adjustment_type === 'decrease' ? 'error' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography color={Number(adj.quantity_change) > 0 ? 'success.main' : 'error.main'} fontWeight="bold">
                          {Number(adj.quantity_change) > 0 ? '+' : ''}{Number(adj.quantity_change).toFixed(2)} {adj.unit}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{Number(adj.previous_qty).toFixed(2)}</TableCell>
                      <TableCell align="right">{Number(adj.new_qty).toFixed(2)}</TableCell>
                      <TableCell>{adj.reason}</TableCell>
                      <TableCell>{adj.adjusted_by_name || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {data?.adjustments?.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                No adjustments recorded in the last 30 days
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      <CreateAdjustmentDialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} />
    </Box>
  );
}

// Transaction History Page
function TransactionHistoryPage() {
  const [filters, setFilters] = useState({
    item_id: '',
    transaction_type: '',
    days_back: 7,
  });
  const { data, isLoading, error } = useQuery(
    ['transactions', filters],
    () => inventoryAPI.getTransactions({ ...filters, limit: 100 }),
    { keepPreviousData: true }
  );
  const { data: itemsData } = useQuery('inventoryItems', () => inventoryAPI.getItems());

  const handleFilterChange = (field) => (event) => {
    setFilters({ ...filters, [field]: event.target.value });
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Transaction History
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Complete audit trail of all inventory movements
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Item</InputLabel>
                <Select value={filters.item_id} onChange={handleFilterChange('item_id')} label="Item">
                  <MenuItem value="">All Items</MenuItem>
                  {itemsData?.items?.map((item) => (
                    <MenuItem key={item.id} value={item.id}>{item.item_name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Transaction Type</InputLabel>
                <Select value={filters.transaction_type} onChange={handleFilterChange('transaction_type')} label="Transaction Type">
                  <MenuItem value="">All Types</MenuItem>
                  <MenuItem value="add">Add Stock</MenuItem>
                  <MenuItem value="use">Use Stock</MenuItem>
                  <MenuItem value="adjustment">Adjustment</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Time Period</InputLabel>
                <Select value={filters.days_back} onChange={handleFilterChange('days_back')} label="Time Period">
                  <MenuItem value={7}>Last 7 days</MenuItem>
                  <MenuItem value={30}>Last 30 days</MenuItem>
                  <MenuItem value={90}>Last 90 days</MenuItem>
                  <MenuItem value={365}>Last year</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">Failed to load transactions: {error.message}</Alert>
      ) : (
        <Card>
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date/Time</TableCell>
                    <TableCell>Item</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Change</TableCell>
                    <TableCell align="right">New Balance</TableCell>
                    <TableCell align="right">Cost</TableCell>
                    <TableCell>User</TableCell>
                    <TableCell>Notes</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data?.transactions?.map((txn) => {
                    const isPositive = Number(txn.quantity_change) > 0;
                    return (
                      <TableRow key={txn.id}>
                        <TableCell>{new Date(txn.transaction_date).toLocaleString()}</TableCell>
                        <TableCell>{txn.item_name}</TableCell>
                        <TableCell>
                          <Chip
                            label={txn.transaction_type}
                            color={txn.transaction_type === 'add' ? 'success' : txn.transaction_type === 'use' ? 'error' : 'default'}
                            size="small"
                            icon={isPositive ? <TrendingUpIcon /> : <TrendingDownIcon />}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography color={isPositive ? 'success.main' : 'error.main'} fontWeight="bold">
                            {isPositive ? '+' : ''}{Number(txn.quantity_change).toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">{Number(txn.new_balance).toFixed(2)}</TableCell>
                        <TableCell align="right">
                          {txn.total_cost ? formatCurrency(txn.total_cost) : '-'}
                        </TableCell>
                        <TableCell>{txn.username || '-'}</TableCell>
                        <TableCell>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {txn.notes || '-'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
            {data?.transactions?.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                No transactions found for the selected filters
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

// Analytics & Reports Page
function AnalyticsPage() {
  const { data, isLoading } = useQuery('inventoryDashboard', () => inventoryAPI.getDashboard());

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        Analytics & Reports
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Inventory insights and reports
      </Typography>

      {isLoading ? (
        <CircularProgress />
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📊 Stock Overview
                </Typography>
                <Typography variant="body2">
                  Total Items: <strong>{data?.total_items || 0}</strong>
                </Typography>
                <Typography variant="body2">
                  Categories: <strong>{data?.total_categories || 0}</strong>
                </Typography>
                <Typography variant="body2">
                  Total Value: <strong>{formatCurrency(data?.total_stock_value || 0)}</strong>
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  ⚠️ Alerts Summary
                </Typography>
                <Typography variant="body2" color="warning.main">
                  Low Stock Items: <strong>{data?.low_stock_items || 0}</strong>
                </Typography>
                <Typography variant="body2" color="error.main">
                  Expiring Soon: <strong>{data?.expiring_soon_items || 0}</strong>
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Alert severity="info">
                  <Typography variant="body2" gutterBottom>
                    <strong>Advanced Analytics Features (Coming Soon)</strong>
                  </Typography>
                  <Typography variant="body2">
                    Future features will include:
                  </Typography>
                  <ul>
                    <li>Stock movement trends and charts</li>
                    <li>Consumption patterns by category</li>
                    <li>Supplier performance metrics</li>
                    <li>Cost analysis and budgeting</li>
                    <li>Forecasting and reorder recommendations</li>
                    <li>Export reports to Excel/PDF</li>
                  </ul>
                </Alert>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}

export default function InventoryModule() {
  return (
    <Routes>
      <Route index element={<InventoryDashboardPage />} />
      <Route path="items" element={<ItemsPage />} />
      <Route path="stock" element={<StockOperationsPage />} />
      <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
      <Route path="alerts" element={<AlertsPage />} />

      {/* PHASE 4: New fully-functional sub-modules */}
      <Route path="current-stock" element={<CurrentStockPage />} />
      <Route path="adjustments" element={<StockAdjustmentsPage />} />
      <Route path="history" element={<TransactionHistoryPage />} />
      <Route path="categories" element={<CategoriesPage />} />
      <Route path="suppliers" element={<SuppliersPage />} />
      <Route path="analytics" element={<AnalyticsPage />} />
    </Routes>
  );
}

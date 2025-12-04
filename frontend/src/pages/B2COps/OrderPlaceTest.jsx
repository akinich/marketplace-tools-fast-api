/**
 * Order Place Test Module
 * Version: 2.0.0
 * Updated: 2025-12-04
 *
 * Description:
 *   WooCommerce order placement testing interface
 *   - Add products with prices and stock
 *   - Editable prices per line item
 *   - Shipping charges and customer notes
 *   - Place test orders with full details
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
    Box,
    Paper,
    Typography,
    TextField,
    Button,
    Alert,
    CircularProgress,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    IconButton,
    Chip,
    Card,
    CardContent,
    Grid,
    Autocomplete,
    InputAdornment,
    Divider
} from '@mui/material';
import {
    Add as AddIcon,
    Delete as DeleteIcon,
    ShoppingCart as CartIcon,
    CheckCircle as SuccessIcon,
    LocalShipping as ShippingIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

import { placeWooOrder, checkCustomerStatus, fetchWooCustomers, fetchWooProducts } from '../../api/wooCheckout';

export default function OrderPlaceTest() {
    const { enqueueSnackbar } = useSnackbar();

    // State
    const [lineItems, setLineItems] = useState([{
        product: null,
        quantity: 1,
        price: 0,
        stockAvailable: 0
    }]);
    const [loading, setLoading] = useState(false);
    const [order, setOrder] = useState(null);
    const [error, setError] = useState(null);
    const [customerStatus, setCustomerStatus] = useState(null);
    const [checkingStatus, setCheckingStatus] = useState(true);
    const [customers, setCustomers] = useState([]);
    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [products, setProducts] = useState([]);
    const [shippingCharges, setShippingCharges] = useState(0);
    const [customerNotes, setCustomerNotes] = useState('');

    // Filter products: exclude parent products that have variations, keep simple products
    const filteredProducts = useMemo(() => {
        if (!products || products.length === 0) return [];

        // Get all parent product IDs that have variations
        const parentProductsWithVariations = new Set(
            products
                .filter(p => p.variation_id !== null && p.parent_product)
                .map(p => p.parent_product)
        );

        // Filter: keep variations and simple products (products without variations)
        return products.filter(product => {
            // If it's a variation, keep it
            if (product.variation_id !== null) return true;

            // If it's a simple product (product_name not in parentProductsWithVariations), keep it
            if (!parentProductsWithVariations.has(product.product_name)) return true;

            // Otherwise it's a parent product with variations, exclude it
            return false;
        });
    }, [products]);

    // Check customer status and load data on mount
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [status, customerList, productList] = await Promise.all([
                    checkCustomerStatus(),
                    fetchWooCustomers(),
                    fetchWooProducts()
                ]);
                setCustomerStatus(status);
                setCustomers(customerList);
                setProducts(productList);
            } catch (err) {
                console.error('Failed to load data:', err);
                enqueueSnackbar('Failed to load data', { variant: 'error' });
            } finally {
                setCheckingStatus(false);
            }
        };

        fetchData();
    }, [enqueueSnackbar]);

    // Calculate order total
    const orderTotal = useMemo(() => {
        const itemsTotal = lineItems.reduce((sum, item) => {
            if (item.product && item.quantity > 0 && item.price > 0) {
                return sum + (parseFloat(item.price) * parseInt(item.quantity));
            }
            return sum;
        }, 0);
        return itemsTotal + parseFloat(shippingCharges || 0);
    }, [lineItems, shippingCharges]);

    // Add new line item
    const handleAddItem = () => {
        setLineItems([...lineItems, {
            product: null,
            quantity: 1,
            price: 0,
            stockAvailable: 0
        }]);
    };

    // Remove line item
    const handleRemoveItem = (index) => {
        const newItems = lineItems.filter((_, i) => i !== index);
        setLineItems(newItems.length > 0 ? newItems : [{
            product: null,
            quantity: 1,
            price: 0,
            stockAvailable: 0
        }]);
    };

    // Update line item field
    const handleItemChange = (index, field, value) => {
        const newItems = [...lineItems];

        if (field === 'product' && value) {
            // When product is selected, auto-populate price and stock
            newItems[index].product = value;
            newItems[index].price = value.sale_price || value.regular_price || 0;
            newItems[index].stockAvailable = value.stock_quantity || 0;
        } else {
            newItems[index][field] = value;
        }

        setLineItems(newItems);
    };

    // Format price display for dropdown
    const formatProductLabel = (option) => {
        const priceStr = option.sale_price
            ? `₹${option.sale_price} (Reg: ₹${option.regular_price})`
            : `₹${option.regular_price || 0}`;

        const stockStr = `Stock: ${option.stock_quantity || 0}`;

        if (option.variation_id) {
            return `${option.parent_product || 'Product'} - ${option.product_name} | ${priceStr} | ${stockStr}`;
        } else {
            return `${option.product_name} | ${priceStr} | ${stockStr}`;
        }
    };

    // Place order
    const handlePlaceOrder = async () => {
        // Validate customer selection
        if (!selectedCustomer) {
            enqueueSnackbar('Please select a customer first', { variant: 'warning' });
            return;
        }

        // Validate line items
        const validItems = lineItems.filter(item => item.product && item.quantity > 0);

        if (validItems.length === 0) {
            enqueueSnackbar('Please add at least one product with valid quantity', { variant: 'warning' });
            return;
        }

        // Check stock availability
        for (const item of validItems) {
            if (item.quantity > item.stockAvailable) {
                enqueueSnackbar(
                    `Insufficient stock for ${item.product.product_name}. Available: ${item.stockAvailable}`,
                    { variant: 'error' }
                );
                return;
            }
        }

        // Convert to API format
        const apiItems = validItems.map(item => ({
            product_id: item.product.product_id,
            quantity: parseInt(item.quantity),
            variation_id: item.product.variation_id || null,
            price: parseFloat(item.price)
        }));

        setLoading(true);
        setError(null);
        setOrder(null);

        try {
            const orderData = await placeWooOrder(
                apiItems,
                selectedCustomer?.customer_id || null,
                parseFloat(shippingCharges || 0),
                customerNotes
            );
            setOrder(orderData);
            enqueueSnackbar(`Order #${orderData.id} created successfully!`, { variant: 'success' });

            // Reset form
            setLineItems([{ product: null, quantity: 1, price: 0, stockAvailable: 0 }]);
            setShippingCharges(0);
            setCustomerNotes('');
        } catch (err) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to place order';
            setError(errorMsg);
            enqueueSnackbar(errorMsg, { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box>
            <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CartIcon /> Order Place Test
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                Test WooCommerce order placement with pricing, stock, and custom fields
            </Typography>

            {/* Customer Status */}
            {checkingStatus ? (
                <Alert severity="info" sx={{ mt: 2 }}>
                    Checking customer mapping status...
                </Alert>
            ) : customerStatus && !customerStatus.has_wc_customer_id ? (
                <Alert severity="warning" sx={{ mt: 2 }}>
                    <strong>No WooCommerce Customer Mapping</strong><br />
                    You are not currently mapped to a WooCommerce customer. Please contact support to link your account before placing orders.
                </Alert>
            ) : customerStatus && customerStatus.has_wc_customer_id ? (
                <Alert severity="success" sx={{ mt: 2 }}>
                    ✓ Mapped to WooCommerce Customer ID: {customerStatus.wc_customer_id}
                </Alert>
            ) : null}

            {/* Order Form */}
            <Paper sx={{ p: 3, mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Select Customer
                </Typography>

                <Autocomplete
                    options={customers}
                    getOptionLabel={(option) =>
                        `${option.first_name || ''} ${option.last_name || ''} (ID: ${option.customer_id}) - ${option.email || ''}`.trim()
                    }
                    value={selectedCustomer}
                    onChange={(event, newValue) => setSelectedCustomer(newValue)}
                    renderInput={(params) => (
                        <TextField
                            {...params}
                            label="WooCommerce Customer"
                            placeholder="Search by name, email, or ID..."
                            helperText={selectedCustomer ? `Selected: ${selectedCustomer.first_name} ${selectedCustomer.last_name}` : 'Select a customer to place order for'}
                        />
                    )}
                    loading={checkingStatus}
                    disabled={loading}
                    sx={{ mb: 3 }}
                />

                <Typography variant="h6" gutterBottom>
                    Add Products
                </Typography>

                <TableContainer>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell width="35%">Product</TableCell>
                                <TableCell width="10%" align="center">Stock</TableCell>
                                <TableCell width="10%" align="center">Quantity</TableCell>
                                <TableCell width="15%" align="right">Price (₹)</TableCell>
                                <TableCell width="15%" align="right">Subtotal (₹)</TableCell>
                                <TableCell width="10%" align="center">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {lineItems.map((item, index) => (
                                <TableRow key={index}>
                                    <TableCell>
                                        <Autocomplete
                                            options={filteredProducts}
                                            getOptionLabel={formatProductLabel}
                                            value={item.product}
                                            onChange={(event, newValue) => handleItemChange(index, 'product', newValue)}
                                            renderInput={(params) => (
                                                <TextField
                                                    {...params}
                                                    placeholder="Search products..."
                                                    size="small"
                                                />
                                            )}
                                            disabled={loading}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell align="center">
                                        <Chip
                                            label={item.stockAvailable || 0}
                                            size="small"
                                            color={item.stockAvailable > 10 ? "success" : item.stockAvailable > 0 ? "warning" : "error"}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            value={item.quantity}
                                            onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                                            inputProps={{ min: 1, max: item.stockAvailable }}
                                            size="small"
                                            fullWidth
                                            disabled={loading}
                                            error={item.quantity > item.stockAvailable}
                                            helperText={item.quantity > item.stockAvailable ? 'Exceeds stock' : ''}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            value={item.price}
                                            onChange={(e) => handleItemChange(index, 'price', e.target.value)}
                                            inputProps={{ min: 0, step: 0.01 }}
                                            size="small"
                                            fullWidth
                                            disabled={loading || !item.product}
                                        />
                                    </TableCell>
                                    <TableCell align="right">
                                        <Typography variant="body2" fontWeight="bold">
                                            ₹{(parseFloat(item.price || 0) * parseInt(item.quantity || 0)).toFixed(2)}
                                        </Typography>
                                    </TableCell>
                                    <TableCell align="center">
                                        <IconButton
                                            onClick={() => handleRemoveItem(index)}
                                            color="error"
                                            size="small"
                                            disabled={loading || lineItems.length === 1}
                                        >
                                            <DeleteIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>

                <Box sx={{ mt: 2 }}>
                    <Button
                        startIcon={<AddIcon />}
                        onClick={handleAddItem}
                        variant="outlined"
                        disabled={loading}
                    >
                        Add Product
                    </Button>
                </Box>

                <Divider sx={{ my: 3 }} />

                {/* Shipping and Notes */}
                <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                        <TextField
                            label="Shipping Charges"
                            type="number"
                            value={shippingCharges}
                            onChange={(e) => setShippingCharges(e.target.value)}
                            InputProps={{
                                startAdornment: <InputAdornment position="start"><ShippingIcon /></InputAdornment>,
                                endAdornment: <InputAdornment position="end">₹</InputAdornment>
                            }}
                            inputProps={{ min: 0, step: 0.01 }}
                            fullWidth
                            disabled={loading}
                            helperText="Optional shipping charges to add to the order"
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                                Order Total
                            </Typography>
                            <Typography variant="h4" color="primary">
                                ₹{orderTotal.toFixed(2)}
                            </Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12}>
                        <TextField
                            label="Customer Notes"
                            multiline
                            rows={3}
                            value={customerNotes}
                            onChange={(e) => setCustomerNotes(e.target.value)}
                            fullWidth
                            disabled={loading}
                            placeholder="Add any special instructions or notes for this order..."
                            helperText="These notes will be visible in the WooCommerce order"
                        />
                    </Grid>
                </Grid>

                <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                    <Button
                        startIcon={loading ? <CircularProgress size={20} /> : <CartIcon />}
                        onClick={handlePlaceOrder}
                        variant="contained"
                        size="large"
                        disabled={loading || !selectedCustomer}
                    >
                        {loading ? 'Placing Order...' : `Place Order (₹${orderTotal.toFixed(2)})`}
                    </Button>
                </Box>
            </Paper>

            {/* Error Display */}
            {error && (
                <Alert severity="error" sx={{ mt: 3 }}>
                    <strong>Error:</strong> {error}
                </Alert>
            )}

            {/* Order Success */}
            {order && (
                <Card sx={{ mt: 3, bgcolor: 'success.light', color: 'success.contrastText' }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                            <SuccessIcon />
                            <Typography variant="h6">
                                Order Created Successfully!
                            </Typography>
                        </Box>

                        <Grid container spacing={2}>
                            <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="body2" color="inherit" sx={{ opacity: 0.8 }}>
                                    Order ID
                                </Typography>
                                <Typography variant="h6" color="inherit">
                                    #{order.id}
                                </Typography>
                            </Grid>
                            <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="body2" color="inherit" sx={{ opacity: 0.8 }}>
                                    Status
                                </Typography>
                                <Chip
                                    label={order.status}
                                    size="small"
                                    sx={{ mt: 0.5, bgcolor: 'rgba(255,255,255,0.3)' }}
                                />
                            </Grid>
                            <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="body2" color="inherit" sx={{ opacity: 0.8 }}>
                                    Total
                                </Typography>
                                <Typography variant="h6" color="inherit">
                                    {order.currency || ''} {order.total}
                                </Typography>
                            </Grid>
                            <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="body2" color="inherit" sx={{ opacity: 0.8 }}>
                                    Payment Method
                                </Typography>
                                <Typography variant="body1" color="inherit">
                                    {order.payment_method_title || 'N/A'}
                                </Typography>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            )}
        </Box>
    );
}

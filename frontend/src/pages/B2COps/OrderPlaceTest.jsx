/**
 * Order Place Test Module
 * Version: 1.0.0
 * Created: 2025-12-04
 * 
 * Description:
 *   WooCommerce order placement testing interface
 *   - Add products with IDs and quantities
 *   - Place test orders
 *   - View order confirmation
 */

import React, { useState, useEffect } from 'react';
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
    Autocomplete
} from '@mui/material';
import {
    Add as AddIcon,
    Delete as DeleteIcon,
    ShoppingCart as CartIcon,
    CheckCircle as SuccessIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

import { placeWooOrder, checkCustomerStatus, fetchWooCustomers, fetchWooProducts } from '../../api/wooCheckout';

export default function OrderPlaceTest() {
    const { enqueueSnackbar } = useSnackbar();

    // State
    const [lineItems, setLineItems] = useState([{ product: null, quantity: 1, variation_id: '' }]);
    const [loading, setLoading] = useState(false);
    const [order, setOrder] = useState(null);
    const [error, setError] = useState(null);
    const [customerStatus, setCustomerStatus] = useState(null);
    const [checkingStatus, setCheckingStatus] = useState(true);
    const [customers, setCustomers] = useState([]);
    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [loadingCustomers, setLoadingCustomers] = useState(false);
    const [products, setProducts] = useState([]);

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
            } finally {
                setCheckingStatus(false);
            }
        };

        fetchData();
    }, []);

    // Add new line item
    const handleAddItem = () => {
        setLineItems([...lineItems, { product: null, quantity: 1, variation_id: '' }]);
    };

    // Remove line item
    const handleRemoveItem = (index) => {
        const newItems = lineItems.filter((_, i) => i !== index);
        setLineItems(newItems.length > 0 ? newItems : [{ product: null, quantity: 1, variation_id: '' }]);
    };

    // Update line item field
    const handleItemChange = (index, field, value) => {
        const newItems = [...lineItems];
        newItems[index][field] = value;
        setLineItems(newItems);
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

        // Convert to API format
        const apiItems = validItems.map(item => ({
            product_id: item.product.woo_product_id,
            quantity: parseInt(item.quantity),
            variation_id: item.product.woo_variation_id || null
        }));

        setLoading(true);
        setError(null);
        setOrder(null);

        try {
            const orderData = await placeWooOrder(apiItems, selectedCustomer?.customer_id || null);
            setOrder(orderData);
            enqueueSnackbar(`Order #${orderData.id} created successfully!`, { variant: 'success' });

            // Reset form
            setLineItems([{ product: null, quantity: 1, variation_id: '' }]);
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
                Test WooCommerce order placement functionality
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
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell width="40%">Product</TableCell>
                                <TableCell width="20%">Quantity</TableCell>
                                <TableCell width="30%">Variation (if any)</TableCell>
                                <TableCell width="10%">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {lineItems.map((item, index) => (
                                <TableRow key={index}>
                                    <TableCell>
                                        <Autocomplete
                                            options={products}
                                            getOptionLabel={(option) =>
                                                option.woo_variation_id
                                                    ? `${option.product_name} - ${option.variation_name || 'Variation'} (ID: ${option.woo_product_id})`
                                                    : `${option.product_name} (ID: ${option.woo_product_id})`
                                            }
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
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            value={item.quantity}
                                            onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                                            inputProps={{ min: 1 }}
                                            size="small"
                                            fullWidth
                                            disabled={loading}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <Typography variant="body2" color="text.secondary">
                                            {item.product?.woo_variation_id ? `Variation ID: ${item.product.woo_variation_id}` : 'Simple Product'}
                                        </Typography>
                                    </TableCell>
                                    <TableCell>
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

                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                    <Button
                        startIcon={<AddIcon />}
                        onClick={handleAddItem}
                        variant="outlined"
                        disabled={loading}
                    >
                        Add Product
                    </Button>

                    <Button
                        startIcon={loading ? <CircularProgress size={20} /> : <CartIcon />}
                        onClick={handlePlaceOrder}
                        variant="contained"
                        disabled={loading || !selectedCustomer}
                    >
                        {loading ? 'Placing Order...' : 'Place Order'}
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

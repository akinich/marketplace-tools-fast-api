/**
 * WooCommerce Checkout API Client
 * Version: 1.0.0
 * Created: 2025-12-04
 * 
 * Description:
 *   API client functions for WooCommerce checkout operations
 *   - Place orders
 *   - Check customer mapping status
 */

import apiClient from './client';

/**
 * Place a WooCommerce order
 * @param {Array} lineItems - Array of {product_id, quantity, variation_id?}
 * @param {Number} wcCustomerId - Optional WooCommerce customer ID
 * @returns {Promise<Object>} WooCommerce order response
 */
export async function placeWooOrder(lineItems, wcCustomerId = null) {
    const payload = { line_items: lineItems };
    if (wcCustomerId) {
        payload.wc_customer_id = wcCustomerId;
    }

    const response = await apiClient.post('/woo-checkout/place-order', payload);
    return response.data;
}

/**
 * Check if user has WooCommerce customer mapping
 * @returns {Promise<Object>} Customer status information
 */
export async function checkCustomerStatus() {
    const response = await apiClient.get('/woo-checkout/customer-status');
    return response.data;
}

/**
 * Fetch WooCommerce customers for dropdown
 * @param {String} search - Optional search query
 * @returns {Promise<Array>} List of customers
 */
export async function fetchWooCustomers(search = '') {
    const params = { limit: 10000 };
    if (search) {
        params.search = search;
    }

    const response = await apiClient.get('/woo-customers', { params });
    return response.data.customers || [];
}

/**
 * Fetch WooCommerce products for dropdown
 * @param {String} search - Optional search query
 * @returns {Promise<Array>} List of products
 */
export async function fetchWooProducts(search = '') {
    const params = { limit: 500, active_only: true };
    if (search) {
        params.search = search;
    }

    const response = await apiClient.get('/products', { params });
    return response.data.products || [];
}

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
 * @returns {Promise<Object>} WooCommerce order response
 */
export async function placeWooOrder(lineItems) {
    const response = await apiClient.post('/woo-checkout/place-order', {
        line_items: lineItems
    });
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

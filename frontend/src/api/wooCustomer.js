/**
 * ================================================================================
 * WooCommerce Customer Master API Client
 * ================================================================================
 * Version: 1.0.0
 * Created: 2025-12-03
 * 
 * API client for WooCommerce Customer Master
 * ================================================================================
 */

import apiClient from './client';

export const wooCustomerAPI = {
    /**
     * Get all WooCommerce customers with filters
     */
    getCustomers: async (params = {}) => {
        const response = await apiClient.get('/woo-customers', { params });
        return response.data;
    },

    /**
     * Get single WooCommerce customer by ID
     */
    getCustomer: async (customerId) => {
        const response = await apiClient.get(`/woo-customers/${customerId}`);
        return response.data;
    },

    /**
     * Update WooCommerce customer
     */
    updateCustomer: async (customerId, customerData) => {
        const response = await apiClient.patch(`/woo-customers/${customerId}`, customerData);
        return response.data;
    },

    /**
     * Sync customers from WooCommerce
     */
    syncFromWooCommerce: async () => {
        const response = await apiClient.post('/woo-customers/sync', {});
        return response.data;
    },

    /**
     * Get WooCommerce customer statistics
     */
    getStats: async () => {
        const response = await apiClient.get('/woo-customers/stats');
        return response.data;
    },

    /**
     * Get sync progress
     */
    getSyncProgress: async () => {
        const response = await apiClient.get('/woo-customers/sync-progress');
        return response.data;
    },
};

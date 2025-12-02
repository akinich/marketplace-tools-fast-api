/**
 * ================================================================================
 * Zoho Item Master API Client
 * ================================================================================
 * Version: 1.0.0
 * Created: 2025-12-02
 * 
 * API client for Zoho Item Master (Zoho Books Item Management)
 * ================================================================================
 */

import apiClient from './client';

export const zohoItemAPI = {
    /**
     * Get all Zoho items with filters
     */
    getItems: async (params = {}) => {
        const response = await apiClient.get('/zoho-items', { params });
        return response.data;
    },

    /**
     * Get single Zoho item by ID
     */
    getItem: async (itemId) => {
        const response = await apiClient.get(`/zoho-items/${itemId}`);
        return response.data;
    },

    /**
     * Update Zoho item
     */
    updateItem: async (itemId, itemData) => {
        const response = await apiClient.patch(`/zoho-items/${itemId}`, itemData);
        return response.data;
    },

    /**
     * Sync items from Zoho Books
     */
    syncFromZohoBooks: async (forceRefresh = false) => {
        const response = await apiClient.post('/zoho-items/sync', {
            force_refresh: forceRefresh
        });
        return response.data;
    },

    /**
     * Get Zoho item statistics
     */
    getStats: async () => {
        const response = await apiClient.get('/zoho-items/stats');
        return response.data;
    },
};

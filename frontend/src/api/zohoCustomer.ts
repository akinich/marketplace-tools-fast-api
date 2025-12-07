/**
 * ================================================================================
 * Zoho Customer Master API Client
 * ================================================================================
 * Version: 1.0.0
 * Created: 2025-12-02
 * 
 * API client for Zoho Customer Master (Zoho Books Item Management)
 * ================================================================================
 */

import apiClient from './client';

export const zohoCustomerAPI = {
    /**
     * Get all Zoho customers with filters
     */
    getItems: async (params: any = {}): Promise<any> => {
        const response = await apiClient.get('/zoho-customers', { params });
        return response.data;
    },

    /**
     * Search customers by name
     */
    searchCustomers: async (query: string): Promise<any> => {
        // Assuming backend supports 'search' or 'name' filter.
        // If not, we might need to adjust this to match the backend implementation.
        // For now, assuming standard filter pattern.
        const response = await apiClient.get('/zoho-customers', { params: { search: query, limit: 100 } });
        return response.data;
    },

    /**
     * Get single Zoho item by ID
     */
    getItem: async (itemId: string | number): Promise<any> => {
        const response = await apiClient.get(`/zoho-customers/${itemId}`);
        return response.data;
    },

    /**
     * Update Zoho item
     */
    updateItem: async (itemId: string | number, itemData: any): Promise<any> => {
        const response = await apiClient.patch(`/zoho-customers/${itemId}`, itemData);
        return response.data;
    },

    /**
     * Sync customers from Zoho Books
     */
    syncFromZohoBooks: async (forceRefresh: boolean = false): Promise<any> => {
        const response = await apiClient.post('/zoho-customers/sync', {
            force_refresh: forceRefresh
        });
        return response.data;
    },

    /**
     * Get Zoho item statistics
     */
    getStats: async (): Promise<any> => {
        const response = await apiClient.get('/zoho-customers/stats');
        return response.data;
    },

    /**
     * Get sync progress
     */
    getSyncProgress: async (): Promise<any> => {
        const response = await apiClient.get('/zoho-customers/sync-progress');
        return response.data;
    },
};

/**
 * ================================================================================
 * Product Management API Client
 * ================================================================================
 * Version: 1.0.0
 * Created: 2025-12-01
 * 
 * API client for Woo Item Master (Product Management)
 * ================================================================================
 */

import apiClient from './client';

export const productAPI = {
    /**
     * Get all products with filters
     */
    getProducts: async (params: any = {}): Promise<any> => {
        const response = await apiClient.get('/products', { params });
        return response.data;
    },

    /**
     * Get single product by ID
     */
    getProduct: async (productId: string | number): Promise<any> => {
        const response = await apiClient.get(`/products/${productId}`);
        return response.data;
    },

    /**
     * Create new product
     */
    createProduct: async (productData: any): Promise<any> => {
        const response = await apiClient.post('/products', productData);
        return response.data;
    },

    /**
     * Update product
     */
    updateProduct: async (productId: string | number, productData: any): Promise<any> => {
        const response = await apiClient.patch(`/products/${productId}`, productData);
        return response.data;
    },

    /**
     * Sync products from WooCommerce
     */
    syncFromWooCommerce: async (limit: number = 100, updateExisting: boolean = false): Promise<any> => {
        const response = await apiClient.post('/products/sync', {
            limit,
            update_existing: updateExisting
        });
        return response.data;
    },

    /**
     * Get sync progress
     */
    getSyncProgress: async (): Promise<any> => {
        const response = await apiClient.get('/products/sync-progress');
        return response.data;
    },

    /**
     * Get product statistics
     */
    getStats: async (): Promise<any> => {
        const response = await apiClient.get('/products/stats');
        return response.data;
    },
};

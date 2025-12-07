/**
 * ================================================================================
 * Stock & Price Updater API Client
 * ================================================================================
 * Version: 1.0.1
 * Created: 2025-12-01
 * Updated: 2025-12-03
 *
 * API client for Stock & Price Updater module
 * ================================================================================
 */

import apiClient from './client';

const stockPriceAPI = {
    // Get categorized products
    getProducts: async (): Promise<any> => {
        const response = await apiClient.get('/stock-price/products');
        return response.data;
    },

    // Preview changes
    previewChanges: async (changes: any): Promise<any> => {
        const response = await apiClient.post('/stock-price/preview', { changes });
        return response.data;
    },

    // Apply updates
    applyUpdates: async (changes: any): Promise<any> => {
        const response = await apiClient.post('/stock-price/update', { changes });
        return response.data;
    },

    // Sync from WooCommerce
    syncFromWooCommerce: async (): Promise<any> => {
        const response = await apiClient.post('/stock-price/sync', {});
        return response.data;
    },

    // Download Excel template
    downloadExcelTemplate: async (): Promise<any> => {
        const response = await apiClient.get('/stock-price/excel-template', {
            responseType: 'blob',
        });
        return response.data;
    },

    // Upload Excel file
    uploadExcel: async (file: File): Promise<any> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post('/stock-price/excel-upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // Update product setting (lock/unlock)
    updateProductSetting: async (productId: string | number, variationId: string | number | null, isUpdatable: boolean, notes: string | null = null): Promise<any> => {
        const response = await apiClient.put('/stock-price/settings', {
            product_id: productId,
            variation_id: variationId,
            is_updatable: isUpdatable,
            notes,
        });
        return response.data;
    },

    // Restore deleted product
    restoreProduct: async (productId: string | number, variationId: string | number | null = null): Promise<any> => {
        const params = variationId ? `?variation_id=${variationId}` : '';
        const response = await apiClient.post(`/stock-price/restore/${productId}${params}`, {});
        return response.data;
    },

    // Get change history
    getHistory: async (limit: number = 100, offset: number = 0, productId: string | number | null = null): Promise<any> => {
        const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
        if (productId) params.append('product_id', productId.toString());

        const response = await apiClient.get(`/stock-price/history?${params.toString()}`);
        return response.data;
    },

    // Get statistics
    getStatistics: async (): Promise<any> => {
        const response = await apiClient.get('/stock-price/statistics');
        return response.data;
    },
};

export default stockPriceAPI;

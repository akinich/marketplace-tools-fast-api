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
    getProducts: async () => {
        const response = await apiClient.get('/stock-price/products');
        return response.data;
    },

    // Preview changes
    previewChanges: async (changes) => {
        const response = await apiClient.post('/stock-price/preview', { changes });
        return response.data;
    },

    // Apply updates
    applyUpdates: async (changes) => {
        const response = await apiClient.post('/stock-price/update', { changes });
        return response.data;
    },

    // Sync from WooCommerce
    syncFromWooCommerce: async () => {
        const response = await apiClient.post('/stock-price/sync', {});
        return response.data;
    },

    // Download Excel template
    downloadExcelTemplate: async () => {
        const response = await apiClient.get('/stock-price/excel-template', {
            responseType: 'blob',
        });
        return response.data;
    },

    // Upload Excel file
    uploadExcel: async (file) => {
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
    updateProductSetting: async (productId, variationId, isUpdatable, notes = null) => {
        const response = await apiClient.put('/stock-price/settings', {
            product_id: productId,
            variation_id: variationId,
            is_updatable: isUpdatable,
            notes,
        });
        return response.data;
    },

    // Restore deleted product
    restoreProduct: async (productId, variationId = null) => {
        const params = variationId ? `?variation_id=${variationId}` : '';
        const response = await apiClient.post(`/stock-price/restore/${productId}${params}`, {});
        return response.data;
    },

    // Get change history
    getHistory: async (limit = 100, offset = 0, productId = null) => {
        const params = new URLSearchParams({ limit, offset });
        if (productId) params.append('product_id', productId);

        const response = await apiClient.get(`/stock-price/history?${params.toString()}`);
        return response.data;
    },

    // Get statistics
    getStatistics: async () => {
        const response = await apiClient.get('/stock-price/statistics');
        return response.data;
    },
};

export default stockPriceAPI;

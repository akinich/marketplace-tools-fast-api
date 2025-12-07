/**
 * ================================================================================
 * Woo to Zoho Export API Client
 * ================================================================================
 * Version: 1.0.1
 * Created: 2025-12-03
 * Updated: 2025-12-03
 *
 * API client for Woo to Zoho Export module
 * ================================================================================
 */

import apiClient from './client';

export const wooToZohoAPI = {
    /**
     * Get last used sequence number for a prefix
     * @param {string} prefix
     * @returns {Promise<{last_sequence: number|null, suggested_sequence: number}>}
     */
    getLastSequence: async (prefix: string): Promise<any> => {
        const response = await apiClient.get('/woo-to-zoho/last-sequence', {
            params: { prefix }
        });
        return response.data;
    },

    /**
     * Preview export data
     * @param {Object} params {start_date, end_date, invoice_prefix, start_sequence}
     * @returns {Promise<Object>} Preview data
     */
    previewExport: async (params: any): Promise<any> => {
        const response = await apiClient.post('/woo-to-zoho/preview', params);
        return response.data;
    },

    /**
     * Generate and download export file
     * @param {Object} params {start_date, end_date, invoice_prefix, start_sequence}
     * @returns {Promise<Blob>} ZIP file blob
     */
    exportOrders: async (params: any): Promise<any> => {
        const response = await apiClient.post('/woo-to-zoho/export', params, {
            responseType: 'blob'
        });
        return response.data;
    },

    /**
     * Get export history
     * @param {Object} params {start_date, end_date}
     * @returns {Promise<Array>} History items
     */
    getHistory: async (params: any): Promise<any> => {
        const response = await apiClient.get('/woo-to-zoho/history', {
            params
        });
        return response.data;
    }
};

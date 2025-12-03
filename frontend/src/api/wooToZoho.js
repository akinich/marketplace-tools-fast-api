import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with auth header
const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

export const wooToZohoAPI = {
    /**
     * Get last used sequence number for a prefix
     * @param {string} prefix 
     * @returns {Promise<{last_sequence: number|null, suggested_sequence: number}>}
     */
    getLastSequence: async (prefix) => {
        const response = await axios.get(`${API_URL}/woo-to-zoho/last-sequence`, {
            params: { prefix },
            headers: getAuthHeader()
        });
        return response.data;
    },

    /**
     * Preview export data
     * @param {Object} params {start_date, end_date, invoice_prefix, start_sequence}
     * @returns {Promise<Object>} Preview data
     */
    previewExport: async (params) => {
        const response = await axios.post(`${API_URL}/woo-to-zoho/preview`, params, {
            headers: getAuthHeader()
        });
        return response.data;
    },

    /**
     * Generate and download export file
     * @param {Object} params {start_date, end_date, invoice_prefix, start_sequence}
     * @returns {Promise<Blob>} ZIP file blob
     */
    exportOrders: async (params) => {
        const response = await axios.post(`${API_URL}/woo-to-zoho/export`, params, {
            headers: getAuthHeader(),
            responseType: 'blob'
        });
        return response.data;
    },

    /**
     * Get export history
     * @param {Object} params {start_date, end_date}
     * @returns {Promise<Array>} History items
     */
    getHistory: async (params) => {
        const response = await axios.get(`${API_URL}/woo-to-zoho/history`, {
            params,
            headers: getAuthHeader()
        });
        return response.data;
    }
};

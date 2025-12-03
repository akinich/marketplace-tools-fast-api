import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get auth token from localStorage
const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

const stockPriceAPI = {
    // Get categorized products
    getProducts: async () => {
        const response = await axios.get(`${API_URL}/api/v1/stock-price/products`, {
            headers: getAuthHeaders(),
        });
        return response.data;
    },

    // Preview changes
    previewChanges: async (changes) => {
        const response = await axios.post(
            `${API_URL}/api/v1/stock-price/preview`,
            { changes },
            { headers: getAuthHeaders() }
        );
        return response.data;
    },

    // Apply updates
    applyUpdates: async (changes) => {
        const response = await axios.post(
            `${API_URL}/api/v1/stock-price/update`,
            { changes },
            { headers: getAuthHeaders() }
        );
        return response.data;
    },

    // Sync from WooCommerce
    syncFromWooCommerce: async () => {
        const response = await axios.post(
            `${API_URL}/api/v1/stock-price/sync`,
            {},
            { headers: getAuthHeaders() }
        );
        return response.data;
    },

    // Download Excel template
    downloadExcelTemplate: async () => {
        const response = await axios.get(`${API_URL}/api/v1/stock-price/excel-template`, {
            headers: getAuthHeaders(),
            responseType: 'blob',
        });
        return response.data;
    },

    // Upload Excel file
    uploadExcel: async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post(
            `${API_URL}/api/v1/stock-price/excel-upload`,
            formData,
            {
                headers: {
                    ...getAuthHeaders(),
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data;
    },

    // Update product setting (lock/unlock)
    updateProductSetting: async (productId, variationId, isUpdatable, notes = null) => {
        const response = await axios.put(
            `${API_URL}/api/v1/stock-price/settings`,
            {
                product_id: productId,
                variation_id: variationId,
                is_updatable: isUpdatable,
                notes,
            },
            { headers: getAuthHeaders() }
        );
        return response.data;
    },

    // Restore deleted product
    restoreProduct: async (productId, variationId = null) => {
        const params = variationId ? `?variation_id=${variationId}` : '';
        const response = await axios.post(
            `${API_URL}/api/v1/stock-price/restore/${productId}${params}`,
            {},
            { headers: getAuthHeaders() }
        );
        return response.data;
    },

    // Get change history
    getHistory: async (limit = 100, offset = 0, productId = null) => {
        const params = new URLSearchParams({ limit, offset });
        if (productId) params.append('product_id', productId);

        const response = await axios.get(
            `${API_URL}/api/v1/stock-price/history?${params.toString()}`,
            { headers: getAuthHeaders() }
        );
        return response.data;
    },

    // Get statistics
    getStatistics: async () => {
        const response = await axios.get(`${API_URL}/api/v1/stock-price/statistics`, {
            headers: getAuthHeaders(),
        });
        return response.data;
    },
};

export default stockPriceAPI;

/**
 * API Keys API Client
 * File: frontend/src/api/apiKeys.ts
 * Description: Client for API key management endpoints
 */

import apiClient from './client';

interface ApiKeyData {
    name: string;
    description?: string;
    scopes: string[];
    expires_in_days?: number;
}

/**
 * API Keys API endpoints
 */
export const apiKeysAPI = {
    /**
     * List all API keys for the current user
     * @returns {Promise<Array>} List of API key objects
     */
    list: async (): Promise<any> => {
        const response = await apiClient.get('/api-keys');
        return response.data;
    },

    /**
     * Create a new API key
     * @param {ApiKeyData} data - API key creation data
     * @returns {Promise<Object>} Created API key with full key (shown only once)
     */
    create: async (data: ApiKeyData): Promise<any> => {
        const response = await apiClient.post('/api-keys', data);
        return response.data;
    },

    /**
     * Revoke an API key
     * @param {number} id - API key ID
     * @returns {Promise<Object>} Success message
     */
    revoke: async (id: number): Promise<any> => {
        const response = await apiClient.delete(`/api-keys/${id}`);
        return response.data;
    },

    /**
     * Get usage logs for an API key
     * @param {number} id - API key ID
     * @param {number} [limit=100] - Maximum number of logs to retrieve
     * @returns {Promise<Array>} List of usage log entries
     */
    getUsage: async (id: number, limit: number = 100): Promise<any> => {
        const response = await apiClient.get(`/api-keys/${id}/usage`, {
            params: { limit }
        });
        return response.data;
    },

    /**
     * Get list of available permission scopes
     * @returns {Promise<Object>} Object with scopes array
     */
    getAvailableScopes: async (): Promise<any> => {
        const response = await apiClient.get('/api-keys/scopes/available');
        return response.data;
    },

    /**
     * Admin: List all API keys in the system
     * @returns {Promise<Array>} List of all API keys from all users
     */
    adminListAll: async (): Promise<any> => {
        const response = await apiClient.get('/api-keys/admin/all');
        return response.data;
    },

    /**
     * Admin: Revoke any user's API key
     * @param {number} id - API key ID
     * @returns {Promise<Object>} Success message
     */
    adminRevoke: async (id: number): Promise<any> => {
        const response = await apiClient.delete(`/api-keys/admin/${id}`);
        return response.data;
    }
};

export default apiKeysAPI;

/**
 * ============================================================================
 * Marketplace ERP - Settings API Client
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-22
 *
 * Changelog:
 * ----------
 * v1.0.0 (2025-11-22):
 *   - Initial settings API client
 *   - Get all settings (admin)
 *   - Get public settings
 *   - Get categories
 *   - Get settings by category
 *   - Update setting
 *   - Get audit log
 * ============================================================================
 */

import apiClient from './client';

export const settingsAPI = {
    /**
     * Get all settings (admin only)
     */
    getAll: async (): Promise<any> => {
        const response = await apiClient.get('/settings');
        return response.data;
    },

    /**
     * Get public settings
     */
    getPublic: async (): Promise<any> => {
        const response = await apiClient.get('/settings/public');
        return response.data;
    },

    /**
     * Get categories
     */
    getCategories: async (): Promise<any> => {
        const response = await apiClient.get('/settings/categories');
        return response.data;
    },

    /**
     * Get settings by category
     */
    getByCategory: async (category: string): Promise<any> => {
        const response = await apiClient.get(`/settings/category/${category}`);
        return response.data;
    },

    /**
     * Update setting
     */
    update: async (settingKey: string, value: any): Promise<any> => {
        const response = await apiClient.put(`/settings/${settingKey}`, {
            setting_value: value
        });
        return response.data;
    },

    /**
     * Get audit log
     */
    getAuditLog: async (settingKey: string | null = null, limit: number = 100): Promise<any> => {
        const params: any = { limit };
        if (settingKey) params.setting_key = settingKey;

        const response = await apiClient.get('/settings/audit-log', { params });
        return response.data;
    }
};

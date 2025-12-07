/**
 * Auth API Service
 * Version: 1.1.0
 *
 * Changelog:
 * v1.1.0 (2025-11-21):
 *   - Added getProfile() - Get user profile with security info
 *   - Added updateProfile(fullName) - Update user full name
 */

import apiClient from './client';

export const authAPI = {
    // Login
    login: async (email: string, password: string): Promise<any> => {
        const response = await apiClient.post('/auth/login', { email, password });
        return response.data;
    },

    // Logout
    logout: async (): Promise<any> => {
        const response = await apiClient.post('/auth/logout');
        return response.data;
    },

    // Refresh token
    refreshToken: async (refreshToken: string): Promise<any> => {
        const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
        return response.data;
    },

    // Get current user
    getCurrentUser: async (): Promise<any> => {
        const response = await apiClient.get('/auth/me');
        return response.data;
    },

    // Forgot password
    forgotPassword: async (email: string): Promise<any> => {
        const response = await apiClient.post('/auth/forgot-password', { email });
        return response.data;
    },

    // Reset password
    resetPassword: async (recoveryToken: string, newPassword: string): Promise<any> => {
        const response = await apiClient.post('/auth/reset-password', {
            recovery_token: recoveryToken,
            new_password: newPassword,
        });
        return response.data;
    },

    // Change password (for logged-in users)
    changePassword: async (currentPassword: string, newPassword: string): Promise<any> => {
        const response = await apiClient.post('/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword,
        });
        return response.data;
    },

    // Get user profile
    getProfile: async (): Promise<any> => {
        const response = await apiClient.get('/auth/profile');
        return response.data;
    },

    // Update user profile
    updateProfile: async (fullName: string): Promise<any> => {
        const response = await apiClient.put('/auth/profile', {
            full_name: fullName,
        });
        return response.data;
    },
};

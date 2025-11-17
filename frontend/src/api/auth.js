/**
 * Auth API Service
 * Version: 1.0.0
 */

import apiClient from './client';

export const authAPI = {
  // Login
  login: async (email, password) => {
    const response = await apiClient.post('/auth/login', { email, password });
    return response.data;
  },

  // Logout
  logout: async () => {
    const response = await apiClient.post('/auth/logout');
    return response.data;
  },

  // Refresh token
  refreshToken: async (refreshToken) => {
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  // Forgot password
  forgotPassword: async (email) => {
    const response = await apiClient.post('/auth/forgot-password', { email });
    return response.data;
  },

  // Reset password
  resetPassword: async (recoveryToken, newPassword) => {
    const response = await apiClient.post('/auth/reset-password', {
      recovery_token: recoveryToken,
      new_password: newPassword,
    });
    return response.data;
  },
};

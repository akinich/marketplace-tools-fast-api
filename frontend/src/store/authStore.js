/**
 * ============================================================================
 * Authentication Store (Zustand)
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-17
 * ============================================================================
 */

import { create } from 'zustand';
import { authAPI } from '../api/auth';

const useAuthStore = create((set, get) => ({
  // State
  user: JSON.parse(localStorage.getItem('user')) || null,
  accessToken: localStorage.getItem('access_token') || null,
  refreshToken: localStorage.getItem('refresh_token') || null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  // Actions
  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authAPI.login(email, password);

      // Store tokens and user
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      set({
        user: data.user,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      set({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },

  logout: async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout API error:', error);
    }

    // Clear storage and state
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');

    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      error: null,
    });
  },

  refreshAccessToken: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return false;

    try {
      const data = await authAPI.refreshToken(refreshToken);
      localStorage.setItem('access_token', data.access_token);

      set({
        accessToken: data.access_token,
      });

      return true;
    } catch (error) {
      // Refresh failed - logout
      get().logout();
      return false;
    }
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;

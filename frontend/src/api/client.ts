/**
 * ============================================================================
 * Marketplace ERP - API Client
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-17
 *
 * Changelog:
 * ----------
 * v1.0.0 (2025-11-17):
 *   - Initial API client setup
 *   - Axios configuration with interceptors
 *   - Token management
 *   - Error handling
 * ============================================================================
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// API Base URL
const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_PREFIX: string = '/api/v1';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
    baseURL: `${API_BASE_URL}${API_PREFIX}`,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ============================================================================
// REQUEST INTERCEPTOR - Add auth token
// ============================================================================
apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    }
);

// ============================================================================
// RESPONSE INTERCEPTOR - Handle errors
// ============================================================================
apiClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error: any) => {
        const originalRequest = error.config;

        // If 401 and not already retried, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refresh_token');
                if (refreshToken) {
                    const response = await axios.post(
                        `${API_BASE_URL}${API_PREFIX}/auth/refresh`,
                        { refresh_token: refreshToken }
                    );

                    const { access_token } = response.data;
                    localStorage.setItem('access_token', access_token);

                    // Retry original request with new token
                    if (originalRequest.headers) {
                        originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    }
                    return apiClient(originalRequest);
                }
            } catch (refreshError) {
                // Refresh failed - logout user
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default apiClient;

/**
 * ============================================================================
 * Marketplace ERP - Product API Client
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-12-02
 *
 * API client for B2C Item Master (Product Management)
 * ============================================================================
 */

import apiClient from './client';

export const productAPI = {
  /**
   * Get all products with filters
   */
  getProducts: async (params = {}) => {
    const response = await apiClient.get('/products', { params });
    return response.data;
  },

  /**
   * Get single product by ID
   */
  getProduct: async (productId) => {
    const response = await apiClient.get(`/products/${productId}`);
    return response.data;
  },

  /**
   * Create new product
   */
  createProduct: async (productData) => {
    const response = await apiClient.post('/products', productData);
    return response.data;
  },

  /**
   * Update product
   */
  updateProduct: async (productId, productData) => {
    const response = await apiClient.patch(`/products/${productId}`, productData);
    return response.data;
  },

  /**
   * Sync products from WooCommerce
   */
  syncFromWooCommerce: async (limit = 100, updateExisting = false) => {
    const response = await apiClient.post('/products/sync', {
      limit,
      update_existing: updateExisting
    });
    return response.data;
  },

  /**
   * Get product statistics
   */
  getStats: async () => {
    const response = await apiClient.get('/products/stats');
    return response.data;
  },
};

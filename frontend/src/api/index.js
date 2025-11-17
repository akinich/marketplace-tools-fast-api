/**
 * API Services Export
 * Version: 1.0.0
 */

import apiClient from './client';
import { authAPI } from './auth';

// ============================================================================
// DASHBOARD API
// ============================================================================
export const dashboardAPI = {
  getSummary: async () => {
    const response = await apiClient.get('/dashboard/summary');
    return response.data;
  },

  getUserModules: async () => {
    const response = await apiClient.get('/dashboard/modules');
    return response.data;
  },
};

// ============================================================================
// ADMIN API
// ============================================================================
export const adminAPI = {
  // Users
  getUsers: async (params = {}) => {
    const response = await apiClient.get('/admin/users', { params });
    return response.data;
  },

  createUser: async (data) => {
    const response = await apiClient.post('/admin/users', data);
    return response.data;
  },

  updateUser: async (userId, data) => {
    const response = await apiClient.put(`/admin/users/${userId}`, data);
    return response.data;
  },

  deleteUser: async (userId) => {
    const response = await apiClient.delete(`/admin/users/${userId}`);
    return response.data;
  },

  // Permissions
  getUserPermissions: async (userId) => {
    const response = await apiClient.get(`/admin/permissions/${userId}`);
    return response.data;
  },

  updateUserPermissions: async (userId, moduleIds) => {
    const response = await apiClient.put(`/admin/permissions/${userId}`, { module_ids: moduleIds });
    return response.data;
  },

  // Activity Logs
  getActivityLogs: async (params = {}) => {
    const response = await apiClient.get('/admin/activity-logs', { params });
    return response.data;
  },

  // Statistics
  getStatistics: async () => {
    const response = await apiClient.get('/admin/statistics');
    return response.data;
  },

  // Roles & Modules
  getRoles: async () => {
    const response = await apiClient.get('/admin/roles');
    return response.data;
  },

  getModules: async () => {
    const response = await apiClient.get('/admin/modules');
    return response.data;
  },
};

// ============================================================================
// INVENTORY API
// ============================================================================
export const inventoryAPI = {
  // Items
  getItems: async (params = {}) => {
    const response = await apiClient.get('/inventory/items', { params });
    return response.data;
  },

  createItem: async (data) => {
    const response = await apiClient.post('/inventory/items', data);
    return response.data;
  },

  updateItem: async (itemId, data) => {
    const response = await apiClient.put(`/inventory/items/${itemId}`, data);
    return response.data;
  },

  deleteItem: async (itemId) => {
    const response = await apiClient.delete(`/inventory/items/${itemId}`);
    return response.data;
  },

  // Stock Operations
  addStock: async (data) => {
    const response = await apiClient.post('/inventory/stock/add', data);
    return response.data;
  },

  useStock: async (data) => {
    const response = await apiClient.post('/inventory/stock/use', data);
    return response.data;
  },

  // Purchase Orders
  getPurchaseOrders: async (params = {}) => {
    const response = await apiClient.get('/inventory/purchase-orders', { params });
    return response.data;
  },

  createPurchaseOrder: async (data) => {
    const response = await apiClient.post('/inventory/purchase-orders', data);
    return response.data;
  },

  updatePurchaseOrder: async (poId, data) => {
    const response = await apiClient.put(`/inventory/purchase-orders/${poId}`, data);
    return response.data;
  },

  // Suppliers
  getSuppliers: async () => {
    const response = await apiClient.get('/inventory/suppliers');
    return response.data;
  },

  createSupplier: async (data) => {
    const response = await apiClient.post('/inventory/suppliers', data);
    return response.data;
  },

  updateSupplier: async (supplierId, data) => {
    const response = await apiClient.put(`/inventory/suppliers/${supplierId}`, data);
    return response.data;
  },

  // Categories
  getCategories: async () => {
    const response = await apiClient.get('/inventory/categories');
    return response.data;
  },

  // Alerts
  getLowStockAlerts: async () => {
    const response = await apiClient.get('/inventory/alerts/low-stock');
    return response.data;
  },

  getExpiryAlerts: async (days = 30) => {
    const response = await apiClient.get('/inventory/alerts/expiry', { params: { days } });
    return response.data;
  },

  // Transactions
  getTransactions: async (params = {}) => {
    const response = await apiClient.get('/inventory/transactions', { params });
    return response.data;
  },

  // Dashboard
  getDashboard: async () => {
    const response = await apiClient.get('/inventory/dashboard');
    return response.data;
  },
};

// Export all APIs
export { authAPI, apiClient };
export default {
  auth: authAPI,
  dashboard: dashboardAPI,
  admin: adminAPI,
  inventory: inventoryAPI,
};

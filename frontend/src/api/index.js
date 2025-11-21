/**
 * API Services Export
 * Version: 1.2.0
 * Last Updated: 2025-11-21
 *
 * Changelog:
 * ----------
 * v1.2.0 (2025-11-21):
 *   - Added hardDeleteItem API function for permanent deletion of inactive items
 *   - DELETE /inventory/items/{itemId}/permanent
 *
 * v1.1.1 (2025-11-21):
 *   - CRITICAL FIX: Removed duplicate export of telegramAPI
 *   - Fixed Rollup build error: "Duplicate export 'telegramAPI'"
 *   - telegramAPI now only exported once on line 430
 *
 * v1.1.0 (2025-11-20):
 *   - Added telegramAPI for Telegram bot notification management
 *   - Added endpoints for settings, status, testing, and user linking
 *
 * v1.0.0 (2025-11-17):
 *   - Initial API services export
 */

import apiClient from './client';
import { authAPI } from './auth';
import { bioflocAPI } from './biofloc';
import { docsAPI } from './docs';

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

  deleteUser: async (userId, hardDelete = false) => {
    const response = await apiClient.delete(`/admin/users/${userId}`, {
      params: { hard_delete: hardDelete }
    });
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

  updateModule: async (moduleId, data) => {
    const response = await apiClient.put(`/admin/modules/${moduleId}`, data);
    return response.data;
  },

  getModuleUsersCount: async (moduleId) => {
    const response = await apiClient.get(`/admin/modules/${moduleId}/users-count`);
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

  hardDeleteItem: async (itemId) => {
    const response = await apiClient.delete(`/inventory/items/${itemId}/permanent`);
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

  adjustStock: async (data) => {
    const response = await apiClient.post('/inventory/stock/adjust', data);
    return response.data;
  },

  getStockAdjustments: async (params = {}) => {
    const response = await apiClient.get('/inventory/stock/adjustments', { params });
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

  deleteSupplier: async (supplierId) => {
    const response = await apiClient.delete(`/inventory/suppliers/${supplierId}`);
    return response.data;
  },

  // Categories
  getCategories: async () => {
    const response = await apiClient.get('/inventory/categories');
    return response.data;
  },

  createCategory: async (data) => {
    const response = await apiClient.post('/inventory/categories', data);
    return response.data;
  },

  updateCategory: async (categoryId, data) => {
    const response = await apiClient.put(`/inventory/categories/${categoryId}`, data);
    return response.data;
  },

  deleteCategory: async (categoryId) => {
    const response = await apiClient.delete(`/inventory/categories/${categoryId}`);
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

  // ============================================================================
  // PHASE 1 & 2: BATCH OPERATIONS & RESERVATIONS (Added: 2025-11-18)
  // ============================================================================

  // Batch Deduction
  batchDeduct: async (data) => {
    const response = await apiClient.post('/inventory/stock/use-batch', data);
    return response.data;
  },

  // Bulk Fetch
  bulkFetch: async (data) => {
    const response = await apiClient.post('/inventory/items/bulk-fetch', data);
    return response.data;
  },

  // Stock Reservations
  createReservation: async (data) => {
    const response = await apiClient.post('/inventory/stock/reserve', data);
    return response.data;
  },

  getReservations: async (params = {}) => {
    const response = await apiClient.get('/inventory/stock/reservations', { params });
    return response.data;
  },

  cancelReservation: async (reservationId) => {
    const response = await apiClient.delete(`/inventory/stock/reserve/${reservationId}`);
    return response.data;
  },

  confirmReservation: async (reservationId) => {
    const response = await apiClient.post(`/inventory/stock/confirm-reservation/${reservationId}`);
    return response.data;
  },

  // ============================================================================
  // PHASE 3: MODULE INTEGRATION (Added: 2025-11-18)
  // ============================================================================

  // Module-Specific Views
  getModuleItems: async (moduleName) => {
    const response = await apiClient.get(`/inventory/module/${moduleName}/items`);
    return response.data;
  },

  getModuleConsumption: async (moduleName, daysBack = 30) => {
    const response = await apiClient.get(`/inventory/module/${moduleName}/consumption`, {
      params: { days_back: daysBack },
    });
    return response.data;
  },

  // Item-Module Mappings
  createItemModuleMapping: async (itemId, data) => {
    const response = await apiClient.post(`/inventory/items/${itemId}/modules`, data);
    return response.data;
  },

  getItemModuleMappings: async (itemId) => {
    const response = await apiClient.get(`/inventory/items/${itemId}/modules`);
    return response.data;
  },

  deleteItemModuleMapping: async (itemId, moduleName) => {
    const response = await apiClient.delete(`/inventory/items/${itemId}/modules/${moduleName}`);
    return response.data;
  },
};

// ============================================================================
// TICKETS API
// ============================================================================
export const ticketsAPI = {
  // Tickets
  getTickets: async (params = {}) => {
    const response = await apiClient.get('/tickets', { params });
    return response.data;
  },

  getMyTickets: async (params = {}) => {
    const response = await apiClient.get('/tickets/my', { params });
    return response.data;
  },

  getTicketStats: async () => {
    const response = await apiClient.get('/tickets/stats');
    return response.data;
  },

  getTicket: async (ticketId) => {
    const response = await apiClient.get(`/tickets/${ticketId}`);
    return response.data;
  },

  createTicket: async (data) => {
    const response = await apiClient.post('/tickets', data);
    return response.data;
  },

  updateTicket: async (ticketId, data) => {
    const response = await apiClient.put(`/tickets/${ticketId}`, data);
    return response.data;
  },

  // Admin Operations
  adminUpdateTicket: async (ticketId, data) => {
    const response = await apiClient.put(`/tickets/${ticketId}/admin`, data);
    return response.data;
  },

  closeTicket: async (ticketId, comment = null) => {
    const response = await apiClient.post(`/tickets/${ticketId}/close`, { comment });
    return response.data;
  },

  deleteTicket: async (ticketId) => {
    const response = await apiClient.delete(`/tickets/${ticketId}`);
    return response.data;
  },

  // Comments
  addComment: async (ticketId, data) => {
    const response = await apiClient.post(`/tickets/${ticketId}/comments`, data);
    return response.data;
  },

  updateComment: async (commentId, data) => {
    const response = await apiClient.put(`/tickets/comments/${commentId}`, data);
    return response.data;
  },

  deleteComment: async (commentId) => {
    const response = await apiClient.delete(`/tickets/comments/${commentId}`);
    return response.data;
  },
};

// ============================================================================
// DEVELOPMENT API
// ============================================================================
export const developmentAPI = {
  // Features
  getFeatures: async (params = {}) => {
    const response = await apiClient.get('/development', { params });
    return response.data;
  },

  getFeatureStats: async () => {
    const response = await apiClient.get('/development/stats');
    return response.data;
  },

  getFeature: async (featureId) => {
    const response = await apiClient.get(`/development/${featureId}`);
    return response.data;
  },

  createFeature: async (data) => {
    const response = await apiClient.post('/development', data);
    return response.data;
  },

  updateFeature: async (featureId, data) => {
    const response = await apiClient.put(`/development/${featureId}`, data);
    return response.data;
  },

  deleteFeature: async (featureId) => {
    const response = await apiClient.delete(`/development/${featureId}`);
    return response.data;
  },

  // Steps
  createStep: async (featureId, data) => {
    const response = await apiClient.post(`/development/${featureId}/steps`, data);
    return response.data;
  },

  updateStep: async (stepId, data) => {
    const response = await apiClient.put(`/development/steps/${stepId}`, data);
    return response.data;
  },

  deleteStep: async (stepId) => {
    const response = await apiClient.delete(`/development/steps/${stepId}`);
    return response.data;
  },

  reorderSteps: async (featureId, stepIds) => {
    const response = await apiClient.post(`/development/${featureId}/steps/reorder`, { step_ids: stepIds });
    return response.data;
  },

  // Comments
  addComment: async (featureId, data) => {
    const response = await apiClient.post(`/development/${featureId}/comments`, data);
    return response.data;
  },

  deleteComment: async (commentId) => {
    const response = await apiClient.delete(`/development/comments/${commentId}`);
    return response.data;
  },
};

// ============================================================================
// TELEGRAM NOTIFICATIONS API
// ============================================================================
export const telegramAPI = {
  // Settings Management (Admin)
  getSettings: async () => {
    const response = await apiClient.get('/telegram/settings');
    return response.data;
  },

  updateSettings: async (data) => {
    const response = await apiClient.put('/telegram/settings', data);
    return response.data;
  },

  // Bot Health Status (Admin)
  getStatus: async () => {
    const response = await apiClient.get('/telegram/status');
    return response.data;
  },

  // Test Notification (Admin)
  sendTest: async (data) => {
    const response = await apiClient.post('/telegram/test', data);
    return response.data;
  },

  // User Linking
  createLinkCode: async () => {
    const response = await apiClient.post('/telegram/link/create');
    return response.data;
  },

  getLinkStatus: async () => {
    const response = await apiClient.get('/telegram/link/status');
    return response.data;
  },

  unlinkTelegram: async () => {
    const response = await apiClient.post('/telegram/link/unlink');
    return response.data;
  },
};

// Export all APIs
export { authAPI, bioflocAPI, docsAPI, apiClient };
export default {
  auth: authAPI,
  dashboard: dashboardAPI,
  admin: adminAPI,
  inventory: inventoryAPI,
  biofloc: bioflocAPI,
  tickets: ticketsAPI,
  development: developmentAPI,
  docs: docsAPI,
  telegram: telegramAPI,
};

/**
 * API Services Export
 * Version: 1.3.0
 * Last Updated: 2025-11-22
 *
 * Changelog:
 * ----------
 * v1.3.0 (2025-11-22):
 *   - Added unitsAPI for managing units of measurement
 *   - CRUD operations: getUnits, createUnit, updateUnit, deleteUnit
 *   - Soft delete: deactivateUnit, reactivateUnit
 *   - Get categories endpoint for grouping units
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
import { productAPI } from './product';
import { docsAPI } from './docs';
import { settingsAPI } from './settings';
import stockPriceAPI from './stockPrice';
import { batchTrackingAPI } from './batchTracking';

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

  getWidgets: async () => {
    const response = await apiClient.get('/dashboard/widgets');
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

  // Unlock user account
  unlockUser: async (userId) => {
    const response = await apiClient.post(`/admin/users/${userId}/unlock`);
    return response.data;
  },
};

// ============================================================================
// SECURITY API
// ============================================================================
export const securityAPI = {
  // User's own sessions
  getMySessions: async () => {
    const response = await apiClient.get('/security/sessions');
    return response.data;
  },

  revokeSession: async (sessionId) => {
    const response = await apiClient.delete(`/security/sessions/${sessionId}`);
    return response.data;
  },

  revokeAllMySessions: async () => {
    const response = await apiClient.delete('/security/sessions');
    return response.data;
  },

  getMyLoginHistory: async (limit = 20) => {
    const response = await apiClient.get('/security/login-history', { params: { limit } });
    return response.data;
  },

  // Admin endpoints
  getAllSessions: async () => {
    const response = await apiClient.get('/security/admin/sessions');
    return response.data;
  },

  adminRevokeSession: async (sessionId) => {
    const response = await apiClient.delete(`/security/admin/sessions/${sessionId}`);
    return response.data;
  },

  adminRevokeUserSessions: async (userId) => {
    const response = await apiClient.delete(`/security/admin/users/${userId}/sessions`);
    return response.data;
  },

  getAllLoginHistory: async (limit = 50, statusFilter = null) => {
    const params = { limit };
    if (statusFilter) params.status_filter = statusFilter;
    const response = await apiClient.get('/security/admin/login-history', { params });
    return response.data;
  },

  getSecurityStats: async () => {
    const response = await apiClient.get('/security/admin/stats');
    return response.data;
  },
};

// ============================================================================



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

// ============================================================================
// B2C OPERATIONS API
// ============================================================================
export const b2cOpsAPI = {
  // Order Extractor
  fetchOrders: async (startDate, endDate, status = 'any') => {
    const response = await apiClient.post('/b2c-ops/orders/fetch', {
      start_date: startDate,
      end_date: endDate,
      status: status
    });
    return response.data;
  },

  exportOrders: async (orderIds, startDate, endDate) => {
    const response = await apiClient.post('/b2c-ops/orders/export', {
      order_ids: orderIds,
      start_date: startDate,
      end_date: endDate
    }, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Label Generator
  previewLabels: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/b2c-ops/labels/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  generateLabels: async (data, config) => {
    const response = await apiClient.post('/b2c-ops/labels/generate', {
      data: data,
      config: config
    }, {
      responseType: 'blob'
    });
    return response.data;
  },

  // MRP Label Generator
  previewMrpLabels: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/b2c-ops/mrp-labels/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  generateMrpLabels: async (data) => {
    const response = await apiClient.post('/b2c-ops/mrp-labels/generate', { data }, {
      responseType: 'blob'
    });
    return response.data;
  },

  listMrpLibrary: async () => {
    const response = await apiClient.get('/b2c-ops/mrp-labels/library');
    return response.data;
  },

  uploadMrpPdf: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/b2c-ops/mrp-labels/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  deleteMrpPdf: async (filename) => {
    const response = await apiClient.delete(`/b2c-ops/mrp-labels/library/${filename}`);
    return response.data;
  },
};

// Export all APIs
export { authAPI, docsAPI, settingsAPI, productAPI, stockPriceAPI, batchTrackingAPI, apiClient };
export default {
  auth: authAPI,
  dashboard: dashboardAPI,
  admin: adminAPI,
  tickets: ticketsAPI,
  development: developmentAPI,
  docs: docsAPI,
  telegram: telegramAPI,
  settings: settingsAPI,
  b2cOps: b2cOpsAPI,
  product: productAPI,
  stockPrice: stockPriceAPI,
  batchTracking: batchTrackingAPI,
};

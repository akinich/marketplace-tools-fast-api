/**
 * Webhook API Client
 * Version: 1.0.0
 */
import apiClient from './client';

export const webhooksAPI = {
  list: async () => {
    const response = await apiClient.get('/webhooks');
    return response.data;
  },

  get: async (id) => {
    const response = await apiClient.get(`/webhooks/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await apiClient.post('/webhooks', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await apiClient.put(`/webhooks/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await apiClient.delete(`/webhooks/${id}`);
    return response.data;
  },

  test: async (webhookId, testPayload = null) => {
    const response = await apiClient.post('/webhooks/test', {
      webhook_id: webhookId,
      test_payload: testPayload
    });
    return response.data;
  },

  getDeliveries: async (webhookId, limit = 50, status = null) => {
    const params = { limit };
    if (status) params.status = status;
    const response = await apiClient.get(`/webhooks/${webhookId}/deliveries`, { params });
    return response.data;
  },

  getAvailableEvents: async () => {
    const response = await apiClient.get('/webhooks/events/available');
    return response.data;
  }
};

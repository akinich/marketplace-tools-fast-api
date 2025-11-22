import apiClient from './client';

export const emailAPI = {
  // Templates
  getTemplates: async () => {
    const response = await apiClient.get('/email/templates');
    return response.data;
  },

  getTemplate: async (templateKey) => {
    const response = await apiClient.get(`/email/templates/${templateKey}`);
    return response.data;
  },

  // Queue
  getQueue: async (status = null, limit = 50) => {
    const params = { limit };
    if (status) params.status = status;
    const response = await apiClient.get('/email/queue', { params });
    return response.data;
  },

  // Send
  sendEmail: async (data) => {
    const response = await apiClient.post('/email/send', data);
    return response.data;
  },

  sendTemplateEmail: async (data) => {
    const response = await apiClient.post('/email/send-template', data);
    return response.data;
  },

  testSMTP: async (testEmail) => {
    const response = await apiClient.post('/email/test', { test_email: testEmail });
    return response.data;
  },

  // Recipients
  getRecipients: async () => {
    const response = await apiClient.get('/email/recipients');
    return response.data;
  },

  updateRecipients: async (notificationType, data) => {
    const response = await apiClient.put(`/email/recipients/${notificationType}`, data);
    return response.data;
  }
};

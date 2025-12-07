/**
 * Webhook API Client
 * Version: 1.0.0
 */
import apiClient from './client';

export const webhooksAPI = {
    list: async (): Promise<any> => {
        const response = await apiClient.get('/webhooks');
        return response.data;
    },

    get: async (id: number): Promise<any> => {
        const response = await apiClient.get(`/webhooks/${id}`);
        return response.data;
    },

    create: async (data: any): Promise<any> => {
        const response = await apiClient.post('/webhooks', data);
        return response.data;
    },

    update: async (id: number, data: any): Promise<any> => {
        const response = await apiClient.put(`/webhooks/${id}`, data);
        return response.data;
    },

    delete: async (id: number): Promise<any> => {
        const response = await apiClient.delete(`/webhooks/${id}`);
        return response.data;
    },

    test: async (webhookId: number, testPayload: any = null): Promise<any> => {
        const response = await apiClient.post('/webhooks/test', {
            webhook_id: webhookId,
            test_payload: testPayload
        });
        return response.data;
    },

    getDeliveries: async (webhookId: number, limit: number = 50, status: string | null = null): Promise<any> => {
        const params: any = { limit };
        if (status) params.status = status;
        const response = await apiClient.get(`/webhooks/${webhookId}/deliveries`, { params });
        return response.data;
    },

    getAvailableEvents: async (): Promise<any> => {
        const response = await apiClient.get('/webhooks/events/available');
        return response.data;
    }
};

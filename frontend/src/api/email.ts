import apiClient from './client';

interface EmailData {
    to: string | string[];
    subject: string;
    body: string;
    [key: string]: any;
}

interface TemplateEmailData {
    to: string | string[];
    template_key: string;
    context?: any;
}

export const emailAPI = {
    // Templates
    getTemplates: async (): Promise<any> => {
        const response = await apiClient.get('/email/templates');
        return response.data;
    },

    getTemplate: async (templateKey: string): Promise<any> => {
        const response = await apiClient.get(`/email/templates/${templateKey}`);
        return response.data;
    },

    // Queue
    getQueue: async (status: string | null = null, limit: number = 50): Promise<any> => {
        const params: any = { limit };
        if (status) params.status = status;
        const response = await apiClient.get('/email/queue', { params });
        return response.data;
    },

    // Send
    sendEmail: async (data: EmailData): Promise<any> => {
        const response = await apiClient.post('/email/send', data);
        return response.data;
    },

    sendTemplateEmail: async (data: TemplateEmailData): Promise<any> => {
        const response = await apiClient.post('/email/send-template', data);
        return response.data;
    },

    testSMTP: async (testEmail: string): Promise<any> => {
        const response = await apiClient.post('/email/test', { test_email: testEmail });
        return response.data;
    },

    // Recipients
    getRecipients: async (): Promise<any> => {
        const response = await apiClient.get('/email/recipients');
        return response.data;
    },

    updateRecipients: async (notificationType: string, data: any): Promise<any> => {
        const response = await apiClient.put(`/email/recipients/${notificationType}`, data);
        return response.data;
    }
};

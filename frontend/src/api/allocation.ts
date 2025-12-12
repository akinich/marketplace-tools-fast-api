/**
 * Allocation Sheet API
 * Version: 1.0.0
 */

import apiClient from './client';

export const allocationApi = {
    // Sheet Management
    getSheet: async (deliveryDate: string): Promise<any> => {
        const response = await apiClient.get(`/allocation/sheet/${deliveryDate}`);
        return response.data;
    },

    updateCell: async (cellId: number, data: any): Promise<any> => {
        const response = await apiClient.put(`/allocation/cell/${cellId}`, data);
        return response.data;
    },

    autoFillSheet: async (sheetId: number): Promise<any> => {
        const response = await apiClient.post(`/allocation/sheet/${sheetId}/auto-fill`);
        return response.data;
    },

    getAvailableDates: async (): Promise<any> => {
        const response = await apiClient.get('/allocation/dates');
        return response.data;
    },

    // Invoice Generation
    markCustomerReady: async (sheetId: number, customerId: string): Promise<any> => {
        const response = await apiClient.post('/allocation/customer/mark-ready', {
            sheet_id: sheetId,
            customer_id: customerId
        });
        return response.data;
    },

    generateInvoice: async (sheetId: number, customerId: string): Promise<any> => {
        const response = await apiClient.post('/allocation/customer/generate-invoice', {
            sheet_id: sheetId,
            customer_id: customerId
        });
        return response.data;
    },

    getInvoiceStatus: async (sheetId: number): Promise<any> => {
        const response = await apiClient.get(`/allocation/sheet/${sheetId}/invoice-status`);
        return response.data;
    },

    // Statistics
    getStatistics: async (sheetId: number): Promise<any> => {
        const response = await apiClient.get(`/allocation/sheet/${sheetId}/statistics`);
        return response.data;
    }
};

export default allocationApi;

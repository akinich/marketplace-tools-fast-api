/**
 * Sales Orders API Client
 * Version: 1.0.0
 * Created: 2024-12-07
 */

import apiClient from './client';
CreateSORequest,
    UpdateSORequest,
    SalesOrderListFilters,
    SalesOrderListResponse,
    CustomerPricing,
    SalesOrder // Assuming this new type is needed for the updated API
} from '../types/SalesOrder';

export const salesOrdersAPI = {
    // List Orders
    getOrders: async (filters: SalesOrderListFilters): Promise<SalesOrderListResponse> => {
        const response = await apiClient.get('/sales-orders/list', { params: filters });
        return response.data;
    },

    // Get Single Order
    getOrder: async (id: string): Promise<SalesOrder> => {
        const response = await apiClient.get(`/sales-orders/${id}`);
        return response.data;
    },

    // Create Order
    createOrder: async (data: CreateSORequest): Promise<SalesOrder> => {
        const response = await apiClient.post('/sales-orders/create', data);
        return response.data;
    },

    // Update Order
    updateOrder: async (id: string, data: UpdateSORequest): Promise<SalesOrder> => {
        const response = await apiClient.put(`/sales-orders/${id}/update`, data);
        return response.data;
    },

    // --- Customer Pricing ---

    // Check Price (3-tier logic)
    getItemPrice: async (customerId: number, itemId: number, date?: string): Promise<{ price: number | null, source: string }> => {
        const response = await apiClient.get('/sales-orders/price-check', {
            params: { customer_id: customerId, item_id: itemId, order_date: date }
        });
        return response.data;
    },

    // Get Price History
    getCustomerPricingHistory: async (customerId: number, itemId?: number): Promise<CustomerPricing[]> => {
        const response = await apiClient.get('/sales-orders/customer-pricing/history', {
            params: { customer_id: customerId, item_id: itemId }
        });
        return response.data;
    },

    // Add/Update Customer Price
    setCustomerPrice: async (request: {
        customer_id: number,
        item_id: number,
        price: number,
        effective_from: string,
        effective_to?: string,
        notes?: string
    }): Promise<CustomerPricing> => {
        const response = await apiClient.post('/sales-orders/customer-pricing', request);
        return response.data;
    },
};

export default salesOrdersAPI;

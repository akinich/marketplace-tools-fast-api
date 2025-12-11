/**
 * ================================================================================
 * Price List API Client
 * ================================================================================
 * Version: 1.0.0
 * Created: 2025-12-11
 *
 * API client for Customer Price List management with date-based validity,
 * Excel import/export, and price resolution.
 * ================================================================================
 */

import apiClient from './client';

// ============================================================================
// TYPES
// ============================================================================

export interface PriceList {
    id: number;
    price_list_name: string;
    description?: string;
    valid_from: string; // YYYY-MM-DD
    valid_to?: string; // YYYY-MM-DD
    is_active: boolean;
    items_count: number;
    customers_count: number;
    status: 'active' | 'expired' | 'upcoming' | 'inactive';
    created_by?: string;
    created_at: string;
    updated_at: string;
}

export interface PriceListCreate {
    price_list_name: string;
    description?: string;
    valid_from: string; // YYYY-MM-DD
    valid_to?: string; // YYYY-MM-DD
    is_active?: boolean;
}

export interface PriceListUpdate {
    price_list_name?: string;
    description?: string;
    valid_from?: string;
    valid_to?: string;
    is_active?: boolean;
}

export interface PriceListItem {
    id: number;
    price_list_id: number;
    item_id: number;
    item_name: string;
    item_sku?: string;
    price: number;
    notes?: string;
    created_at: string;
    updated_at: string;
}

export interface PriceListItemCreate {
    item_id: number;
    price: number;
    notes?: string;
}

export interface PriceListListResponse {
    price_lists: PriceList[];
    total: number;
    page: number;
    limit: number;
}

export interface PriceListItemsResponse {
    items: PriceListItem[];
    total: number;
}

export interface ExcelImportResponse {
    success: boolean;
    items_imported: number;
    items_updated: number;
    items_failed: number;
    errors: Array<{
        row_number: number;
        sku: string;
        error: string;
    }>;
    message: string;
}

export interface DuplicatePriceListRequest {
    new_name: string;
    copy_items?: boolean;
    valid_from?: string;
    valid_to?: string;
}

export interface ResolvedPrice {
    customer_id: number;
    item_id: number;
    price: number;
    source: 'price_list' | 'zoho_default';
    price_list_id?: number;
    price_list_name?: string;
    date_resolved_for: string;
    is_price_list_active: boolean;
}

export interface CustomerPriceListInfo {
    customer_id: number;
    company_name: string;
    contact_name?: string;
    price_list_id?: number;
    price_list_name?: string;
    price_list_status?: string;
}

export interface AssignedCustomersResponse {
    price_list_id: number;
    price_list_name: string;
    customers: CustomerPriceListInfo[];
    total: number;
}

export interface PriceHistoryItem {
    id: number;
    price_list_id: number;
    item_id?: number;
    item_name?: string;
    field_changed: string;
    old_value?: string;
    new_value?: string;
    changed_by?: string;
    changed_at: string;
}

export interface PriceHistoryResponse {
    history: PriceHistoryItem[];
    total: number;
}

export interface PriceListStats {
    total_price_lists: number;
    active_price_lists: number;
    expired_price_lists: number;
    upcoming_price_lists: number;
    total_customers_with_price_lists: number;
    expiring_within_30_days: number;
}

// ============================================================================
// API CLIENT
// ============================================================================

export const priceListAPI = {
    /**
     * List all price lists with optional filters
     */
    list: async (params?: {
        status_filter?: 'active' | 'expired' | 'upcoming';
        date_filter?: string;
        page?: number;
        limit?: number;
    }): Promise<PriceListListResponse> => {
        const response = await apiClient.get('/price-lists', { params });
        return response.data;
    },

    /**
     * Create new price list
     */
    create: async (data: PriceListCreate): Promise<PriceList> => {
        const response = await apiClient.post('/price-lists', data);
        return response.data;
    },

    /**
     * Get price list by ID
     */
    getById: async (priceListId: number): Promise<PriceList> => {
        const response = await apiClient.get(`/price-lists/${priceListId}`);
        return response.data;
    },

    /**
     * Update price list
     */
    update: async (priceListId: number, data: PriceListUpdate): Promise<PriceList> => {
        const response = await apiClient.put(`/price-lists/${priceListId}`, data);
        return response.data;
    },

    /**
     * Delete price list
     */
    delete: async (priceListId: number): Promise<void> => {
        await apiClient.delete(`/price-lists/${priceListId}`);
    },

    /**
     * Duplicate price list
     */
    duplicate: async (
        priceListId: number,
        data: DuplicatePriceListRequest
    ): Promise<PriceList> => {
        const response = await apiClient.post(`/price-lists/${priceListId}/duplicate`, data);
        return response.data;
    },

    // ============================================================================
    // ITEMS
    // ============================================================================

    /**
     * Get all items in price list
     */
    getItems: async (priceListId: number): Promise<PriceListItemsResponse> => {
        const response = await apiClient.get(`/price-lists/${priceListId}/items`);
        return response.data;
    },

    /**
     * Add or update single item
     */
    addOrUpdateItem: async (
        priceListId: number,
        data: PriceListItemCreate
    ): Promise<PriceListItem> => {
        const response = await apiClient.post(`/price-lists/${priceListId}/items`, data);
        return response.data;
    },

    /**
     * Bulk add or update items
     */
    bulkAddOrUpdateItems: async (
        priceListId: number,
        items: PriceListItemCreate[]
    ): Promise<{ added: number; updated: number; errors: any[] }> => {
        const response = await apiClient.post(`/price-lists/${priceListId}/items/bulk`, {
            items,
        });
        return response.data;
    },

    /**
     * Update item price
     */
    updateItem: async (
        priceListId: number,
        itemId: number,
        data: PriceListItemCreate
    ): Promise<PriceListItem> => {
        const response = await apiClient.put(
            `/price-lists/${priceListId}/items/${itemId}`,
            data
        );
        return response.data;
    },

    /**
     * Remove item from price list
     */
    deleteItem: async (priceListId: number, itemId: number): Promise<void> => {
        await apiClient.delete(`/price-lists/${priceListId}/items/${itemId}`);
    },

    // ============================================================================
    // EXCEL IMPORT/EXPORT
    // ============================================================================

    /**
     * Download Excel template
     */
    downloadTemplate: async (): Promise<Blob> => {
        const response = await apiClient.get('/price-lists/template/download', {
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Import from Excel
     */
    importFromExcel: async (
        priceListId: number,
        file: File
    ): Promise<ExcelImportResponse> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post(`/price-lists/${priceListId}/import`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Export to Excel
     */
    exportToExcel: async (priceListId: number): Promise<Blob> => {
        const response = await apiClient.get(`/price-lists/${priceListId}/export`, {
            responseType: 'blob',
        });
        return response.data;
    },

    // ============================================================================
    // CUSTOMER ASSIGNMENT
    // ============================================================================

    /**
     * Get assigned customers
     */
    getAssignedCustomers: async (
        priceListId: number
    ): Promise<AssignedCustomersResponse> => {
        const response = await apiClient.get(`/price-lists/${priceListId}/customers`);
        return response.data;
    },

    // ============================================================================
    // PRICE RESOLUTION
    // ============================================================================

    /**
     * Resolve price for customer + item combination
     */
    resolvePrice: async (
        customerId: number,
        itemId: number,
        dateFor?: string
    ): Promise<ResolvedPrice> => {
        const response = await apiClient.get(
            `/price-lists/resolve-price/customer/${customerId}/item/${itemId}`,
            {
                params: dateFor ? { date_for: dateFor } : undefined,
            }
        );
        return response.data;
    },

    // ============================================================================
    // HISTORY & STATS
    // ============================================================================

    /**
     * Get price list change history
     */
    getHistory: async (priceListId: number, limit?: number): Promise<PriceHistoryResponse> => {
        const response = await apiClient.get(`/price-lists/${priceListId}/history`, {
            params: limit ? { limit } : undefined,
        });
        return response.data;
    },

    /**
     * Get statistics
     */
    getStats: async (): Promise<PriceListStats> => {
        const response = await apiClient.get('/price-lists/stats/summary');
        return response.data;
    },
};

export default priceListAPI;

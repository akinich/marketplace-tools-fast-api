/**
 * ================================================================================
 * Purchase Orders API Client
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * API client for Purchase Order Management module - Complete PO lifecycle management
 * ================================================================================
 */

import apiClient from './client';

// ============================================================================
// TYPES
// ============================================================================

export enum POStatus {
    DRAFT = 'draft',
    SENT_TO_FARM = 'sent_to_farm',
    GRN_GENERATED = 'grn_generated',
    COMPLETED = 'completed',
    EXPORTED_TO_ZOHO = 'exported_to_zoho',
    CLOSED = 'closed',
}

export enum PriceSource {
    VENDOR = 'vendor',
    ZOHO = 'zoho',
    MANUAL = 'manual',
}

export interface POItem {
    item_id: number;
    quantity: number;
    unit_price?: number;
    notes?: string;
}

export interface POCreateRequest {
    vendor_id: number;
    dispatch_date: string;  // ISO date: YYYY-MM-DD
    delivery_date: string;
    items: POItem[];
    notes?: string;
}

export interface POUpdateRequest {
    vendor_id?: number;
    dispatch_date?: string;
    delivery_date?: string;
    items?: POItem[];
    notes?: string;
}

export interface POItemResponse extends POItem {
    id: number;
    item_name: string;
    item_sku?: string;
    unit_price: number;
    price_source: string;
    total_price: number;
    added_from_grn: boolean;
}

export interface POResponse {
    id: number;
    po_number: string;
    vendor_id: number;
    vendor_name: string;
    dispatch_date: string;
    delivery_date: string;
    status: string;
    total_amount: number;
    notes?: string;
    created_at: string;
    updated_at: string;
    exported_at?: string;
}

export interface StatusChange {
    from_status?: string;
    to_status: string;
    changed_by?: string;
    changed_at: string;
    notes?: string;
}

export interface PODetailResponse extends POResponse {
    items: POItemResponse[];
    status_history: StatusChange[];
}

export interface POListParams {
    status?: string;
    vendor_id?: number;
    from_date?: string;
    to_date?: string;
    item_id?: number;
    page?: number;
    limit?: number;
}

export interface POListResponse {
    pos: POResponse[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

export interface VendorPricingRequest {
    vendor_id: number;
    item_id: number;
    price: number;
    effective_from: string;
    effective_to?: string;
    notes?: string;
}

export interface PriceHistoryResponse {
    id: number;
    vendor_id: number;
    vendor_name: string;
    item_id: number;
    item_name: string;
    price: number;
    effective_from: string;
    effective_to?: string;
    created_by?: string;
    created_at: string;
    notes?: string;
}

export interface ActivePriceResponse {
    item_id: number;
    item_name: string;
    item_sku?: string;
    price: number;
    source: string;
    effective_from?: string;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

export const purchaseOrdersAPI = {
    /**
     * Create new purchase order
     */
    create: async (data: POCreateRequest): Promise<PODetailResponse> => {
        const response = await apiClient.post('/po/create', data);
        return response.data;
    },

    /**
     * Get complete PO details with items and history
     */
    getById: async (poId: number): Promise<PODetailResponse> => {
        const response = await apiClient.get(`/po/${poId}`);
        return response.data;
    },

    /**
     * Update purchase order
     */
    update: async (poId: number, data: POUpdateRequest): Promise<PODetailResponse> => {
        const response = await apiClient.put(`/po/${poId}/update`, data);
        return response.data;
    },

    /**
     * Send PO to farm via email
     */
    send: async (poId: number): Promise<{ message: string; status: string }> => {
        const response = await apiClient.post(`/po/${poId}/send`);
        return response.data;
    },

    /**
     * List purchase orders with filters and pagination
     */
    list: async (params: POListParams): Promise<POListResponse> => {
        const response = await apiClient.get('/po/list', { params });
        return response.data;
    },

    /**
     * Export selected POs to Zoho Books format (admin only)
     */
    exportToZoho: async (poIds: number[]): Promise<Blob> => {
        const response = await apiClient.post(
            '/po/export-zoho',
            { po_ids: poIds },
            { responseType: 'blob' }
        );
        return response.data;
    },

    /**
     * Generate printable PO PDF
     */
    generatePDF: async (poId: number): Promise<Blob> => {
        const response = await apiClient.get(`/po/${poId}/pdf`, { responseType: 'blob' });
        return response.data;
    },

    // ============================================================================
    // VENDOR PRICING MANAGEMENT (ADMIN ONLY)
    // ============================================================================

    /**
     * Add or update vendor-item pricing (admin only)
     */
    addVendorPrice: async (data: VendorPricingRequest): Promise<PriceHistoryResponse> => {
        const response = await apiClient.post('/vendor-pricing/manage', data);
        return response.data;
    },

    /**
     * Get price history for vendor-item combinations (admin only)
     */
    getPriceHistory: async (vendorId: number, itemId?: number): Promise<PriceHistoryResponse[]> => {
        const response = await apiClient.get('/vendor-pricing/history', {
            params: { vendor_id: vendorId, item_id: itemId }
        });
        return response.data;
    },

    /**
     * Get all active vendor-item prices for a specific date
     */
    getActivePrices: async (vendorId: number, date?: string): Promise<ActivePriceResponse[]> => {
        const response = await apiClient.get('/vendor-pricing/active', {
            params: { vendor_id: vendorId, price_date: date }
        });
        return response.data;
    },
};

export default purchaseOrdersAPI;

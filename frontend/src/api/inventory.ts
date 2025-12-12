/**
 * ================================================================================
 * Inventory API Client
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-12
 *
 * API client for Inventory Management module - Stock tracking and management
 * ================================================================================
 */

import apiClient from './client';

// ============================================================================
// TYPES
// ============================================================================

export interface InventoryItem {
    id: number;
    item_id: number;
    item_name: string;
    item_sku: string;
    batch_id: number;
    batch_number: string;
    location: string;
    quantity: number;
    grade?: string;
    status: string;
    shelf_life_days?: number;
    entry_date: string;
    expiry_date?: string;
    days_until_expiry?: number;
    created_at: string;
    updated_at: string;
}

export interface InventoryListParams {
    location?: string;
    status?: string;
    item_id?: number;
    batch_id?: number;
    grade?: string;
    expiring_within_days?: number;
    page?: number;
    limit?: number;
}

export interface InventoryListResponse {
    items: InventoryItem[];
    total: number;
    page: number;
    limit: number;
}

export interface ManualStockEntryRequest {
    item_id: number;
    batch_id: number;
    location: string;
    quantity: number;
    grade?: string;
    shelf_life_days?: number;
    entry_date?: string;
}

export interface BatchInventoryResponse {
    batch_id: number;
    batch_number: string;
    item_id: number;
    item_name: string;
    total_quantity: number;
    locations: {
        location: string;
        quantity: number;
        status: string;
        grade?: string;
    }[];
    movements: InventoryMovement[];
}

export interface InventoryMovement {
    id: number;
    movement_type: string;
    quantity: number;
    from_location?: string;
    to_location?: string;
    reference_type?: string;
    reference_id?: number;
    notes?: string;
    created_by: string;
    created_at: string;
}

export interface LocationTransferRequest {
    batch_id: number;
    item_id: number;
    from_location: string;
    to_location: string;
    quantity: number;
}

export interface StockAvailabilityQuery {
    item_id: number;
    quantity: number;
    location?: string;
    grade?: string;
}

export interface StockAvailabilityResponse {
    available: boolean;
    item_id: number;
    item_name: string;
    required_quantity: number;
    current_stock: number;
    allocated_stock: number;
    net_available: number;
    shortage: number;
    locations: {
        location: string;
        available: number;
    }[];
}

export interface InventoryAdjustmentRequest {
    item_id: number;
    batch_id?: number;
    location: string;
    adjustment_type: 'increase' | 'decrease' | 'correction';
    quantity: number;
    reason: string;
    photo_urls?: string[];
}

export interface InventoryAdjustment {
    id: number;
    item_id: number;
    item_name: string;
    batch_id?: number;
    batch_number?: string;
    location: string;
    adjustment_type: string;
    quantity: number;
    reason: string;
    approval_status: string;
    approved_by?: string;
    approved_at?: string;
    rejection_reason?: string;
    photo_urls?: string[];
    created_by: string;
    created_at: string;
}

export interface InventoryAdjustmentApproval {
    approved: boolean;
    notes?: string;
}

export interface ReorderLevelConfig {
    item_id: number;
    location: string;
    reorder_quantity: number;
    alert_threshold: number;
    is_active: boolean;
}

export interface LowStockAlert {
    item_id: number;
    item_name: string;
    location: string;
    current_stock: number;
    alert_threshold: number;
    reorder_quantity: number;
    shortage: number;
}

export interface ExpiringItem {
    id: number;
    item_id: number;
    item_name: string;
    batch_id: number;
    batch_number: string;
    location: string;
    quantity: number;
    expiry_date: string;
    days_until_expiry: number;
    urgency: 'critical' | 'warning' | 'normal';
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

export const inventoryAPI = {
    /**
     * Add stock manually (testing endpoint)
     */
    addStock: async (data: ManualStockEntryRequest): Promise<InventoryItem> => {
        const response = await apiClient.post('/inventory/add', data);
        return response.data;
    },

    /**
     * List inventory with filters and pagination
     */
    list: async (params: InventoryListParams): Promise<InventoryListResponse> => {
        const response = await apiClient.get('/inventory/list', { params });
        return response.data;
    },

    /**
     * Get batch-wise inventory view
     */
    getBatchInventory: async (batchId: number): Promise<BatchInventoryResponse> => {
        const response = await apiClient.get(`/inventory/by-batch/${batchId}`);
        return response.data;
    },

    /**
     * Check stock availability
     */
    checkAvailability: async (params: StockAvailabilityQuery): Promise<StockAvailabilityResponse> => {
        const response = await apiClient.get('/inventory/availability', { params });
        return response.data;
    },

    /**
     * Get low stock items
     */
    getLowStock: async (): Promise<LowStockAlert[]> => {
        const response = await apiClient.get('/inventory/low-stock');
        return response.data;
    },

    /**
     * Get expiring items
     */
    getExpiringItems: async (daysThreshold: number = 7): Promise<ExpiringItem[]> => {
        const response = await apiClient.get('/inventory/expiring', {
            params: { days_threshold: daysThreshold }
        });
        return response.data;
    },

    /**
     * Transfer stock between locations
     */
    transferLocation: async (data: LocationTransferRequest): Promise<any> => {
        const response = await apiClient.post('/inventory/transfer', data);
        return response.data;
    },

    /**
     * Create stock adjustment request
     */
    createAdjustment: async (data: InventoryAdjustmentRequest): Promise<InventoryAdjustment> => {
        const response = await apiClient.post('/inventory/adjust', data);
        return response.data;
    },

    /**
     * Approve/reject adjustment (admin only)
     */
    approveAdjustment: async (adjustmentId: number, data: InventoryAdjustmentApproval): Promise<InventoryAdjustment> => {
        const response = await apiClient.put(`/inventory/adjust/${adjustmentId}/approve`, data);
        return response.data;
    },

    /**
     * List adjustments
     */
    listAdjustments: async (params: { approval_status?: string; page?: number; limit?: number }): Promise<any> => {
        const response = await apiClient.get('/inventory/adjustments', { params });
        return response.data;
    },

    /**
     * Configure reorder level
     */
    configureReorderLevel: async (data: ReorderLevelConfig): Promise<any> => {
        const response = await apiClient.post('/inventory/reorder-level', data);
        return response.data;
    },

    /**
     * Generate current stock report
     */
    generateCurrentStockReport: async (params: {
        location?: string;
        item_id?: number;
        status?: string;
        include_zero_stock?: boolean;
    }): Promise<any> => {
        const response = await apiClient.get('/inventory/reports/current-stock', { params });
        return response.data;
    },

    /**
     * Generate stock movement report
     */
    generateMovementReport: async (params: {
        date_from?: string;
        date_to?: string;
        movement_type?: string;
        location?: string;
        item_id?: number;
    }): Promise<any> => {
        const response = await apiClient.get('/inventory/reports/movements', { params });
        return response.data;
    },

    /**
     * Generate batch age report
     */
    generateBatchAgeReport: async (): Promise<any> => {
        const response = await apiClient.get('/inventory/reports/batch-age');
        return response.data;
    },
};

export default inventoryAPI;

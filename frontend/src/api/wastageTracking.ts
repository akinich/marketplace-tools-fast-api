/**
 * ================================================================================
 * Wastage Tracking API Client
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * API client for Wastage Tracking module - Centralized wastage data aggregation,
 * cost tracking, and analytics across the supply chain.
 * ================================================================================
 */

import apiClient from './client';

// ============================================================================
// TYPES
// ============================================================================

export enum WastageStage {
    RECEIVING = 'receiving',
    GRADING = 'grading',
    PACKING = 'packing',
    COLD_STORAGE = 'cold_storage',
    CUSTOMER = 'customer',
}

export enum WastageType {
    DAMAGE = 'damage',
    REJECT = 'reject',
    QC = 'qc',
    OVERFILL = 'overfill',
    PARTIAL_DAMAGE = 'partial_damage',
    FULL_LOSS = 'full_loss',
    CUSTOMER_CLAIM = 'customer_claim',
}

export enum CostAllocation {
    FARM = 'farm',
    US = 'us',
}

export enum AlertLevel {
    CRITICAL = 'critical',
    WARNING = 'warning',
    INFO = 'info',
}

export interface PhotoData {
    file?: File;
    url?: string;
    path?: string;
    filename?: string;
}

export interface LogWastageRequest {
    batch_number: string;
    stage: WastageStage | string;
    wastage_type: WastageType | string;
    item_name: string;
    quantity: number;
    unit: string;
    cost_allocation: CostAllocation | string;
    estimated_cost?: number;
    reason?: string;
    notes?: string;
    location?: string;
    po_id?: number;
    grn_id?: number;
    so_id?: number;
    ticket_id?: number;
}

export interface WastageEventResponse {
    wastage_event_id: number;
    event_id: string;
    batch_number: string;
    photos_uploaded: number;
    created_at: string;
}

export interface WastageEvent {
    event_id: string;
    stage: string;
    wastage_type: string;
    quantity: number;
    unit: string;
    cost_allocation: string;
    estimated_cost: number;
    reason?: string;
    notes?: string;
    photos: string[];
    created_at: string;
    created_by: string;
}

export interface WastageByBatchResponse {
    batch_number: string;
    total_wastage_events: number;
    total_quantity_wasted: number;
    total_estimated_cost: number;
    cost_breakdown: {
        farm: number;
        us: number;
    };
    events: WastageEvent[];
}

export interface FarmAnalytics {
    farm_name: string;
    total_wastage_kg: number;
    total_cost: number;
    wastage_percentage: number;
    breakdown_by_type: Record<string, number>;
    breakdown_by_stage: Record<string, number>;
}

export interface WastageAnalyticsByFarmResponse {
    date_range: {
        from: string;
        to: string;
    };
    farms: FarmAnalytics[];
}

export interface StageAnalytics {
    stage: string;
    stage_name: string;
    total_wastage_kg: number;
    total_cost: number;
    percentage_of_total: number;
    event_count: number;
    avg_wastage_per_event: number;
    top_reasons: Array<{ reason: string; count: number }>;
}

export interface WastageAnalyticsByStageResponse {
    date_range: {
        from: string;
        to: string;
    };
    stages: StageAnalytics[];
}

export interface ProductAnalytics {
    item_name: string;
    total_wastage_kg: number;
    total_cost: number;
    wastage_percentage: number;
    problematic_stages: Array<{ stage: string; wastage_kg: number }>;
}

export interface WastageAnalyticsByProductResponse {
    date_range: {
        from: string;
        to: string;
    };
    products: ProductAnalytics[];
}

export interface TrendDataPoint {
    date: string;
    total_wastage_kg: number;
    total_cost: number;
    event_count: number;
}

export interface WastageTrendsResponse {
    granularity: string;
    date_range: {
        from: string;
        to: string;
    };
    data_points: TrendDataPoint[];
}

export interface WastageCategory {
    id: number;
    stage: string;
    wastage_type: string;
    reason: string;
    description?: string;
}

export interface CategoriesListResponse {
    categories: WastageCategory[];
}

export interface WastageThreshold {
    id: number;
    scope_type: string;
    scope_value?: string;
    stage?: string;
    threshold_percentage: number;
    alert_level: string;
    is_active: boolean;
}

export interface ThresholdsListResponse {
    thresholds: WastageThreshold[];
}

export interface UpdateThresholdRequest {
    threshold_percentage?: number;
    alert_level?: AlertLevel | string;
    is_active?: boolean;
}

export interface WastageAlert {
    alert_level: string;
    message: string;
    farm?: string;
    stage?: string;
    current_percentage: number;
    threshold: number;
    period: string;
}

export interface AlertsListResponse {
    alerts: WastageAlert[];
}

export interface RepackRequest {
    parent_batch_number: string;
    wastage_event_id?: number;
    damaged_quantity: number;
    repacked_quantity: number;
    wastage_in_repacking?: number;
    reason: string;
    notes?: string;
}

export interface RepackBatchResponse {
    parent_batch: string;
    new_batch_number: string;
    new_batch_id: number;
    repacking_id: number;
    repacked_quantity: number;
    created_at: string;
}

// ============================================================================
// API CLIENT
// ============================================================================

export const wastageTrackingAPI = {
    /**
     * Log a new wastage event with photos
     */
    logWastage: async (
        data: LogWastageRequest,
        photos: File[]
    ): Promise<WastageEventResponse> => {
        const formData = new FormData();
        formData.append('data', JSON.stringify(data));

        photos.forEach((photo) => {
            formData.append('photos', photo);
        });

        const response = await apiClient.post('/wastage/log', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Get all wastage events for a specific batch
     */
    getWastageByBatch: async (batchNumber: string): Promise<WastageByBatchResponse> => {
        const response = await apiClient.get(`/wastage/by-batch/${encodeURIComponent(batchNumber)}`);
        return response.data;
    },

    /**
     * Get wastage analytics by farm
     */
    getAnalyticsByFarm: async (params?: {
        date_from?: string;
        date_to?: string;
        farm_id?: number;
    }): Promise<WastageAnalyticsByFarmResponse> => {
        const response = await apiClient.get('/wastage/analytics/by-farm', { params });
        return response.data;
    },

    /**
     * Get wastage analytics by stage
     */
    getAnalyticsByStage: async (params?: {
        date_from?: string;
        date_to?: string;
    }): Promise<WastageAnalyticsByStageResponse> => {
        const response = await apiClient.get('/wastage/analytics/by-stage', { params });
        return response.data;
    },

    /**
     * Get wastage analytics by product
     */
    getAnalyticsByProduct: async (params?: {
        date_from?: string;
        date_to?: string;
        item_name?: string;
    }): Promise<WastageAnalyticsByProductResponse> => {
        const response = await apiClient.get('/wastage/analytics/by-product', { params });
        return response.data;
    },

    /**
     * Get wastage trends over time
     */
    getTrends: async (params?: {
        date_from?: string;
        date_to?: string;
        granularity?: 'daily' | 'weekly' | 'monthly';
    }): Promise<WastageTrendsResponse> => {
        const response = await apiClient.get('/wastage/analytics/trends', { params });
        return response.data;
    },

    /**
     * Initiate repacking workflow
     */
    initiateRepack: async (
        data: RepackRequest,
        photos: File[]
    ): Promise<RepackBatchResponse> => {
        const formData = new FormData();
        formData.append('data', JSON.stringify(data));

        photos.forEach((photo) => {
            formData.append('photos', photo);
        });

        const response = await apiClient.post('/wastage/repack', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Get wastage categories for dropdowns
     */
    getCategories: async (stage?: string): Promise<CategoriesListResponse> => {
        const response = await apiClient.get('/wastage/categories', {
            params: stage ? { stage } : undefined,
        });
        return response.data;
    },

    /**
     * Get wastage thresholds (admin only)
     */
    getThresholds: async (): Promise<ThresholdsListResponse> => {
        const response = await apiClient.get('/wastage/thresholds');
        return response.data;
    },

    /**
     * Update wastage threshold (admin only)
     */
    updateThreshold: async (
        id: number,
        data: UpdateThresholdRequest
    ): Promise<WastageThreshold> => {
        const response = await apiClient.put(`/wastage/thresholds/${id}`, data);
        return response.data;
    },

    /**
     * Get current wastage alerts
     */
    getAlerts: async (): Promise<AlertsListResponse> => {
        const response = await apiClient.get('/wastage/alerts');
        return response.data;
    },
};

export default wastageTrackingAPI;

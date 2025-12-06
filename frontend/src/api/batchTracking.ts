/**
 * ================================================================================
 * Batch Tracking API Client
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-04
 *
 * API client for Batch Tracking module - Complete traceability from farm to customer
 * ================================================================================
 */

import apiClient from './client';

// ============================================================================
// TYPES
// ============================================================================

export enum BatchStatus {
  ORDERED = 'ordered',
  RECEIVED = 'received',
  IN_GRADING = 'in_grading',
  IN_PACKING = 'in_packing',
  IN_INVENTORY = 'in_inventory',
  ALLOCATED = 'allocated',
  IN_TRANSIT = 'in_transit',
  DELIVERED = 'delivered',
  ARCHIVED = 'archived',
}

export enum BatchStage {
  PO = 'po',
  GRN = 'grn',
  GRADING = 'grading',
  PACKING = 'packing',
  INVENTORY = 'inventory',
  ALLOCATION = 'allocation',
  DELIVERY = 'delivery',
}

export enum BatchEventType {
  CREATED = 'created',
  RECEIVED = 'received',
  GRADED = 'graded',
  PACKED = 'packed',
  MOVED_TO_INVENTORY = 'moved_to_inventory',
  ALLOCATED = 'allocated',
  IN_TRANSIT = 'in_transit',
  DELIVERED = 'delivered',
  STATUS_CHANGED = 'status_changed',
  REPACKED = 'repacked',
}

export interface GenerateBatchRequest {
  po_id?: number;
  grn_id?: number;
  created_by: string;
}

export interface BatchResponse {
  batch_id: number;
  batch_number: string;
  status: string;
  created_at: string;
}

export interface BatchDocumentLink {
  document_type: string;
  document_id: number;
  document_number?: string;
}

export interface BatchHistoryEvent {
  stage: string;
  event_type: string;
  event_details?: Record<string, any>;
  old_status?: string;
  new_status?: string;
  location?: string;
  created_at: string;
  created_by_name?: string;
}

export interface BatchDetailResponse {
  batch_id: number;
  batch_number: string;
  status: string;
  is_repacked: boolean;
  parent_batch_number?: string;
  child_batch_number?: string;
  po_id?: number;
  grn_id?: number;
  created_at: string;
  archived_at?: string;
  documents: BatchDocumentLink[];
  history: BatchHistoryEvent[];
}

export interface BatchTimelineStage {
  stage: string;
  stage_name: string;
  timestamp?: string;
  status: string; // completed, in_progress, pending
  details?: Record<string, any>;
}

export interface BatchTimelineResponse {
  batch_number: string;
  timeline: BatchTimelineStage[];
}

export interface SearchBatchesRequest {
  batch_number?: string;
  po_number?: string;
  grn_number?: string;
  so_number?: string;
  farm_name?: string;
  item_name?: string;
  customer_name?: string;
  status?: BatchStatus;
  date_from?: string;
  date_to?: string;
  is_archived?: boolean;
  is_repacked?: boolean;
  page?: number;
  limit?: number;
}

export interface BatchSearchResult {
  batch_id: number;
  batch_number: string;
  status: string;
  is_repacked: boolean;
  created_at: string;
  farm?: string;
  current_location?: string;
}

export interface BatchSearchResponse {
  batches: BatchSearchResult[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface RepackBatchRequest {
  reason: string;
  damaged_quantity: number;
  repacked_quantity: number;
  photos?: string[];
  notes?: string;
}

export interface RepackBatchResponse {
  parent_batch: string;
  new_batch_number: string;
  new_batch_id: number;
  status: string;
  created_at: string;
}

export interface AddBatchHistoryRequest {
  stage: BatchStage;
  event_type: BatchEventType;
  event_details?: Record<string, any>;
  new_status?: BatchStatus;
  location?: string;
}

export interface BatchStatsResponse {
  total_batches: number;
  active_batches: number;
  archived_batches: number;
  repacked_batches: number;
  by_status: Record<string, number>;
}

// ============================================================================
// API CLIENT
// ============================================================================

export const batchTrackingAPI = {
  /**
   * Generate new batch number
   */
  generateBatch: async (data: GenerateBatchRequest): Promise<BatchResponse> => {
    const response = await apiClient.post('/batches/generate', data);
    return response.data;
  },

  /**
   * Get complete batch details with history and documents
   */
  getBatchDetails: async (batchNumber: string): Promise<BatchDetailResponse> => {
    const response = await apiClient.get(`/batches/${batchNumber}`);
    return response.data;
  },

  /**
   * Get visual timeline of batch journey
   */
  getBatchTimeline: async (batchNumber: string): Promise<BatchTimelineResponse> => {
    const response = await apiClient.get(`/batches/${batchNumber}/timeline`);
    return response.data;
  },

  /**
   * Search batches with filters and pagination
   */
  searchBatches: async (filters: SearchBatchesRequest): Promise<BatchSearchResponse> => {
    const response = await apiClient.post('/batches/search', filters);
    return response.data;
  },

  /**
   * Create repacked batch from damaged items
   */
  repackBatch: async (
    batchNumber: string,
    data: RepackBatchRequest
  ): Promise<RepackBatchResponse> => {
    const response = await apiClient.post(`/batches/${batchNumber}/repack`, data);
    return response.data;
  },

  /**
   * Get all active (non-archived) batches
   */
  getActiveBatches: async (params?: {
    status?: string;
    page?: number;
    limit?: number;
  }): Promise<BatchSearchResponse> => {
    const response = await apiClient.get('/batches/active', { params });
    return response.data;
  },

  /**
   * Archive a batch (admin only)
   */
  archiveBatch: async (batchNumber: string): Promise<{ batch_number: string; archived_at: string; status: string }> => {
    const response = await apiClient.post(`/batches/${batchNumber}/archive`);
    return response.data;
  },

  /**
   * Add event to batch history (called by other modules)
   */
  addBatchHistory: async (
    batchNumber: string,
    event: AddBatchHistoryRequest
  ): Promise<{ history_id: number; batch_number: string; created_at: string }> => {
    const response = await apiClient.post(`/batches/${batchNumber}/history`, event);
    return response.data;
  },

  /**
   * Get batch statistics summary
   */
  getStats: async (): Promise<BatchStatsResponse> => {
    const response = await apiClient.get('/batches/stats/summary');
    return response.data;
  },
};

export default batchTrackingAPI;

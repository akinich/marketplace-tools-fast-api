import api from './index';

// ============================================================================
// TYPES
// ============================================================================

export interface GRNItemUpdate {
    item_id: number;
    gross_received: number;
    damage: number;
    reject: number;
    damage_cost_allocation?: 'farm' | 'us';
    reject_cost_allocation?: 'farm' | 'us';
    notes?: string;
}

export interface GRNUpdateRequest {
    transport_method?: string;
    number_of_boxes?: number;
    receiving_time?: string;  // HH:MM:SS
    receiving_date?: string;   // YYYY-MM-DD
    receiver_id?: number;
    items?: GRNItemUpdate[];
    notes?: string;
}

export interface GRNItemResponse extends GRNItemUpdate {
    id: number;
    item_name: string;
    final_accepted: number;
    added_to_po: boolean;
    expected_quantity: number; // Added based on context in pages
}

export interface GRNPhotoResponse {
    id: number;
    item_id: number;
    item_name: string;
    photo_type: 'damage' | 'reject';
    photo_url: string;
    uploaded_by: number;
    uploaded_by_name: string;
    uploaded_at: string;
    file_size: number;
    notes?: string;
}

export interface GRNResponse {
    id: number;
    grn_number: string;
    po_id: number;
    po_number: string;
    batch_id: number;
    batch_number: string;
    vendor_id: number;
    vendor_name: string;
    transport_method?: string;
    number_of_boxes?: number;
    receiving_time?: string;
    receiving_date: string;
    status: string;
    receiver_id?: number;
    receiver_name?: string;
    created_at: string;
    completed_at?: string;
    notes?: string;
}

export interface EditHistory {
    field_name: string;
    old_value?: string;
    new_value: string;
    edited_by: number;
    edited_by_name: string;
    edited_at: string;
}

export interface GRNDetailResponse extends GRNResponse {
    items: GRNItemResponse[];
    photos: GRNPhotoResponse[];
    edit_history: EditHistory[];
}

export interface GRNListParams {
    status?: string;
    po_id?: number;
    batch_number?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
    limit?: number;
}

export interface GRNListResponse {
    grns: GRNResponse[];
    total: number;
    page: number;
    limit: number;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

export const grnAPI = {
    // GRN Management
    generate: (poId: number) =>
        api.post<GRNResponse>('/grn/generate', { po_id: poId }),

    getById: (grnId: number) =>
        api.get<GRNDetailResponse>(`/grn/${grnId}`),

    update: (grnId: number, data: GRNUpdateRequest) =>
        api.put<GRNResponse>(`/grn/${grnId}/update`, data),

    finalize: (grnId: number) =>
        api.post<GRNResponse>(`/grn/${grnId}/finalize`),

    list: (params: GRNListParams) =>
        api.get<GRNListResponse>('/grn/list', { params }),

    getByPO: (poId: number) =>
        api.get<GRNResponse[]>(`/grn/by-po/${poId}`),

    getByBatch: (batchNumber: string) =>
        api.get<GRNDetailResponse>(`/grn/by-batch/${batchNumber}`),

    generateBlankPDF: (grnId: number) =>
        api.get(`/grn/${grnId}/print`, { responseType: 'blob' }),

    // Photo Management
    uploadPhotos: (grnId: number, itemId: number, photoType: 'damage' | 'reject', files: File[]) => {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));

        return api.post<string[]>(
            `/grn/${grnId}/photos/upload?item_id=${itemId}&photo_type=${photoType}`,
            formData,
            {
                headers: { 'Content-Type': 'multipart/form-data' }
            }
        );
    },

    deletePhoto: (photoId: number) =>
        api.delete(`/grn/photos/${photoId}`),
};

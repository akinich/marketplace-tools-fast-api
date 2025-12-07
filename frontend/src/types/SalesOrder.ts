/**
 * Sales Order Management Types
 * Version: 1.0.0
 * Created: 2024-12-07
 */

export enum SalesOrderStatus {
    DRAFT = 'draft',
    CONFIRMED = 'confirmed',
    PACKING = 'packing',
    SHIPPED = 'shipped',
    COMPLETED = 'completed',
    CANCELLED = 'cancelled',
    EXPORTED_TO_ZOHO = 'exported_to_zoho',
}

export enum OrderSource {
    MANUAL = 'manual',
    WHATSAPP = 'whatsapp',
    EMAIL = 'email',
    WEBSITE = 'website',
}

export enum PriceSource {
    CUSTOMER = 'customer',
    ITEM_RATE = 'item_rate',
    MANUAL = 'manual',
}

export interface SOItem {
    id?: number;
    item_id: number;
    item_name: string;
    item_sku?: string;
    quantity: number;
    unit_price: number;
    price_source: PriceSource;
    line_total: number;
    notes?: string;
}

export interface StatusChange {
    from_status?: string;
    to_status: string;
    changed_by?: string;
    changed_at: string;
    notes?: string;
}

export interface SalesOrder {
    id: number;
    so_number: string;
    customer_id: number;
    customer_name: string;
    order_date: string;
    delivery_date?: string;
    status: SalesOrderStatus;
    order_source: string;
    total_amount: number;
    notes?: string;
    items: SOItem[];
    status_history?: StatusChange[];
    created_at: string;
    updated_at: string;
}

export interface CreateSORequest {
    customer_id: number;
    so_number?: string;
    order_date: string;
    delivery_date?: string;
    order_source?: string;
    items: {
        item_id: number;
        quantity: number;
        unit_price?: number;
        notes?: string;
    }[];
    notes?: string;
}

export interface UpdateSORequest {
    customer_id?: number;
    order_date?: string;
    delivery_date?: string;
    order_source?: string;
    items?: {
        item_id: number;
        quantity: number;
        unit_price?: number;
        notes?: string;
    }[];
    notes?: string;
}

export interface CustomerPricing {
    id: number;
    customer_id: number;
    customer_name?: string;
    item_id: number;
    item_name?: string;
    price: number;
    effective_from: string;
    effective_to?: string;
    notes?: string;
    created_by?: string;
    created_at?: string;
}

export interface SalesOrderListFilters {
    status?: string | null;
    customer_id?: number | null;
    from_date?: string | null;
    to_date?: string | null;
    page?: number;
    limit?: number;
}

export interface SalesOrderListResponse {
    orders: SalesOrder[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

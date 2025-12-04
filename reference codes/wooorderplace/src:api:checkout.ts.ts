// src/api/checkout.ts
import { apiClient } from "./client";

export interface LineItemPayload {
    productId: number;
    quantity: number;
    variationId?: number;
}

export interface WooOrder {
    id: number;
    status: string;
    total: string;
    // other fields from WooCommerce are also present but we only type what we need
}

export async function checkout(
    supabaseUserId: string,
    items: LineItemPayload[]
): Promise<WooOrder> {
    const payload = {
        supabase_user_id: supabaseUserId,
        line_items: items.map((item) => ({
            product_id: item.productId,
            quantity: item.quantity,
            variation_id: item.variationId,
        })),
    };

    return apiClient.post<WooOrder>("/checkout", payload);
}

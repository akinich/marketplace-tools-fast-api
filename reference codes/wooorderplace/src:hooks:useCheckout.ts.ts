// src/hooks/useCheckout.ts
import { useState } from "react";
import { checkout, LineItemPayload, WooOrder } from "../api/checkout";

interface UseCheckoutOptions {
    supabaseUserId: string | null | undefined;
}

export function useCheckout({ supabaseUserId }: UseCheckoutOptions) {
    const [loading, setLoading] = useState(false);
    const [order, setOrder] = useState<WooOrder | null>(null);
    const [error, setError] = useState<string | null>(null);

    const placeOrder = async (items: LineItemPayload[]) => {
        if (!supabaseUserId) {
            setError("User not authenticated.");
            return;
        }

        try {
            setLoading(true);
            setError(null);

            const result = await checkout(supabaseUserId, items);
            setOrder(result);
        } catch (e: any) {
            setError(e.message ?? "Unknown error");
        } finally {
            setLoading(false);
        }
    };

    return { placeOrder, loading, order, error };
}

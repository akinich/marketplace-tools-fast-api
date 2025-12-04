// src/components/CheckoutButton.tsx
import React from "react";
import { useCheckout } from "../hooks/useCheckout";
import type { LineItemPayload } from "../api/checkout";

// Replace this with your actual Supabase auth hook
// e.g. `const { data: { user } } = useSupabaseClient().auth.getUser()`
const useMockSupabaseUser = () => {
    // Just for demo purposes
    return { id: "00000000-0000-0000-0000-000000000000" };
};

export const CheckoutButton: React.FC = () => {
    const user = useMockSupabaseUser();
    const { placeOrder, loading, order, error } = useCheckout({
        supabaseUserId: user?.id,
    });

    // Example: your React app’s cart items with Woo product IDs
    const exampleCart: LineItemPayload[] = [
        { productId: 10, quantity: 2 },
        { productId: 42, quantity: 1 },
    ];

    const handleClick = () => {
        placeOrder(exampleCart);
    };

    return (
        <div style={{ padding: "1rem", border: "1px solid #ccc" }}>
            <button onClick={handleClick} disabled={loading}>
                {loading ? "Placing order..." : "Place order"}
            </button>

            {error && (
                <div style={{ color: "red", marginTop: "0.5rem" }}>
                    Error: {error}
                </div>
            )}

            {order && (
                <div style={{ marginTop: "0.5rem" }}>
                    <p>Order created!</p>
                    <p>
                        Woo Order ID: <strong>{order.id}</strong>
                    </p>
                    <p>Status: {order.status}</p>
                    <p>Total: {order.total}</p>
                </div>
            )}
        </div>
    );
};

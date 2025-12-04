# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from .models import CheckoutRequest, WooOrder
from .supabase_client import get_wc_customer_id_from_supabase
from .wc_client import wc_client

app = FastAPI(
    title="WooCommerce Checkout API",
    version="1.0.0",
)

# Adjust origins for your React app on Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/checkout", response_model=WooOrder)
def create_order(payload: CheckoutRequest) -> Any:
    # 1. Resolve WooCommerce customer ID from Supabase user ID
    wc_customer_id = get_wc_customer_id_from_supabase(payload.supabase_user_id)
    if wc_customer_id is None:
        # You could create a WooCommerce customer here instead of erroring
        raise HTTPException(
            status_code=400,
            detail="No WooCommerce customer mapped to this Supabase user.",
        )

    # 2. Build line items in the shape WooCommerce expects
    wc_line_items = []
    for item in payload.line_items:
        li: Dict[str, Any] = {
            "product_id": item.product_id,
            "quantity": item.quantity,
        }
        if item.variation_id:
            li["variation_id"] = item.variation_id
        wc_line_items.append(li)

    # 3. Build the WooCommerce order payload
    order_data: Dict[str, Any] = {
        "customer_id": wc_customer_id,
        "set_paid": False,  # or True if you’ve already taken payment elsewhere
        "line_items": wc_line_items,
        # You can add billing/shipping info here.
    }

    # 4. Create order in WooCommerce
    try:
        order = wc_client.create_order(order_data)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 5. Optionally: store order info into Supabase `orders` table
    # (you can add that later; keeping this sample minimal)

    return order

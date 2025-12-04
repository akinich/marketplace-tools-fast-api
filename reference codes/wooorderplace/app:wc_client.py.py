# app/wc_client.py
from typing import Any, Dict, List
import requests
from .config import get_settings

settings = get_settings()


class WooCommerceClient:
    def __init__(self) -> None:
        self.base_url = settings.wc_store_url.rstrip("/")
        self.auth = (settings.wc_consumer_key, settings.wc_consumer_secret)

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/wp-json/wc/v3/orders"
        resp = requests.post(url, auth=self.auth, json=order_data, timeout=20)
        if not resp.ok:
            raise RuntimeError(
                f"WooCommerce order creation failed: {resp.status_code} {resp.text}"
            )
        return resp.json()

    # Optional: you can add more methods like get_products, get_customer, etc.


wc_client = WooCommerceClient()

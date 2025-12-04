# app/supabase_client.py
from typing import Optional
from supabase import create_client, Client
from .config import get_settings

_settings = get_settings()
_supabase: Client = create_client(
    _settings.supabase_url,
    _settings.supabase_anon_key,
)


def get_wc_customer_id_from_supabase(supabase_user_id: str) -> Optional[int]:
    """
    Fetch WooCommerce customer ID mapped to this Supabase user.
    Assumes there is a 'users' table with:
      - id (uuid) primary key
      - wc_customer_id (int, nullable)
    """
    response = (
        _supabase.table("users")
        .select("wc_customer_id")
        .eq("id", supabase_user_id)
        .single()
        .execute()
    )

    data = response.data
    if not data:
        return None

    return data.get("wc_customer_id")

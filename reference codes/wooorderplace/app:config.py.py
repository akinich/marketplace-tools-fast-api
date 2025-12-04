# app/config.py
import os
from functools import lru_cache
from pydantic import BaseSettings, AnyHttpUrl, ValidationError


class Settings(BaseSettings):
    # WooCommerce
    wc_store_url: AnyHttpUrl
    wc_consumer_key: str
    wc_consumer_secret: str

    # Supabase
    supabase_url: AnyHttpUrl
    supabase_anon_key: str  # or service role key depending on usage

    class Config:
        env_prefix = ""  # use exact names
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings(
            wc_store_url=os.environ["WC_STORE_URL"],
            wc_consumer_key=os.environ["WC_CONSUMER_KEY"],
            wc_consumer_secret=os.environ["WC_CONSUMER_SECRET"],
            supabase_url=os.environ["SUPABASE_URL"],
            supabase_anon_key=os.environ["SUPABASE_KEY"],
        )
    except KeyError as e:
        raise RuntimeError(f"Missing environment variable: {e}") from e
    except ValidationError as e:
        raise RuntimeError(f"Config validation error: {e}") from e

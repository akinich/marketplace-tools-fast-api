"""
================================================================================
Zoho Books API Client
================================================================================
Version: 1.0.0
Created: 2025-12-02

Service for authenticating and fetching data from Zoho Books API
================================================================================
"""

import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.services import settings_service
from app.database import get_db

logger = logging.getLogger(__name__)

# Token cache (in-memory, expires after 50 minutes)
_token_cache = {
    "access_token": None,
    "expires_at": None
}


async def get_access_token() -> str:
    """
    Get Zoho Books access token using refresh token
    Caches token for 50 minutes to avoid unnecessary API calls
    
    Returns:
        Access token string
    """
    # Check if cached token is still valid
    if _token_cache["access_token"] and _token_cache["expires_at"]:
        if datetime.utcnow() < _token_cache["expires_at"]:
            logger.debug("Using cached Zoho access token")
            return _token_cache["access_token"]
    
    try:
        # Get credentials from database
        pool = get_db()
        async with pool.acquire() as conn:
            client_id = await settings_service.get_setting(conn, "zoho.client_id")
            client_secret = await settings_service.get_setting(conn, "zoho.client_secret")
            refresh_token = await settings_service.get_setting(conn, "zoho.refresh_token")
        
        if not all([client_id, client_secret, refresh_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zoho Books API credentials not configured. Please set zoho.client_id, zoho.client_secret, and zoho.refresh_token in system settings."
            )
        
        # Exchange refresh token for access token
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        payload = {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        
        access_token = data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to obtain access token from Zoho"
            )
        
        # Cache token for 50 minutes (Zoho tokens expire after 1 hour)
        _token_cache["access_token"] = access_token
        _token_cache["expires_at"] = datetime.utcnow() + timedelta(minutes=50)
        
        logger.info("Successfully obtained new Zoho access token")
        return access_token
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Zoho access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate with Zoho Books: {str(e)}"
        )


async def fetch_all_items() -> List[Dict]:
    """
    Fetch all items from Zoho Books with automatic pagination
    
    Returns:
        List of item dictionaries
    """
    try:
        access_token = await get_access_token()
        
        # Get organization ID and base URL from settings
        pool = get_db()
        async with pool.acquire() as conn:
            organization_id = await settings_service.get_setting(conn, "zoho.organization_id")
            base_url = await settings_service.get_setting(conn, "zoho.base_url")
        
        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zoho organization_id not configured in system settings"
            )
        
        if not base_url:
            base_url = "https://books.zoho.com/api/v3"
        
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        items = []
        page = 1
        
        async with httpx.AsyncClient() as client:
            while True:
                logger.info(f"Fetching Zoho items page {page}...")
                
                response = await client.get(
                    f"{base_url}/items",
                    headers=headers,
                    params={
                        "organization_id": organization_id,
                        "page": page
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Zoho API error: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Zoho Books API error: {response.text}"
                    )
                
                data = response.json()
                page_items = data.get("items", [])
                
                if not page_items:
                    break
                
                items.extend(page_items)
                
                # Check if there are more pages
                page_context = data.get("page_context", {})
                if not page_context.get("has_more_page"):
                    break
                
                page += 1
        
        logger.info(f"Successfully fetched {len(items)} items from Zoho Books")
        return items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Zoho items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch items from Zoho Books: {str(e)}"
        )


async def fetch_item_by_id(item_id: str) -> Optional[Dict]:
    """
    Fetch a single item from Zoho Books by ID
    
    Args:
        item_id: Zoho item ID
        
    Returns:
        Item dictionary or None
    """
    try:
        access_token = await get_access_token()
        
        pool = get_db()
        async with pool.acquire() as conn:
            organization_id = await settings_service.get_setting(conn, "zoho.organization_id")
            base_url = await settings_service.get_setting(conn, "zoho.base_url")
        
        if not base_url:
            base_url = "https://books.zoho.com/api/v3"
        
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/items/{item_id}",
                headers=headers,
                params={"organization_id": organization_id},
                timeout=30.0
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            return data.get("item")
            
    except Exception as e:
        logger.error(f"Error fetching Zoho item {item_id}: {e}")
        return None

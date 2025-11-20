"""
Documentation API Routes
Provides access to in-app documentation for logged-in users
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.schemas.docs import (
    DocListResponse,
    DocSummary,
    DocContent,
    DocSearchResponse,
    DocCategoriesResponse,
    TOCEntry
)
from app.services.docs_service import DocsService
from app.auth.dependencies import get_current_user


router = APIRouter(prefix="/docs", tags=["Documentation"])


@router.get(
    "/",
    response_model=DocListResponse,
    summary="Get list of all available documentation"
)
async def get_doc_list(
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of all available documentation files.

    **Authentication Required:** User must be logged in.

    Returns:
    - List of documentation with titles, categories, and descriptions
    """
    docs = DocsService.get_doc_list()

    return {
        "total": len(docs),
        "docs": docs
    }


@router.get(
    "/categories",
    response_model=DocCategoriesResponse,
    summary="Get documentation organized by categories"
)
async def get_doc_categories(
    current_user: dict = Depends(get_current_user)
):
    """
    Get documentation organized into categories (General, Modules, etc.).

    **Authentication Required:** User must be logged in.

    Returns:
    - Categories with their associated documents
    """
    categories = DocsService.get_categories()

    return {
        "total_categories": len(categories),
        "categories": categories
    }


@router.get(
    "/search",
    response_model=DocSearchResponse,
    summary="Search across all documentation"
)
async def search_docs(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for a term across all documentation files.

    **Authentication Required:** User must be logged in.

    **Parameters:**
    - **q**: Search query (at least 2 characters)
    - **limit**: Maximum results to return (default: 20, max: 100)

    Returns:
    - List of matching results with context and line numbers
    """
    results = DocsService.search_docs(q, limit=limit)

    return {
        "query": q,
        "total_results": len(results),
        "results": results
    }


@router.get(
    "/{doc_id}",
    response_model=DocContent,
    summary="Get specific documentation content"
)
async def get_doc(
    doc_id: str,
    format: str = Query("html", regex="^(markdown|html)$", description="Response format: 'markdown' or 'html'"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the full content of a specific documentation file.

    **Authentication Required:** User must be logged in.

    **Parameters:**
    - **doc_id**: Document identifier (e.g., 'getting-started', 'admin', 'inventory', 'biofloc')
    - **format**: Response format - 'markdown' (raw) or 'html' (rendered)

    **Available Documents:**
    - `getting-started` - Getting Started Guide
    - `admin` - Admin Module Guide
    - `inventory` - Inventory Module Guide
    - `biofloc` - Biofloc Module Guide

    Returns:
    - Document content in requested format with metadata
    """
    doc = DocsService.get_doc_content(doc_id, format=format)

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Documentation '{doc_id}' not found. Available docs: getting-started, admin, inventory, biofloc"
        )

    return doc


@router.get(
    "/{doc_id}/toc",
    response_model=List[TOCEntry],
    summary="Get table of contents for a document"
)
async def get_doc_toc(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the table of contents (headers) for a specific document.

    **Authentication Required:** User must be logged in.

    **Parameters:**
    - **doc_id**: Document identifier

    Returns:
    - List of headers with levels and anchor links
    """
    toc = DocsService.get_table_of_contents(doc_id)

    if toc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Documentation '{doc_id}' not found"
        )

    return toc

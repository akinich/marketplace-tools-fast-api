"""
Documentation Schema Models
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class DocSummary(BaseModel):
    """Summary of a documentation file"""
    id: str = Field(..., description="Unique document ID")
    title: str = Field(..., description="Document title")
    category: str = Field(..., description="Category (General, Modules, etc.)")
    description: str = Field(..., description="Brief description")
    order: int = Field(..., description="Display order")


class DocContent(BaseModel):
    """Full documentation content"""
    id: str = Field(..., description="Unique document ID")
    title: str = Field(..., description="Document title")
    category: str = Field(..., description="Category")
    description: str = Field(..., description="Brief description")
    content: str = Field(..., description="Document content (markdown or HTML)")
    format: str = Field(..., description="Content format: 'markdown' or 'html'")


class DocSearchResult(BaseModel):
    """Search result entry"""
    doc_id: str = Field(..., description="Document ID where match was found")
    doc_title: str = Field(..., description="Document title")
    line_number: int = Field(..., description="Line number of match")
    match: str = Field(..., description="Matching line content")
    highlighted_match: str = Field(..., description="Match with query highlighted")
    context: str = Field(..., description="Surrounding context")


class DocSearchResponse(BaseModel):
    """Search response"""
    query: str = Field(..., description="Search query")
    total_results: int = Field(..., description="Number of results found")
    results: List[DocSearchResult] = Field(..., description="Search results")


class DocCategory(BaseModel):
    """Documentation category"""
    name: str = Field(..., description="Category name")
    docs: List[DocSummary] = Field(..., description="Documents in this category")


class TOCEntry(BaseModel):
    """Table of contents entry"""
    level: int = Field(..., description="Header level (1-6)")
    title: str = Field(..., description="Header title")
    anchor: str = Field(..., description="Anchor ID for linking")


class DocListResponse(BaseModel):
    """Response with list of available docs"""
    total: int = Field(..., description="Total number of documents")
    docs: List[DocSummary] = Field(..., description="List of documents")


class DocCategoriesResponse(BaseModel):
    """Response with categorized docs"""
    total_categories: int = Field(..., description="Number of categories")
    categories: List[DocCategory] = Field(..., description="Categories with docs")

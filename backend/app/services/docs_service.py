"""
================================================================================
Documentation Service
================================================================================
Version: 1.0.0
Created: 2025-11-20
Last Updated: 2025-11-20

Description:
  Service for managing and serving in-app documentation. Reads markdown files,
  provides search functionality, renders HTML, and extracts table of contents.

Changelog:
----------
v1.0.0 (2025-11-20):
  - Initial implementation
  - Read markdown files from /docs/simplified directory
  - Convert markdown to HTML using markdown library
  - Full-text search across all documentation
  - Extract table of contents from headers
  - Category organization (General, Modules)
  - Support for 4 docs: getting-started, admin, inventory, biofloc

================================================================================
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import markdown


class DocsService:
    """Service for managing and serving documentation"""

    # Path to simplified docs
    DOCS_BASE_PATH = Path(__file__).parent.parent.parent.parent / "docs" / "simplified"

    # Available documentation files
    DOCS_MAP = {
        "getting-started": {
            "title": "Getting Started",
            "file": "getting-started.md",
            "category": "General",
            "description": "Learn the basics of using the Farm Management System",
            "order": 1
        },
        "admin": {
            "title": "Admin Module",
            "file": "admin.md",
            "category": "Modules",
            "description": "Manage users, permissions, and system settings",
            "order": 2
        },
        "inventory": {
            "title": "Inventory Module",
            "file": "inventory.md",
            "category": "Modules",
            "description": "Track supplies, manage stock, and create purchase orders",
            "order": 3
        },
        "biofloc": {
            "title": "Biofloc Module",
            "file": "biofloc.md",
            "category": "Modules",
            "description": "Manage fish tanks, batches, and daily operations",
            "order": 4
        }
    }

    @classmethod
    def get_doc_list(cls) -> List[Dict]:
        """Get list of all available documentation"""
        docs = []
        for key, info in cls.DOCS_MAP.items():
            docs.append({
                "id": key,
                "title": info["title"],
                "category": info["category"],
                "description": info["description"],
                "order": info["order"]
            })

        # Sort by order
        docs.sort(key=lambda x: x["order"])
        return docs

    @classmethod
    def get_doc_content(cls, doc_id: str, format: str = "markdown") -> Optional[Dict]:
        """
        Get content of a specific documentation file

        Args:
            doc_id: ID of the document (e.g., 'getting-started')
            format: 'markdown' or 'html'

        Returns:
            Dict with title, content, and metadata or None if not found
        """
        if doc_id not in cls.DOCS_MAP:
            return None

        doc_info = cls.DOCS_MAP[doc_id]
        file_path = cls.DOCS_BASE_PATH / doc_info["file"]

        if not file_path.exists():
            return None

        # Read markdown content
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Convert to HTML if requested
        content = markdown_content
        if format == "html":
            content = markdown.markdown(
                markdown_content,
                extensions=['fenced_code', 'tables', 'toc']
            )

        return {
            "id": doc_id,
            "title": doc_info["title"],
            "category": doc_info["category"],
            "description": doc_info["description"],
            "content": content,
            "format": format
        }

    @classmethod
    def search_docs(cls, query: str, limit: int = 20) -> List[Dict]:
        """
        Search across all documentation files

        Args:
            query: Search term
            limit: Maximum number of results

        Returns:
            List of matching results with context
        """
        if not query or len(query.strip()) < 2:
            return []

        query_lower = query.lower()
        results = []

        for doc_id, doc_info in cls.DOCS_MAP.items():
            file_path = cls.DOCS_BASE_PATH / doc_info["file"]

            if not file_path.exists():
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Search in content (case-insensitive)
            content_lower = content.lower()

            # Find all occurrences
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if query_lower in line.lower():
                    # Get context (line before and after)
                    start_idx = max(0, line_num - 2)
                    end_idx = min(len(lines), line_num + 1)
                    context_lines = lines[start_idx:end_idx]

                    # Highlight the search term in the matching line
                    highlighted_line = re.sub(
                        f'({re.escape(query)})',
                        r'**\1**',
                        line,
                        flags=re.IGNORECASE
                    )

                    results.append({
                        "doc_id": doc_id,
                        "doc_title": doc_info["title"],
                        "line_number": line_num,
                        "match": line.strip(),
                        "highlighted_match": highlighted_line.strip(),
                        "context": '\n'.join(context_lines).strip()
                    })

                    # Limit results per document
                    if len([r for r in results if r["doc_id"] == doc_id]) >= 5:
                        break

        # Sort by relevance (number of times query appears in match)
        results.sort(
            key=lambda x: x["match"].lower().count(query_lower),
            reverse=True
        )

        return results[:limit]

    @classmethod
    def get_categories(cls) -> List[Dict]:
        """Get list of documentation categories"""
        categories = {}

        for doc_id, doc_info in cls.DOCS_MAP.items():
            category = doc_info["category"]
            if category not in categories:
                categories[category] = {
                    "name": category,
                    "docs": []
                }

            categories[category]["docs"].append({
                "id": doc_id,
                "title": doc_info["title"],
                "category": doc_info["category"],
                "description": doc_info["description"],
                "order": doc_info["order"]
            })

        return list(categories.values())

    @classmethod
    def get_table_of_contents(cls, doc_id: str) -> Optional[List[Dict]]:
        """
        Extract table of contents from a document (headers)

        Args:
            doc_id: ID of the document

        Returns:
            List of headers with levels and titles
        """
        if doc_id not in cls.DOCS_MAP:
            return None

        doc_info = cls.DOCS_MAP[doc_id]
        file_path = cls.DOCS_BASE_PATH / doc_info["file"]

        if not file_path.exists():
            return None

        toc = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Match markdown headers (# Header)
                match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
                if match:
                    level = len(match.group(1))  # Number of #
                    title = match.group(2).strip()

                    # Remove emojis and extra formatting for cleaner TOC
                    title_clean = re.sub(r'[^\w\s-]', '', title).strip()

                    # Generate anchor ID (lowercase, spaces to hyphens)
                    anchor = title_clean.lower().replace(' ', '-')

                    toc.append({
                        "level": level,
                        "title": title,
                        "anchor": anchor
                    })

        return toc

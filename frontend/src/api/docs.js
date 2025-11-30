/**
 * ============================================================================
 * Documentation API Client
 * ============================================================================
 * Version: 1.0.0
 * Created: 2025-11-20
 * Last Updated: 2025-11-20
 *
 * Description:
 *   API client for documentation endpoints. Handles fetching doc lists,
 *   content, search, and table of contents.
 *
 * Methods:
 *   - getDocsList() - Get list of all available documentation
 *   - getCategories() - Get documentation organized by categories
 *   - getDocument(docId, format) - Get specific document content
 *   - searchDocs(query, limit) - Search across all documentation
 *   - getTableOfContents(docId) - Get TOC for a document
 *
 * Changelog:
 * ----------
 * v1.0.0 (2025-11-20):
 *   - Initial implementation
 *   - All methods call authenticated endpoints
 *   - Support for HTML and markdown formats
 *   - Search with configurable limit
 *   - TOC extraction
 * ============================================================================
 */

import apiClient from './client';

export const docsAPI = {
  /**
   * Get list of all available documentation
   */
  getDocsList: async () => {
    const response = await apiClient.get('/docs');
    return response.data;
  },

  /**
   * Get documentation organized by categories
   */
  getCategories: async () => {
    const response = await apiClient.get('/docs/categories');
    return response.data;
  },

  /**
   * Get specific document content
   * @param {string} docId - Document ID (e.g., 'getting-started', 'admin')
   * @param {string} format - 'markdown' or 'html' (default: 'html')
   */
  getDocument: async (docId, format = 'html') => {
    const response = await apiClient.get(`/docs/${docId}`, {
      params: { format }
    });
    return response.data;
  },

  /**
   * Search across all documentation
   * @param {string} query - Search term
   * @param {number} limit - Maximum results (default: 20)
   */
  searchDocs: async (query, limit = 20) => {
    const response = await apiClient.get('/docs/search', {
      params: { q: query, limit }
    });
    return response.data;
  },

  /**
   * Get table of contents for a document
   * @param {string} docId - Document ID
   */
  getTableOfContents: async (docId) => {
    const response = await apiClient.get(`/docs/${docId}/toc`);
    return response.data;
  },
};

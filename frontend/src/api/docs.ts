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
 */

import apiClient from './client';

export const docsAPI = {
    /**
     * Get list of all available documentation
     */
    getDocsList: async (): Promise<any> => {
        const response = await apiClient.get('/docs');
        return response.data;
    },

    /**
     * Get documentation organized by categories
     */
    getCategories: async (): Promise<any> => {
        const response = await apiClient.get('/docs/categories');
        return response.data;
    },

    /**
     * Get specific document content
     * @param {string} docId - Document ID (e.g., 'getting-started', 'admin')
     * @param {string} format - 'markdown' or 'html' (default: 'html')
     */
    getDocument: async (docId: string, format: string = 'html'): Promise<any> => {
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
    searchDocs: async (query: string, limit: number = 20): Promise<any> => {
        const response = await apiClient.get('/docs/search', {
            params: { q: query, limit }
        });
        return response.data;
    },

    /**
     * Get table of contents for a document
     * @param {string} docId - Document ID
     */
    getTableOfContents: async (docId: string): Promise<any> => {
        const response = await apiClient.get(`/docs/${docId}/toc`);
        return response.data;
    },
};

/**
 * ============================================================================
 * Documentation Module
 * ============================================================================
 * Version: 1.0.0
 * Created: 2025-11-20
 * Last Updated: 2025-11-20
 *
 * Description:
 *   Main module component that handles routing for documentation pages.
 *   Provides access to in-app help guides written in simple language.
 *
 * Routes:
 *   - /docs or /docs/browse - List all documentation with categories
 *   - /docs/:docId - View specific documentation
 *
 * Changelog:
 * ----------
 * v1.0.0 (2025-11-20):
 *   - Initial implementation
 *   - Route handling for browse and view pages
 *   - Fallback to /docs on invalid routes
 * ============================================================================
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Import documentation pages
import DocsList from './DocsList';
import DocsViewer from './DocsViewer';

export default function DocsModule() {
  return (
    <Routes>
      {/* Default route - List */}
      <Route index element={<DocsList />} />

      {/* Main pages */}
      <Route path="browse" element={<DocsList />} />
      <Route path=":docId" element={<DocsViewer />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/docs" replace />} />
    </Routes>
  );
}

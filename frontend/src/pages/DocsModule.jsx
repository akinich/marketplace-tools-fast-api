/**
 * ============================================================================
 * Documentation Module
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-20
 *
 * Main module component that handles routing for documentation pages:
 * - Browse: List all documentation with categories
 * - View: Read specific documentation
 * - Search: Search across all documentation
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

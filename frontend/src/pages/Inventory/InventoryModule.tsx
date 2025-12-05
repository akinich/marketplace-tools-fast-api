/**
 * Inventory Module - Parent Component
 * Version: 1.0.0
 * Created: 2024-12-04
 *
 * Description:
 *   Parent wrapper for Inventory sub-modules
 *   - Batch Tracking
 *   - Inventory Management (future)
 *   - Wastage Tracking (future)
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import BatchTrackingPage from './BatchTrackingPage';
import BatchDetailPage from './BatchDetailPage';

export default function InventoryModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="batch-tracking" replace />} />
            <Route path="batch-tracking" element={<BatchTrackingPage />} />
            <Route path="batch-tracking/:batchNumber" element={<BatchDetailPage />} />
        </Routes>
    );
}

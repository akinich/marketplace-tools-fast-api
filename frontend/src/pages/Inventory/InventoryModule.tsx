/**
 * Inventory Module - Parent Component
 * Version: 2.0.0
 * Created: 2024-12-04
 * Updated: 2024-12-06
 *
 * Description:
 *   Parent wrapper for Inventory sub-modules
 *   - Batch Tracking
 *   - Wastage Tracking
 *   - Inventory Management (future)
 */


import { Routes, Route, Navigate } from 'react-router-dom';
import BatchTrackingPage from './BatchTrackingPage';
import BatchDetailPage from './BatchDetailPage';
import WastageTrackingPage from './WastageTracking/WastageTrackingPage';
import WastageLogForm from './WastageTracking/WastageLogForm';
import WastageAnalyticsPage from './WastageTracking/WastageAnalyticsPage';
import WastageAlertsPage from './WastageTracking/WastageAlertsPage';

export default function InventoryModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="batch-tracking" replace />} />
            <Route path="batch-tracking" element={<BatchTrackingPage />} />
            <Route path="batch-tracking/:batchNumber" element={<BatchDetailPage />} />
            <Route path="wastage-tracking" element={<WastageTrackingPage />} />
            <Route path="wastage-tracking/log" element={<WastageLogForm />} />
            <Route path="wastage-tracking/analytics" element={<WastageAnalyticsPage />} />
            <Route path="wastage-tracking/alerts" element={<WastageAlertsPage />} />
        </Routes>
    );
}

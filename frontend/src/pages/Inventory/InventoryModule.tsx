/**
 * Inventory Module - Parent Component
 * Version: 3.0.0
 * Created: 2024-12-04
 * Updated: 2024-12-12
 *
 * Description:
 *   Parent wrapper for Inventory sub-modules
 *   - Stock Management (NEW)
 *   - Batch Tracking
 *   - Wastage Tracking
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import InventoryDashboard from './InventoryDashboard';
import BatchTrackingPage from './BatchTrackingPage';
import BatchDetailPage from './BatchDetailPage';
import WastageTrackingPage from './WastageTracking/WastageTrackingPage';
import WastageLogForm from './WastageTracking/WastageLogForm';
import WastageAnalyticsPage from './WastageTracking/WastageAnalyticsPage';
import WastageAlertsPage from './WastageTracking/WastageAlertsPage';

// Stock Management pages
import InventoryListPage from './StockManagement/InventoryListPage';
import BatchInventoryPage from './StockManagement/BatchInventoryPage';
import AdjustmentsPage from './StockManagement/AdjustmentsPage';
import ReportsPage from './StockManagement/ReportsPage';

export default function InventoryModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<InventoryDashboard />} />

            {/* Stock Management */}
            <Route path="stock" element={<InventoryListPage />} />
            <Route path="stock/batch/:batchId" element={<BatchInventoryPage />} />
            <Route path="stock/adjustments" element={<AdjustmentsPage />} />
            <Route path="stock/reports" element={<ReportsPage />} />

            {/* Batch Tracking */}
            <Route path="batch-tracking" element={<BatchTrackingPage />} />
            <Route path="batch-tracking/:batchNumber" element={<BatchDetailPage />} />

            {/* Wastage Tracking */}
            <Route path="wastage-tracking" element={<WastageTrackingPage />} />
            <Route path="wastage-tracking/log" element={<WastageLogForm />} />
            <Route path="wastage-tracking/analytics" element={<WastageAnalyticsPage />} />
            <Route path="wastage-tracking/alerts" element={<WastageAlertsPage />} />
        </Routes>
    );
}

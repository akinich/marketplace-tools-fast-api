/**
 * Reporting Module - Parent Component
 * Version: 1.0.0
 * Created: 2025-12-07
 *
 * Description:
 *   Parent wrapper for Reporting sub-modules
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import ReportingDashboard from './ReportingDashboard';
import PurchaseReports from './PurchaseReports';
import WastageReports from './WastageReports';
import InventoryReports from './InventoryReports';
import SalesReports from './SalesReports';
import OperationalReports from './OperationalReports';
import FinancialReports from './FinancialReports';
import TraceabilityReports from './TraceabilityReports';
import LogisticsReports from './LogisticsReports';

export default function ReportingModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<ReportingDashboard />} />
            <Route path="purchase" element={<PurchaseReports />} />
            <Route path="wastage" element={<WastageReports />} />
            <Route path="inventory" element={<InventoryReports />} />
            <Route path="sales" element={<SalesReports />} />
            <Route path="operations" element={<OperationalReports />} />
            <Route path="financial" element={<FinancialReports />} />
            <Route path="traceability" element={<TraceabilityReports />} />
            <Route path="logistics" element={<LogisticsReports />} />
        </Routes>
    );
}

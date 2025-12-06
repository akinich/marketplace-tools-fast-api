/**
 * Inward Operations Module - Parent Component
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Description:
 *   Parent wrapper for Inward Operations sub-modules
 *   - Purchase Order Management
 *   - GRN Management (future)
 *   - Grading & Sorting (future)
 *   - Packing & Labeling (future)
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import POListPage from './PurchaseOrders/POListPage';
import POCreateForm from './PurchaseOrders/POCreateForm';
import PODetailPage from './PurchaseOrders/PODetailPage';
import VendorPricingManager from './PurchaseOrders/VendorPricingManager';
import GRNListPage from './GRN/GRNListPage';
import GRNDetailPage from './GRN/GRNDetailPage';
import GRNDataEntryForm from './GRN/GRNDataEntryForm';

export default function InwardModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="purchase-orders" replace />} />
            <Route path="purchase-orders" element={<POListPage />} />
            <Route path="purchase-orders/create" element={<POCreateForm />} />
            <Route path="purchase-orders/:poId" element={<PODetailPage />} />
            <Route path="vendor-pricing" element={<VendorPricingManager />} />

            {/* GRN Management */}
            <Route path="grn" element={<GRNListPage />} />
            <Route path="grn/:grnId" element={<GRNDetailPage />} />
            <Route path="grn/:grnId/edit" element={<GRNDataEntryForm />} />
        </Routes>
    );
}

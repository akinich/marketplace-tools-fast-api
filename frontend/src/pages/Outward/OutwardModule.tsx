/**
 * Outward Operations Module - Parent Component
 * Version: 1.0.0
 * Created: 2025-12-07
 *
 * Description:
 *   Parent wrapper for Outward Operations sub-modules
 *   - Dashboard
 *   - Sales Orders
 *   - Invoice Management
 *   - Order Allocation
 *   - Customer Pricing Lists
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import OutwardDashboard from './OutwardDashboard';
import SalesOrders from './SalesOrders';
import InvoiceManagement from './InvoiceManagement';
import OrderAllocation from './OrderAllocation';
import CustomerPricing from './CustomerPricing';

export default function OutwardModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<OutwardDashboard />} />
            <Route path="sales-orders" element={<SalesOrders />} />
            <Route path="invoices" element={<InvoiceManagement />} />
            <Route path="allocation" element={<OrderAllocation />} />
            <Route path="customer-pricing" element={<CustomerPricing />} />
        </Routes>
    );
}

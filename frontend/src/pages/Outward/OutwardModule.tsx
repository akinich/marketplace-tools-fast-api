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
import SalesOrderList from './SalesOrders/SalesOrderList';
import SalesOrderForm from './SalesOrders/SalesOrderForm';
import InvoiceManagement from './InvoiceManagement';
import OrderAllocation from './OrderAllocation';
import CustomerPricing from './CustomerPricing';
import PriceListManagement from '../OutwardOperations/PriceListManagement';
import PriceListDetail from '../OutwardOperations/PriceListDetail';

export default function OutwardModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<OutwardDashboard />} />

            {/* Sales Orders */}
            <Route path="sales-orders" element={<SalesOrderList />} />
            <Route path="sales-orders/new" element={<SalesOrderForm />} />
            <Route path="sales-orders/:id" element={<SalesOrderForm />} />

            <Route path="invoices" element={<InvoiceManagement />} />
            <Route path="allocation" element={<OrderAllocation />} />
            <Route path="customer-pricing" element={<CustomerPricing />} />
            <Route path="price-lists" element={<PriceListManagement />} />
            <Route path="price-lists/:id" element={<PriceListDetail />} />
        </Routes>
    );
}

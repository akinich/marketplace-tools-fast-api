/**
 * B2C Operations Module - Parent Component
 * Version: 1.1.0
 * Last Updated: 2025-12-01
 *
 * Description:
 *   Parent wrapper for B2C Operations sub-modules
 *   - Order Extractor
 *   - Label Generator
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import B2CManagementDashboard from './B2CManagementDashboard';
import OrderExtractor from './OrderExtractor';
import LabelGenerator from './LabelGenerator';
import MrpLabelGenerator from './MrpLabelGenerator';
import WooToZohoExport from './WooToZohoExport';
import StockPriceUpdater from './StockPriceUpdater';
import OrderPlaceTest from './OrderPlaceTest';
import SubscriptionManagement from './SubscriptionManagement';

export default function B2COpsModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<B2CManagementDashboard />} />
            <Route path="order-extractor" element={<OrderExtractor />} />
            <Route path="label-generator" element={<LabelGenerator />} />
            <Route path="mrp-label-generator" element={<MrpLabelGenerator />} />
            <Route path="woo-to-zoho-export" element={<WooToZohoExport />} />
            <Route path="stock-price-updater" element={<StockPriceUpdater />} />
            <Route path="order-place-test" element={<OrderPlaceTest />} />
            <Route path="subscriptions" element={<SubscriptionManagement />} />
        </Routes>
    );
}

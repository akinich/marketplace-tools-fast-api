/**
 * B2C Operations Module - Parent Component
 * Version: 1.0.0
 * Last Updated: 2025-11-30
 *
 * Description:
 *   Parent wrapper for B2C Operations sub-modules
 *   - Order Extractor
 *   - Shipping Label Generator (future)
 *   - MRP Label Generator (future)
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import OrderExtractor from './OrderExtractor';

export default function B2COpsModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="order-extractor" replace />} />
            <Route path="order-extractor" element={<OrderExtractor />} />
            {/* Future routes */}
            {/* <Route path="shipping-labels" element={<ShippingLabelGenerator />} /> */}
            {/* <Route path="mrp-labels" element={<MRPLabelGenerator />} /> */}
        </Routes>
    );
}

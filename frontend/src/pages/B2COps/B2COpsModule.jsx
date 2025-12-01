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
import OrderExtractor from './OrderExtractor';
import LabelGenerator from './LabelGenerator';
import MrpLabelGenerator from './MrpLabelGenerator';
import ItemMaster from './ItemMaster';

export default function B2COpsModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="order-extractor" replace />} />
            <Route path="order-extractor" element={<OrderExtractor />} />
            <Route path="label-generator" element={<LabelGenerator />} />
            <Route path="mrp-label-generator" element={<MrpLabelGenerator />} />
            <Route path="item-master" element={<ItemMaster />} />
        </Routes>
    );
}

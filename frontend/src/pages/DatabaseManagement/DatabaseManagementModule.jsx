/**
 * Database Management Module - Parent Component
 * Version: 1.0.0
 * Created: 2025-12-02
 *
 * Description:
 *   Parent wrapper for Database Management sub-modules
 *   - Woo Item Master
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import WooItemMaster from './WooItemMaster';

export default function DatabaseManagementModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="woo-item-master" replace />} />
            <Route path="woo-item-master" element={<WooItemMaster />} />
        </Routes>
    );
}

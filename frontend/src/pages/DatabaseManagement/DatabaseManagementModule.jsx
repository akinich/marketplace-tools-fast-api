/**
 * Database Management Module - Parent Component
 * Version: 1.0.0
 * Created: 2025-12-02
 *
 * Description:
 *   Parent wrapper for Database Management sub-modules
 *   - Woo Item Master
 *   - Zoho Item Master
 *   - Zoho Vendor Master
 *   - Zoho Customer Master
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import WooItemMaster from './WooItemMaster';
import ZohoItemMaster from './ZohoItemMaster';
import ZohoVendorMaster from './ZohoVendorMaster';
import ZohoCustomerMaster from './ZohoCustomerMaster';

export default function DatabaseManagementModule() {
    return (
        <Routes>
            <Route index element={<Navigate to="woo-item-master" replace />} />
            <Route path="woo-item-master" element={<WooItemMaster />} />
            <Route path="zoho-item-master" element={<ZohoItemMaster />} />
            <Route path="zoho-vendor-master" element={<ZohoVendorMaster />} />
            <Route path="zoho-customer-master" element={<ZohoCustomerMaster />} />
        </Routes>
    );
}

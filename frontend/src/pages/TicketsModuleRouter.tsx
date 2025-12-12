/**
 * ============================================================================
 * Marketplace ERP - Tickets Module Frontend (Routing Wrapper)
 * ============================================================================
 * Version: 2.0.0
 * Last Updated: 2025-12-07
 *
 * Changelog:
 * ----------
 * v2.0.0 (2025-12-07):
 *   - Added routing structure for ticket categories
 *   - Added dashboard route showing all ticket types
 *   - Added B2B tickets route
 *   - Added B2C tickets route
 *   - Moved internal tickets to /tickets/internal
 *   - Default route redirects to dashboard
 *
 * v1.1.0 (2025-11-20):
 *   - Added ticket deletion functionality
 *
 * v1.0.0 (2025-11-20):
 *   - Initial tickets module implementation
 * ============================================================================
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import TicketsDashboard from './TicketsDashboard';
import TicketsModule from './TicketsModule';
import B2BTickets from './B2BTickets';
import B2CTickets from './B2CTickets';
import TicketDetailPage from './TicketDetailPage';

export default function TicketsModuleRouter() {
    return (
        <Routes>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<TicketsDashboard />} />
            <Route path="internal" element={<TicketsModule />} />
            <Route path="b2b" element={<B2BTickets />} />
            <Route path="b2c" element={<B2CTickets />} />
            <Route path=":id" element={<TicketDetailPage />} />
        </Routes>
    );
}

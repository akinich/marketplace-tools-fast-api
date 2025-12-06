/**
 * Inward Dashboard Page
 * Version: 1.0.0
 * Created: 2025-12-07
 */

import React from 'react';
import ComingSoon from '../../components/ComingSoon';

export default function InwardDashboard() {
    return (
        <ComingSoon
            moduleName="Inward Operations Dashboard"
            description="Overview of all inward activities including active POs, pending GRNs, today's receiving schedule, and wastage alerts."
            estimatedPhase="Phase 2 (Weeks 3-6)"
            priority="CRITICAL"
        />
    );
}

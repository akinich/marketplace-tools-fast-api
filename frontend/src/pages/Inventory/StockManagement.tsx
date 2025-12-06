/**
 * Stock Management Page
 * Version: 1.0.0
 * Created: 2025-12-07
 */

import React from 'react';
import ComingSoon from '../../components/ComingSoon';

export default function StockManagement() {
    return (
        <ComingSoon
            moduleName="Stock Management"
            description="Track stock levels across multiple locations with batch-level granularity. Manage FIFO allocation, reorder levels, and stock movements."
            estimatedPhase="Phase 3 (Weeks 7-8)"
            priority="CRITICAL"
        />
    );
}

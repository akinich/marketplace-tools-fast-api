/**
 * Order Allocation Page
 * Version: 1.0.0
 * Created: 2025-12-07
 */

import ComingSoon from '../../components/ComingSoon';

export default function OrderAllocation() {
    return (
        <ComingSoon
            moduleName="Order Allocation (FIFO)"
            description="Allocate inventory batches to sales orders using FIFO with repacked batch priority. Manage stock availability and shortage handling."
            estimatedPhase="Phase 4 (Weeks 10-11)"
            priority="CRITICAL"
        />
    );
}

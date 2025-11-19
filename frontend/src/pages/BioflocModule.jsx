/**
 * ============================================================================
 * Biofloc Aquaculture Management Module
 * ============================================================================
 * Version: 2.0.0
 * Last Updated: 2025-11-19
 *
 * Main module component that handles routing for all biofloc sub-pages:
 * - Dashboard: Overview and metrics
 * - Tanks: Tank management
 * - Batches: Batch lifecycle tracking
 * - Feeding: Multi-tank feed session recording
 * - Feeding History: View all feeding sessions
 * - Sampling: Fish sampling measurements
 * - Mortality: Mortality event tracking
 * - Water Tests: Multi-tank water quality parameters
 * - Water Test History: View all water tests
 * - Harvests: Harvest recording
 * - Transfer: Batch transfer between tanks
 *
 * CHANGES in v2.0.0:
 * - Added multi-tank feeding support
 * - Added multi-tank water testing support
 * - Added feeding history page
 * - Added water test history page
 * - Added batch transfer form
 * ============================================================================
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Import biofloc pages
import BioflocDashboard from './BioflocDashboard';
import BioflocTanks from './BioflocTanks';
import BioflocBatches from './BioflocBatches';
import BioflocBatchDetail from './BioflocBatchDetail';
import BioflocFeedingHistory from './BioflocFeedingHistory';
import BioflocWaterTestHistory from './BioflocWaterTestHistory';
import BioflocTankInputsHistory from './BioflocTankInputsHistory';

// Import operational forms
import FeedingForm from '../components/FeedingForm';
import SamplingForm from '../components/SamplingForm';
import MortalityForm from '../components/MortalityForm';
import WaterTestForm from '../components/WaterTestForm';
import HarvestForm from '../components/HarvestForm';
import BatchTransferForm from '../components/BatchTransferForm';
import TankInputsForm from '../components/TankInputsForm';

export default function BioflocModule() {
  return (
    <Routes>
      {/* Default route - Dashboard */}
      <Route index element={<BioflocDashboard />} />

      {/* Main pages */}
      <Route path="dashboard" element={<BioflocDashboard />} />
      <Route path="tanks" element={<BioflocTanks />} />
      <Route path="batches/:batchId" element={<BioflocBatchDetail />} />
      <Route path="batches" element={<BioflocBatches />} />

      {/* Operational forms */}
      <Route path="feeding" element={<FeedingForm />} />
      <Route path="feeding-history" element={<BioflocFeedingHistory />} />
      <Route path="sampling" element={<SamplingForm />} />
      <Route path="mortality" element={<MortalityForm />} />
      <Route path="water-tests" element={<WaterTestForm />} />
      <Route path="water-test-history" element={<BioflocWaterTestHistory />} />
      <Route path="tank-inputs" element={<TankInputsForm />} />
      <Route path="tank-inputs-history" element={<BioflocTankInputsHistory />} />
      <Route path="harvests" element={<HarvestForm />} />
      <Route path="transfer" element={<BatchTransferForm />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/biofloc" replace />} />
    </Routes>
  );
}

/**
 * ============================================================================
 * Biofloc Aquaculture Management Module
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-11-18
 *
 * Main module component that handles routing for all biofloc sub-pages:
 * - Dashboard: Overview and metrics
 * - Tanks: Tank management
 * - Batches: Batch lifecycle tracking
 * - Feeding: Feed session recording
 * - Sampling: Fish sampling measurements
 * - Mortality: Mortality event tracking
 * - Water Tests: Water quality parameters
 * - Harvests: Harvest recording
 * ============================================================================
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Import biofloc pages
import BioflocDashboard from './BioflocDashboard';
import BioflocTanks from './BioflocTanks';
import BioflocBatches from './BioflocBatches';

// Import operational forms
import FeedingForm from '../components/FeedingForm';
import SamplingForm from '../components/SamplingForm';
import MortalityForm from '../components/MortalityForm';
import WaterTestForm from '../components/WaterTestForm';
import HarvestForm from '../components/HarvestForm';

export default function BioflocModule() {
  return (
    <Routes>
      {/* Default route - Dashboard */}
      <Route index element={<BioflocDashboard />} />

      {/* Main pages */}
      <Route path="dashboard" element={<BioflocDashboard />} />
      <Route path="tanks" element={<BioflocTanks />} />
      <Route path="batches" element={<BioflocBatches />} />

      {/* Operational forms */}
      <Route path="feeding" element={<FeedingForm />} />
      <Route path="sampling" element={<SamplingForm />} />
      <Route path="mortality" element={<MortalityForm />} />
      <Route path="water-tests" element={<WaterTestForm />} />
      <Route path="harvests" element={<HarvestForm />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/biofloc" replace />} />
    </Routes>
  );
}

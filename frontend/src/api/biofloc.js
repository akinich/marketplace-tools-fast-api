/**
 * ============================================================================
 * Biofloc Module - API Client
 * ============================================================================
 * Version: 1.1.0
 * Last Updated: 2025-11-19
 *
 * API client for biofloc aquaculture management module.
 * Provides methods for tanks, batches, feeding, sampling, mortality,
 * water tests, harvests, tank inputs, and grading.
 *
 * CHANGELOG:
 * v1.1.0 (2025-11-19):
 * - Added recordGrading() for batch grading with size splitting
 * - Updated transferBatch() to support new payload format
 * - Added support for grading transfers (Option B)
 *
 * v1.0.0 (2025-11-18):
 * - Initial release with core biofloc operations
 * ============================================================================
 */

import apiClient from './client';

export const bioflocAPI = {
  // ========================================================================
  // TANKS
  // ========================================================================
  getTanks: async (params = {}) => {
    const response = await apiClient.get('/biofloc/tanks', { params });
    return response.data;
  },

  getTank: async (tankId) => {
    const response = await apiClient.get(`/biofloc/tanks/${tankId}`);
    return response.data;
  },

  createTank: async (data) => {
    const response = await apiClient.post('/biofloc/tanks', data);
    return response.data;
  },

  updateTank: async (tankId, data) => {
    const response = await apiClient.put(`/biofloc/tanks/${tankId}`, data);
    return response.data;
  },

  deleteTank: async (tankId) => {
    const response = await apiClient.delete(`/biofloc/tanks/${tankId}`);
    return response.data;
  },

  getTankHistory: async (tankId) => {
    const response = await apiClient.get(`/biofloc/tanks/${tankId}/history`);
    return response.data;
  },

  // ========================================================================
  // BATCHES
  // ========================================================================
  getBatches: async (params = {}) => {
    const response = await apiClient.get('/biofloc/batches', { params });
    return response.data;
  },

  getBatch: async (batchId) => {
    const response = await apiClient.get(`/biofloc/batches/${batchId}`);
    return response.data;
  },

  createBatch: async (data) => {
    const response = await apiClient.post('/biofloc/batches', data);
    return response.data;
  },

  transferBatch: async (data) => {
    // Support both old format (batchId, data) and new format (just data with batch_id)
    const batchId = data.batch_id;
    const payload = {
      to_tank_id: data.to_tank_id,
      transfer_date: data.transfer_date,
      transfer_reason: data.transfer_reason || 'manual',
      fish_count: data.fish_count,
      avg_weight_g: data.avg_weight_g,
      notes: data.notes,
    };
    if (data.from_tank_id) payload.from_tank_id = data.from_tank_id;
    const response = await apiClient.post(`/biofloc/batches/${batchId}/transfer`, payload);
    return response.data;
  },

  recordGrading: async (data) => {
    const response = await apiClient.post('/biofloc/batches/grading', data);
    return response.data;
  },

  getBatchPerformance: async (batchId) => {
    const response = await apiClient.get(`/biofloc/batches/${batchId}/performance`);
    return response.data;
  },

  // ========================================================================
  // FEEDING
  // ========================================================================
  getFeedingSessions: async (params = {}) => {
    const response = await apiClient.get('/biofloc/feeding', { params });
    return response.data;
  },

  recordFeeding: async (data) => {
    const response = await apiClient.post('/biofloc/feeding', data);
    return response.data;
  },

  // ========================================================================
  // SAMPLING
  // ========================================================================
  getSamplings: async (params = {}) => {
    const response = await apiClient.get('/biofloc/sampling', { params });
    return response.data;
  },

  recordSampling: async (data) => {
    const response = await apiClient.post('/biofloc/sampling', data);
    return response.data;
  },

  // ========================================================================
  // MORTALITY
  // ========================================================================
  getMortalities: async (params = {}) => {
    const response = await apiClient.get('/biofloc/mortality', { params });
    return response.data;
  },

  recordMortality: async (data) => {
    const response = await apiClient.post('/biofloc/mortality', data);
    return response.data;
  },

  // ========================================================================
  // WATER TESTS
  // ========================================================================
  getWaterTests: async (params = {}) => {
    const response = await apiClient.get('/biofloc/water-tests', { params });
    return response.data;
  },

  recordWaterTest: async (data) => {
    const response = await apiClient.post('/biofloc/water-tests', data);
    return response.data;
  },

  // ========================================================================
  // TANK INPUTS
  // ========================================================================
  getTankInputs: async (params = {}) => {
    const response = await apiClient.get('/biofloc/tank-inputs', { params });
    return response.data;
  },

  recordTankInput: async (data) => {
    const response = await apiClient.post('/biofloc/tank-inputs', data);
    return response.data;
  },

  // ========================================================================
  // HARVESTS
  // ========================================================================
  getHarvests: async (params = {}) => {
    const response = await apiClient.get('/biofloc/harvests', { params });
    return response.data;
  },

  recordHarvest: async (data) => {
    const response = await apiClient.post('/biofloc/harvests', data);
    return response.data;
  },

  // ========================================================================
  // DASHBOARD & REPORTING
  // ========================================================================
  getDashboard: async () => {
    const response = await apiClient.get('/biofloc/dashboard');
    return response.data;
  },

  // ========================================================================
  // HEALTH CHECK
  // ========================================================================
  healthCheck: async () => {
    const response = await apiClient.get('/biofloc/health');
    return response.data;
  },
};

/**
 * Main App Component
 * Version: 1.3.0
 *
 * Changelog:
 * v1.3.0 (2025-11-21):
 *   - Added route-based code splitting with React.lazy()
 *   - Added Suspense boundaries for lazy-loaded components
 *   - Improved bundle size with dynamic imports
 *
 * v1.2.0 (2025-11-21):
 *   - Added UserProfilePage route at /profile
 *
 * v1.1.0 (2025-11-21):
 *   - Added ChangePasswordPage route
 *   - Added mustChangePassword redirect logic
 */

import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import useAuthStore from './store/authStore';

// Lazy-loaded Pages (code-split by route)
const LoginPage = lazy(() => import('./pages/LoginPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
const ChangePasswordPage = lazy(() => import('./pages/ChangePasswordPage'));
const UserProfilePage = lazy(() => import('./pages/UserProfilePage'));
const DashboardLayout = lazy(() => import('./components/DashboardLayout'));
const DashboardHome = lazy(() => import('./pages/DashboardHome'));
const AdminPanel = lazy(() => import('./pages/AdminPanel'));
const InventoryModule = lazy(() => import('./pages/InventoryModule'));
const BioflocModule = lazy(() => import('./pages/BioflocModule'));
const TicketsModule = lazy(() => import('./pages/TicketsModule'));
const DevelopmentModule = lazy(() => import('./pages/DevelopmentModule'));
const DocsModule = lazy(() => import('./pages/DocsModule'));

// Loading fallback component
const LoadingFallback = () => (
  <Box
    sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#f5f5f5'
    }}
  >
    <CircularProgress size={60} />
  </Box>
);

// Protected Route Component
const ProtectedRoute = ({ children, allowChangePassword = false }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const mustChangePassword = useAuthStore((state) => state.mustChangePassword);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // If must change password and not on change-password page, redirect
  if (mustChangePassword && !allowChangePassword && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />;
  }

  return children;
};

function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Change Password Route (protected, but allowed when mustChangePassword) */}
        <Route
          path="/change-password"
          element={
            <ProtectedRoute allowChangePassword>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardHome />} />
          <Route path="dashboard" element={<DashboardHome />} />
          <Route path="profile" element={<UserProfilePage />} />
          <Route path="admin/*" element={<AdminPanel />} />
          <Route path="inventory/*" element={<InventoryModule />} />
          <Route path="biofloc/*" element={<BioflocModule />} />
          <Route path="tickets/*" element={<TicketsModule />} />
          <Route path="development/*" element={<DevelopmentModule />} />
          <Route path="docs/*" element={<DocsModule />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;

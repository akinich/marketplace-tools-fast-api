/**
 * Main App Component
 * Version: 1.2.0
 *
 * Changelog:
 * v1.2.0 (2025-11-21):
 *   - Added UserProfilePage route at /profile
 *
 * v1.1.0 (2025-11-21):
 *   - Added ChangePasswordPage route
 *   - Added mustChangePassword redirect logic
 */

import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import useAuthStore from './store/authStore';

// Pages
import LoginPage from './pages/LoginPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import ChangePasswordPage from './pages/ChangePasswordPage';
import UserProfilePage from './pages/UserProfilePage';
import DashboardLayout from './components/DashboardLayout';
import DashboardHome from './pages/DashboardHome';
import AdminPanel from './pages/AdminPanel';
import InventoryModule from './pages/InventoryModule';
import BioflocModule from './pages/BioflocModule';
import TicketsModule from './pages/TicketsModule';
import DevelopmentModule from './pages/DevelopmentModule';
import DocsModule from './pages/DocsModule';

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
  );
}

export default App;

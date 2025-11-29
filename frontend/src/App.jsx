/**
 * Main App Component
 * Version: 1.4.0
 *
 * Changelog:
 * v1.4.0 (2025-11-23):
 *   - Migrated all Communication routes to /communication/* pattern
 *   - Added /communication/telegram route for Telegram settings
 *   - Updated /webhooks to /communication/webhooks
 *   - Updated /api-keys to /communication/api-keys
 *   - Added /communication/websockets route for WebSocket settings
 *   - All Communication modules now properly namespaced under parent route
 *
 * v1.3.0 (2025-11-22):
 *   - Integrated WebSocket service for real-time notifications
 *   - Auto-connect/disconnect WebSocket based on authentication state
 *   - Added WebhooksPage route at /communication/webhooks
 *   - Added EmailManagementPage route at /communication/smtp
 *   - Added API Keys management page route at /api-keys
 *
 * v1.2.0 (2025-11-21):
 *   - Added UserProfilePage route at /profile
 *
 * v1.1.0 (2025-11-21):
 *   - Added ChangePasswordPage route
 *   - Added mustChangePassword redirect logic
 */

import React, { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import useAuthStore from './store/authStore';
import websocketService from './services/websocket';

// Pages
import LoginPage from './pages/LoginPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import ChangePasswordPage from './pages/ChangePasswordPage';
import UserProfilePage from './pages/UserProfilePage';
import DashboardLayout from './components/DashboardLayout';
import DashboardHome from './pages/DashboardHome';
import AdminPanel from './pages/AdminPanel';
import SettingsPage from './pages/SettingsPage';

// Communication Module Pages
import TelegramSettings from './pages/TelegramSettings';
import EmailManagementPage from './pages/EmailManagementPage';
import WebhooksPage from './pages/WebhooksPage';
import APIKeysPage from './pages/APIKeysPage';
import WebSocketSettingsPage from './pages/WebSocketSettingsPage';

// Other Module Pages
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
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Initialize WebSocket connection when user logs in
  useEffect(() => {
    if (isAuthenticated && user) {
      const token = localStorage.getItem('access_token');
      if (token) {
        console.log('Initializing WebSocket connection...');
        websocketService.connect(token);
      }
    } else {
      // Disconnect when user logs out
      console.log('Disconnecting WebSocket...');
      websocketService.disconnect();
    }

    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
    };
  }, [user, isAuthenticated]);

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

        {/* Communication Module Routes */}
        <Route path="communication/telegram" element={<TelegramSettings />} />
        <Route path="communication/smtp" element={<EmailManagementPage />} />
        <Route path="communication/webhooks" element={<WebhooksPage />} />
        <Route path="communication/api-keys" element={<APIKeysPage />} />
        <Route path="communication/websockets" element={<WebSocketSettingsPage />} />

        {/* Other Module Routes */}
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

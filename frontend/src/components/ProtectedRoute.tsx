import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/authStore';

interface ProtectedRouteProps {
    children: React.ReactNode;
    allowChangePassword?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowChangePassword = false }) => {
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

    return <>{children}</>;
};

export default ProtectedRoute;

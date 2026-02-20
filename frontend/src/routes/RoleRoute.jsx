import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { ROUTES } from './routeConfig';

/**
 * A wrapper for <Route> that checks if the authenticated user has an allowed role.
 * Fallback redirects to DASHBOARD if unauthorized.
 */
const RoleRoute = ({ allowedRoles = [] }) => {
    const { user, isAuthenticated } = useSelector((state) => state.auth);

    if (!isAuthenticated) {
        return <Navigate to={ROUTES.LOGIN} replace />;
    }

    if (user && allowedRoles.includes(user.role)) {
        return <Outlet />;
    }

    // Role unauthorized, kick back to dashboard to prevent snooping
    return <Navigate to={ROUTES.DASHBOARD} replace />;
};

export default RoleRoute;

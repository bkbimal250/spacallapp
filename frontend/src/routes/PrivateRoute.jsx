import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { ROUTES } from './routeConfig';

const PrivateRoute = () => {
    const { isAuthenticated } = useSelector((state) => state.auth);

    // For development/mocking purposes, we might want to bypass this or check a token
    // const isAuthenticated = true; // Uncomment to bypass auth check during dev

    return isAuthenticated ? <Outlet /> : <Navigate to={ROUTES.LOGIN} replace />;
};

export default PrivateRoute;

import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import PrivateRoute from './PrivateRoute';
import RoleRoute from './RoleRoute';
import { ROUTES } from './routeConfig';
import DashboardLayout from '../layouts/DashboardLayout';
import AuthLayout from '../layouts/AuthLayout';

// Lazy load pages
const Login = lazy(() => import('../modules/auth/pages/Login'));
const DashboardHome = lazy(() => import('../modules/dashboard/pages/DashboardHome'));
const UserList = lazy(() => import('../modules/users/pages/UserList'));
const BranchList = lazy(() => import('../modules/branches/pages/BranchList'));
const DeviceList = lazy(() => import('../modules/devices/pages/DeviceList'));
const CallLogList = lazy(() => import('../modules/calllogs/pages/CallLogList'));
const AnalyticsDashboard = lazy(() => import('../modules/analytics/pages/AnalyticsDashboard'));
const ExportHistory = lazy(() => import('../modules/exports/pages/ExportHistory'));
const DeviceHealth = lazy(() => import('../modules/monitoring/pages/DeviceHealth'));



const Loading = () => <div>Loading...</div>;

export const AppRoutes = () => {
    return (
        <Suspense fallback={<Loading />}>
            <Routes>
                {/* Public Routes */}
                <Route element={<AuthLayout />}>
                    <Route path={ROUTES.LOGIN} element={<Login />} />
                </Route>

                {/* Private Routes */}
                <Route element={<PrivateRoute />}>
                    <Route element={<DashboardLayout />}>
                        <Route path={ROUTES.DASHBOARD} element={<DashboardHome />} />
                        <Route path={ROUTES.BRANCHES} element={<BranchList />} />
                        <Route path={ROUTES.DEVICES} element={<DeviceList />} />
                        <Route path={ROUTES.CALLLOGS} element={<CallLogList />} />
                        <Route path={ROUTES.ANALYTICS} element={<AnalyticsDashboard />} />
                        <Route path={ROUTES.EXPORTS} element={<ExportHistory />} />
                        <Route path={ROUTES.MONITORING} element={<DeviceHealth />} />

                        {/* Super Admin Only Routes */}
                        <Route element={<RoleRoute allowedRoles={['super_admin']} />}>
                            <Route path={ROUTES.USERS} element={<UserList />} />
                        </Route>
                    </Route>

                </Route>

                {/* Catch all */}
                <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
            </Routes>
        </Suspense>
    );
};

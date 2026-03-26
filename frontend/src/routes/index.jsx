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
const GroupList = lazy(() => import('../modules/branches/pages/GroupList'));
const Branch = lazy(() => import('../modules/branches/pages/Branch'));
const DeviceList = lazy(() => import('../modules/devices/pages/DeviceList'));
const CallLogSummary = lazy(() => import('../modules/calllogs/pages/CallLogSummary'));
const CallLogList = lazy(() => import('../modules/calllogs/pages/CallLogList'));
const AnalyticsDashboard = lazy(() => import('../modules/analytics/pages/AnalyticsDashboard'));
const ExportHistory = lazy(() => import('../modules/exports/pages/ExportHistory'));
const DeviceHealth = lazy(() => import('../modules/monitoring/pages/DeviceHealth'));
const ContactList = lazy(() => import('../modules/contacts/pages/ContactList'));
const LeadManagementSummary = lazy(() => import('../modules/leadManagement/pages/LeadManagementSummary'));
const LeadManagementList = lazy(() => import('../modules/leadManagement/pages/LeadManagementList'));
const NotificationList = lazy(() => import('../modules/notifications/pages/NotificationList'));



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
                        {/* BRANCH SUB-MODULE WITH NESTED TABS */}
                        <Route path={ROUTES.BRANCHES} element={<Branch />}>
                            <Route index element={<BranchList />} />
                            <Route path="groups" element={<GroupList />} />
                        </Route>

                        <Route path={ROUTES.DEVICES} element={<DeviceList />} />
                        <Route path={ROUTES.CALLLOGS} element={<CallLogSummary />} />
                        <Route path={ROUTES.CALLLOG_DETAILS} element={<CallLogList />} />
                        <Route path={ROUTES.ANALYTICS} element={<AnalyticsDashboard />} />
                        <Route path={ROUTES.EXPORTS} element={<ExportHistory />} />
                        <Route path={ROUTES.MONITORING} element={<DeviceHealth />} />
                        <Route path={ROUTES.CONTACTS} element={<ContactList />} />
                        <Route path={ROUTES.LEAD_MANAGEMENT} element={<LeadManagementSummary />} />
                        <Route path={ROUTES.LEAD_MANAGEMENT_LIST} element={<LeadManagementList />} />
                        <Route path={ROUTES.NOTIFICATIONS} element={<NotificationList />} />

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

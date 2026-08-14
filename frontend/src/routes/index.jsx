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
const LoginRecords = lazy(() => import('../modules/users/pages/LoginRecords'));
const BranchList = lazy(() => import('../modules/branches/pages/BranchList'));
const GroupList = lazy(() => import('../modules/branches/pages/GroupList'));
const Branch = lazy(() => import('../modules/branches/pages/Branch'));
const BranchView = lazy(() => import('../modules/branches/pages/BranchView'));
const DeviceList = lazy(() => import('../modules/devices/pages/DeviceList'));
const CallLogSummary = lazy(() => import('../modules/calllogs/pages/CallLogSummary'));
const CallLogList = lazy(() => import('../modules/calllogs/pages/CallLogList'));
const CallRouting = lazy(() => import('../modules/CallRouting/pages/CallRouting'));
const AnalyticsDashboard = lazy(() => import('../modules/analytics/pages/AnalyticsDashboard'));
const ExportHistory = lazy(() => import('../modules/exports/pages/ExportHistory'));
const DeviceHealth = lazy(() => import('../modules/monitoring/pages/DeviceHealth'));
const ContactList = lazy(() => import('../modules/contacts/pages/ContactList'));
const LeadManagementSummary = lazy(() => import('../modules/leadManagement/pages/LeadManagementSummary'));
const LeadManagementList = lazy(() => import('../modules/leadManagement/pages/LeadManagementList'));
const Locations = lazy(() => import('../modules/locations/locations'));
const DoubleTickOverview = lazy(() => import('../modules/doubletick/pages/DoubleTickOverview'));
const DoubleTickConversations = lazy(() => import('../modules/doubletick/pages/DoubleTickConversations'));
const DoubleTickLeads = lazy(() => import('../modules/doubletick/pages/DoubleTickLeads'));
const DoubleTickAreas = lazy(() => import('../modules/doubletick/pages/DoubleTickAreas'));
const DoubleTickAreaMap = lazy(() => import('../modules/doubletick/pages/DoubleTickAreaMap'));
const BotsOverview = lazy(() => import('../modules/bots/pages/Overview'));
const BotsBuilder = lazy(() => import('../modules/bots/pages/Builder'));
const BotsFlows = lazy(() => import('../modules/bots/pages/Flows'));
const BotsNodes = lazy(() => import('../modules/bots/pages/Nodes'));
const BotsNodeOptions = lazy(() => import('../modules/bots/pages/NodeOptions'));
const BotsTransitions = lazy(() => import('../modules/bots/pages/Transitions'));
const BotsTriggers = lazy(() => import('../modules/bots/pages/Triggers'));
const BotsTemplates = lazy(() => import('../modules/bots/pages/Templates'));
const BotsDataSources = lazy(() => import('../modules/bots/pages/DataSources'));
const BotsHandoverRules = lazy(() => import('../modules/bots/pages/HandoverRules'));
const BotsFallbackRules = lazy(() => import('../modules/bots/pages/FallbackRules'));
const BotsSessions = lazy(() => import('../modules/bots/pages/Sessions'));
const BotsSessionVariables = lazy(() => import('../modules/bots/pages/SessionVariables'));
const BotsLogs = lazy(() => import('../modules/bots/pages/Logs'));
const BotsApiCallLogs = lazy(() => import('../modules/bots/pages/ApiCallLogs'));
const BotsSheetSyncLogs = lazy(() => import('../modules/bots/pages/SheetSyncLogs'));
const BotsIntegrations = lazy(() => import('../modules/bots/pages/Integrations'));
const BotsSimulator = lazy(() => import('../modules/bots/pages/Simulator'));
const NotificationList = lazy(() => import('../modules/notifications/pages/NotificationList'));
const WebLeadsDashboard = lazy(() => import('../modules/webleads/pages/WebLeadsDashboard'));
const WebsiteFormsPage = lazy(() => import('../modules/webleads/pages/WebsiteFormsPage'));
const WebsiteFormCreatePage = lazy(() => import('../modules/webleads/pages/WebsiteFormCreatePage'));
const WebsiteFormDetailPage = lazy(() => import('../modules/webleads/pages/WebsiteFormDetailPage'));
const WebsiteFormEditPage = lazy(() => import('../modules/webleads/pages/WebsiteFormEditPage'));
const WebsiteLeadsPage = lazy(() => import('../modules/webleads/pages/WebsiteLeadsPage'));
const WebsiteLeadDetailPage = lazy(() => import('../modules/webleads/pages/WebsiteLeadDetailPage'));
const PendingWebsiteLeadsPage = lazy(() => import('../modules/webleads/pages/PendingWebsiteLeadsPage'));
const WebLeadAnalyticsPage = lazy(() => import('../modules/webleads/pages/WebLeadAnalyticsPage'));
const BranchWebsitePerformancePage = lazy(() => import('../modules/webleads/pages/BranchWebsitePerformancePage'));
const IntegrationHelpPage = lazy(() => import('../modules/webleads/pages/IntegrationHelpPage'));




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
                            <Route path=":id" element={<BranchView />} />
                        </Route>

                        <Route path={ROUTES.DEVICES} element={<DeviceList />} />
                        <Route path={ROUTES.CALLLOGS} element={<CallLogSummary />} />
                        <Route path={ROUTES.CALLLOG_DETAILS} element={<CallLogList />} />
                        <Route path={ROUTES.CALL_ROUTING} element={<CallRouting />} />
                        <Route path={ROUTES.ANALYTICS} element={<AnalyticsDashboard />} />
                        <Route path={ROUTES.EXPORTS} element={<ExportHistory />} />
                        <Route path={ROUTES.MONITORING} element={<DeviceHealth />} />
                        <Route path={ROUTES.CONTACTS} element={<ContactList />} />
                        <Route path={ROUTES.LEAD_MANAGEMENT} element={<LeadManagementSummary />} />
                        <Route path={ROUTES.LEAD_MANAGEMENT_LIST} element={<LeadManagementList />} />
                        <Route path={ROUTES.LOCATIONS} element={<Locations />} />
                        <Route path={ROUTES.DOUBLETICK} element={<DoubleTickOverview />} />
                        <Route path={ROUTES.DOUBLETICK_CONVERSATIONS} element={<DoubleTickConversations />} />
                        <Route path={ROUTES.DOUBLETICK_LEADS} element={<DoubleTickLeads />} />
                        <Route path={ROUTES.DOUBLETICK_AREAS} element={<DoubleTickAreas />} />
                        <Route path={ROUTES.DOUBLETICK_AREA_MAP} element={<DoubleTickAreaMap />} />
                        <Route path={ROUTES.BOTS} element={<BotsOverview />} />
                        <Route path={ROUTES.BOTS_BUILDER} element={<BotsBuilder />} />
                        <Route path={ROUTES.BOTS_BUILDER_FULLSCREEN} element={<BotsBuilder />} />
                        <Route path={ROUTES.BOTS_FLOWS} element={<BotsFlows />} />
                        <Route path={ROUTES.BOTS_NODES} element={<BotsNodes />} />
                        <Route path={ROUTES.BOTS_NODE_OPTIONS} element={<BotsNodeOptions />} />
                        <Route path={ROUTES.BOTS_TRANSITIONS} element={<BotsTransitions />} />
                        <Route path={ROUTES.BOTS_TRIGGERS} element={<BotsTriggers />} />
                        <Route path={ROUTES.BOTS_TEMPLATES} element={<BotsTemplates />} />
                        <Route path={ROUTES.BOTS_DATA_SOURCES} element={<BotsDataSources />} />
                        <Route path={ROUTES.BOTS_HANDOVER_RULES} element={<BotsHandoverRules />} />
                        <Route path={ROUTES.BOTS_FALLBACK_RULES} element={<BotsFallbackRules />} />
                        <Route path={ROUTES.BOTS_SESSIONS} element={<BotsSessions />} />
                        <Route path={ROUTES.BOTS_SESSION_VARIABLES} element={<BotsSessionVariables />} />
                        <Route path={ROUTES.BOTS_LOGS} element={<BotsLogs />} />
                        <Route path={ROUTES.BOTS_API_CALL_LOGS} element={<BotsApiCallLogs />} />
                        <Route path={ROUTES.BOTS_SHEET_SYNC_LOGS} element={<BotsSheetSyncLogs />} />
                        <Route path={ROUTES.BOTS_INTEGRATIONS} element={<BotsIntegrations />} />
                        <Route path={ROUTES.BOTS_SIMULATOR} element={<BotsSimulator />} />
                        <Route path={ROUTES.NOTIFICATIONS} element={<NotificationList />} />
                        <Route path="/web-leads" element={<Navigate to={ROUTES.WEB_LEADS_DASHBOARD} replace />} />
                        <Route path={ROUTES.WEB_LEADS_DASHBOARD} element={<WebLeadsDashboard />} />
                        <Route path={ROUTES.WEB_LEADS_FORMS} element={<WebsiteFormsPage />} />
                        <Route path={ROUTES.WEB_LEADS_FORM_CREATE} element={<WebsiteFormCreatePage />} />
                        <Route path={ROUTES.WEB_LEADS_FORM_DETAIL} element={<WebsiteFormDetailPage />} />
                        <Route path={ROUTES.WEB_LEADS_FORM_EDIT} element={<WebsiteFormEditPage />} />
                        <Route path={ROUTES.WEB_LEADS_LEADS} element={<WebsiteLeadsPage />} />
                        <Route path={ROUTES.WEB_LEADS_LEAD_DETAIL} element={<WebsiteLeadDetailPage />} />
                        <Route path={ROUTES.WEB_LEADS_PENDING} element={<PendingWebsiteLeadsPage />} />
                        <Route path={ROUTES.WEB_LEADS_ANALYTICS} element={<WebLeadAnalyticsPage />} />
                        <Route path={ROUTES.WEB_LEADS_BRANCH_PERFORMANCE} element={<BranchWebsitePerformancePage />} />
                        <Route path={ROUTES.WEB_LEADS_INTEGRATION_HELP} element={<IntegrationHelpPage />} />

                        {/* Super Admin Only Routes */}
                        <Route element={<RoleRoute allowedRoles={['super_admin']} />}>
                            <Route path={ROUTES.USERS} element={<UserList />} />
                            <Route path={ROUTES.USERS_LOGIN_HISTORY} element={<LoginRecords />} />
                        </Route>
                    </Route>

                </Route>

                {/* Catch all */}
                <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
            </Routes>
        </Suspense>
    );
};

import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { ROUTES } from '../../routes/routeConfig';
import { logout } from '../../store/slices/authSlice';
import { removeToken, removeUser } from '../../shared/services/tokenService';

import {
    LayoutDashboard,
    GitBranch,
    Layers,
    Smartphone,
    PhoneCall,
    Activity,
    BarChart3,
    Download,
    Users,
    LogOut,
    Bell,
    Contact,
    Briefcase,
    MessageCircle,
    Workflow,
    MapPinned,
    X
} from 'lucide-react';

const Sidebar = ({ collapsed = false, mobileOpen = false, onMobileClose }) => {

    const { user } = useSelector((state) => state.auth);
    const dispatch = useDispatch();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        removeToken();
        removeUser();
        dispatch(logout());
        navigate(ROUTES.LOGIN);
    };

    const navItems = [
        { to: ROUTES.DASHBOARD, label: 'Dashboard', icon: LayoutDashboard },
        { to: ROUTES.BRANCHES, label: 'Branches', icon: GitBranch },
        { to: ROUTES.BRANCH_GROUPS, label: 'Branch Groups', icon: Layers },
        { to: ROUTES.DEVICES, label: 'Devices', icon: Smartphone },
        { to: ROUTES.CALLLOGS, label: 'Call Logs', icon: PhoneCall },
        { to: ROUTES.MONITORING, label: 'Monitoring', icon: Activity },
        { to: ROUTES.ANALYTICS, label: 'Analytics', icon: BarChart3 },
        { to: ROUTES.EXPORTS, label: 'Exports', icon: Download },
        { to: ROUTES.CONTACTS, label: 'Contacts', icon: Contact },
        { to: ROUTES.LEAD_MANAGEMENT, label: 'Lead Management', icon: Briefcase },
        { to: ROUTES.LOCATIONS, label: 'Locations', icon: MapPinned },
        { to: ROUTES.DOUBLETICK, label: 'DoubleTick', icon: MessageCircle },
        { to: ROUTES.BOTS, label: 'Bot Builder', icon: Workflow },
        { to: ROUTES.NOTIFICATIONS, label: 'Notifications', icon: Bell },
    ];

    return (
        <>
            {mobileOpen && (
                <button
                    type="button"
                    aria-label="Close sidebar"
                    onClick={onMobileClose}
                    className="fixed inset-0 z-40 bg-black/50 lg:hidden"
                />
            )}

            <aside
                className={`fixed inset-y-0 left-0 z-50 flex h-screen w-64 shrink-0 flex-col border-r border-border bg-sidebar text-text-primary transition-all duration-300 ease-in-out lg:static lg:translate-x-0 ${
                    mobileOpen ? 'translate-x-0' : '-translate-x-full'
                } ${collapsed ? 'lg:w-20' : 'lg:w-64'}`}
            >

            {/* LOGO */}
            <div className={`flex h-16 shrink-0 items-center border-b border-border ${collapsed ? 'lg:justify-center lg:px-2' : 'px-6'}`}>

                <span className="truncate text-lg font-semibold text-primary">
                    <span className={collapsed ? 'lg:hidden' : ''}>Master Call</span>
                    <span className={collapsed ? 'hidden lg:inline' : 'hidden'}>MC</span>
                </span>

                <button
                    type="button"
                    onClick={onMobileClose}
                    className="ml-auto rounded-lg p-1.5 text-text-secondary hover:bg-card hover:text-text-primary lg:hidden"
                    aria-label="Close sidebar"
                >
                    <X size={20} />
                </button>
            </div>

            {/* NAVIGATION */}
            <nav className={`custom-scrollbar min-h-0 flex-1 space-y-1 overflow-y-auto ${collapsed ? 'lg:px-3' : ''} p-4`}>

                {navItems.map((item) => {

                    const isActive = location.pathname === item.to || (item.to !== ROUTES.DASHBOARD && location.pathname.startsWith(item.to));

                    return (
                        <Link
                            key={item.to}
                            to={item.to}
                            onClick={onMobileClose}
                            title={collapsed ? item.label : undefined}
                            className={`flex items-center gap-3 rounded-lg px-4 py-2.5 transition-all ${collapsed ? 'lg:justify-center lg:px-2' : ''}
                                
                                ${isActive
                                    ? "bg-primary/20 text-primary"
                                    : "text-text-secondary hover:bg-card hover:text-text-primary"}
                                
                            `}
                        >
                            <item.icon size={18} className="shrink-0" />

                            <span className={`whitespace-nowrap text-sm font-medium ${collapsed ? 'lg:hidden' : ''}`}>
                                {item.label}
                            </span>
                        </Link>
                    );
                })}

                {/* USERS (ROLE BASED) */}
                {(user?.role === 'super_admin' || user?.role === 'admin') && (

                    <Link
                        to={ROUTES.USERS}
                        onClick={onMobileClose}
                        title={collapsed ? 'Users' : undefined}
                        className={`flex items-center gap-3 rounded-lg px-4 py-2.5 text-warning transition hover:bg-card ${collapsed ? 'lg:justify-center lg:px-2' : ''}`}
                    >

                        <Users size={18} className="shrink-0" />

                        <span className={`whitespace-nowrap text-sm font-medium ${collapsed ? 'lg:hidden' : ''}`}>
                            Users
                        </span>

                    </Link>

                )}

            </nav>

            {/* LOGOUT */}
            <div className="shrink-0 border-t border-border p-4">

                <button
                    onClick={handleLogout}
                    title={collapsed ? 'Logout' : undefined}
                    className={`flex w-full items-center gap-3 rounded-lg px-4 py-2.5 text-text-secondary transition hover:bg-danger/10 hover:text-danger ${collapsed ? 'lg:justify-center lg:px-2' : ''}`}
                >

                    <LogOut size={18} className="shrink-0" />

                    <span className={`whitespace-nowrap text-sm font-medium ${collapsed ? 'lg:hidden' : ''}`}>
                        Logout
                    </span>

                </button>

            </div>

            </aside>
        </>
    );
};

export default Sidebar;

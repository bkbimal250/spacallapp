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
    MapPinned
} from 'lucide-react';

const Sidebar = () => {

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
        <aside className="w-64 bg-sidebar border-r border-border text-text-primary flex flex-col">

            {/* LOGO */}
            <div className="h-16 flex items-center px-6 border-b border-border">

                <span className="text-lg font-semibold text-primary">
                    Call Monitoring
                </span>

            </div>

            {/* NAVIGATION */}
            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">

                {navItems.map((item) => {

                    const isActive = location.pathname === item.to || (item.to !== ROUTES.DASHBOARD && location.pathname.startsWith(item.to));

                    return (
                        <Link
                            key={item.to}
                            to={item.to}
                            className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all
                                
                                ${isActive
                                    ? "bg-primary/20 text-primary"
                                    : "text-text-secondary hover:bg-card hover:text-text-primary"}
                                
                            `}
                        >
                            <item.icon size={18} />

                            <span className="text-sm font-medium">
                                {item.label}
                            </span>
                        </Link>
                    );
                })}

                {/* USERS (ROLE BASED) */}
                {(user?.role === 'super_admin' || user?.role === 'admin') && (

                    <Link
                        to={ROUTES.USERS}
                        className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-warning hover:bg-card transition"
                    >

                        <Users size={18} />

                        <span className="text-sm font-medium">
                            Users
                        </span>

                    </Link>

                )}

            </nav>

            {/* LOGOUT */}
            <div className="p-4 border-t border-border">

                <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-3 px-4 py-2.5 rounded-lg text-text-secondary hover:bg-danger/10 hover:text-danger transition"
                >

                    <LogOut size={18} />

                    <span className="text-sm font-medium">
                        Logout
                    </span>

                </button>

            </div>

        </aside>
    );
};

export default Sidebar;

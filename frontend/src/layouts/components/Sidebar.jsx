import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { ROUTES } from '../../routes/routeConfig';
import { logout } from '../../store/slices/authSlice';
import { removeToken, removeUser } from '../../shared/services/tokenService';
import {
    LayoutDashboard,
    GitBranch,
    Smartphone,
    PhoneCall,
    Activity,
    BarChart3,
    Download,
    Users,
    LogOut
} from 'lucide-react';

const Sidebar = () => {
    const { user } = useSelector((state) => state.auth);
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const handleLogout = () => {
        removeToken();
        removeUser();
        dispatch(logout());
        navigate(ROUTES.LOGIN);
    };

    const navItems = [
        { to: ROUTES.DASHBOARD, label: 'Dashboard', icon: LayoutDashboard },
        { to: ROUTES.BRANCHES, label: 'Branches', icon: GitBranch },
        { to: ROUTES.DEVICES, label: 'Devices', icon: Smartphone },
        { to: ROUTES.CALLLOGS, label: 'Call Logs', icon: PhoneCall },
        { to: ROUTES.MONITORING, label: 'Monitoring', icon: Activity },
        { to: ROUTES.ANALYTICS, label: 'Analytics', icon: BarChart3 },
        { to: ROUTES.EXPORTS, label: 'Exports', icon: Download },
    ];

    return (
        <div className="w-64 bg-gray-900 text-white flex flex-col">
            <div className="p-6 text-xl font-bold border-b border-gray-800 flex items-center space-x-2 text-indigo-400">
                <span>CallLog Admin</span>
            </div>

            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                {navItems.map((item) => (
                    <Link
                        key={item.to}
                        to={item.to}
                        className="flex items-center space-x-3 py-2.5 px-4 rounded-lg transition duration-200 hover:bg-gray-800 hover:text-indigo-400"
                    >
                        <item.icon size={20} />
                        <span>{item.label}</span>
                    </Link>
                ))}

                {/* Role Based Rendering: Only super_admin can see the Users Management tab */}
                {user?.role === 'super_admin' && (
                    <Link
                        to={ROUTES.USERS}
                        className="flex items-center space-x-3 py-2.5 px-4 rounded-lg transition duration-200 hover:bg-gray-800 hover:text-indigo-400 text-yellow-500"
                    >
                        <Users size={20} />
                        <span>Users</span>
                    </Link>
                )}
            </nav>

            <div className="p-4 border-t border-gray-800">
                <button
                    onClick={handleLogout}
                    className="flex w-full items-center space-x-3 py-2.5 px-4 rounded-lg transition duration-200 hover:bg-red-900/30 text-gray-400 hover:text-red-500"
                >
                    <LogOut size={20} />
                    <span>Logout</span>
                </button>
            </div>
        </div>
    );
};

export default Sidebar;


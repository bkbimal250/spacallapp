import React from 'react';
import { Link } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { ROUTES } from '../../routes/routeConfig';

const Sidebar = () => {
    const { user } = useSelector((state) => state.auth);
    return (
        <div className="w-64 bg-gray-900 text-white flex flex-col">
            <div className="p-4 text-xl font-bold border-b border-gray-800">
                Admin Panel
            </div>
            <nav className="flex-1 p-4 space-y-2">
                <Link to={ROUTES.DASHBOARD} className="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-800">
                    Dashboard
                </Link>
                <Link to={ROUTES.BRANCHES} className="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-800">
                    Branches
                </Link>
                <Link to={ROUTES.DEVICES} className="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-800">
                    Devices
                </Link>
                <Link to={ROUTES.CALLLOGS} className="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-800">
                    Call Logs
                </Link>
                <Link to={ROUTES.MONITORING} className="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-800">
                    Monitoring
                </Link>
                <Link to={ROUTES.ANALYTICS} className="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-800">
                    Analytics
                </Link>
                <Link to={ROUTES.EXPORTS} className="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-800">
                    Exports
                </Link>
                {/* Role Based Rendering: Only super_admin can see the Users Management tab */}
                {user?.role === 'super_admin' && (
                    <Link to={ROUTES.USERS} className="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-800">
                        Users
                    </Link>
                )}

            </nav>
        </div>
    );
};

export default Sidebar;

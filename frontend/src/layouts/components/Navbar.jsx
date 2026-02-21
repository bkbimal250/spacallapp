import React, { useState, useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import {
    Bell,
    User,
    ShieldCheck,
    Smartphone,
    AlertTriangle,
    CheckCircle2,
    WifiOff,
    BatteryLow,
    CircleDot
} from 'lucide-react';
import { monitoringAPI } from '../../modules/monitoring/api';
import { formatDate } from '../../shared/utils/formatDate';

const Navbar = () => {
    const { user } = useSelector((state) => state.auth);
    const [notifications, setNotifications] = useState([]);
    const [showNotifications, setShowNotifications] = useState(false);
    const [loading, setLoading] = useState(false);
    const notificationRef = useRef(null);

    const fetchNotifications = async () => {
        setLoading(true);
        try {
            const response = await monitoringAPI.getAlerts();
            // Data might be in .results if paginated
            const data = response.data.results || response.data;
            // Filter unresolved alerts
            const unresolved = data.filter(n => !n.resolved);
            setNotifications(unresolved.slice(0, 8)); // Show up to 8 recent alerts
        } catch (error) {
            console.error("Failed to fetch notifications", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 30000); // Faster polling (30s)
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (notificationRef.current && !notificationRef.current.contains(event.target)) {
                setShowNotifications(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const getEventDetails = (type) => {
        switch (type) {
            case 'offline': return { icon: <WifiOff className="text-red-500" size={18} />, label: 'Device Disconnected' };
            case 'battery_low': return { icon: <BatteryLow className="text-orange-500" size={18} />, label: 'Low Battery Alert' };
            case 'sim_change': return { icon: <Smartphone className="text-purple-500" size={18} />, label: 'SIM Configuration Change' };
            default: return { icon: <CircleDot className="text-indigo-500" size={18} />, label: 'System Event' };
        }
    };

    return (
        <header className="bg-white/80 backdrop-blur-md border-b border-gray-100 h-16 flex justify-between items-center px-8 sticky top-0 z-40">
            <div className="flex items-center space-x-4">
                <div className="flex flex-col">
                    <div className="flex items-center space-x-2">
                        <span className="text-sm font-bold text-gray-900 leading-tight">
                            {user?.full_name || 'Admin'}
                        </span>
                        <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse"></div>
                    </div>
                    <span className="text-[10px] text-indigo-600 font-bold uppercase tracking-widest flex items-center">
                        <ShieldCheck size={10} className="mr-1" />
                        {user?.role?.replace('_', ' ') || 'Super Admin'}
                    </span>
                </div>
            </div>

            <div className="flex items-center space-x-6">
                {/* Notifications Dropdown */}
                <div className="relative" ref={notificationRef}>
                    <button
                        onClick={() => setShowNotifications(!showNotifications)}
                        className={`p-2.5 rounded-xl transition-all duration-300 relative ${showNotifications ? 'bg-indigo-50 text-indigo-600 shadow-inner' : 'text-gray-400 hover:text-indigo-600 hover:bg-gray-50'
                            }`}
                    >
                        <Bell size={20} className={notifications.length > 0 ? 'animate-swing' : ''} />
                        {notifications.length > 0 && (
                            <span className="absolute top-2 right-2 block h-2.5 w-2.5 rounded-full bg-red-500 border-2 border-white"></span>
                        )}
                    </button>

                    {showNotifications && (
                        <div className="absolute right-0 mt-4 w-96 bg-white rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.15)] border border-gray-100 overflow-hidden z-50 animate-in fade-in slide-in-from-top-4 duration-300">
                            <div className="p-5 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100 flex justify-between items-center">
                                <div>
                                    <h3 className="font-extrabold text-gray-900 text-base">Security Alerts</h3>
                                    <p className="text-[10px] text-gray-400 uppercase tracking-tighter">Real-time device monitoring</p>
                                </div>
                                {notifications.length > 0 && (
                                    <span className="bg-red-50 text-red-600 text-[10px] font-black px-2 py-0.5 rounded-full">
                                        {notifications.length} NEW
                                    </span>
                                )}
                            </div>

                            <div className="max-h-[32rem] overflow-y-auto custom-scrollbar">
                                {notifications.length === 0 ? (
                                    <div className="p-12 text-center">
                                        <div className="bg-green-50 text-green-500 h-16 w-16 rounded-full flex items-center justify-center mx-auto mb-4">
                                            <CheckCircle2 size={32} />
                                        </div>
                                        <p className="text-sm font-bold text-gray-900">All systems operational</p>
                                        <p className="text-xs text-gray-400 mt-1">No critical alerts detected in your network.</p>
                                    </div>
                                ) : (
                                    notifications.map((n) => {
                                        const { icon, label } = getEventDetails(n.event_type);
                                        return (
                                            <div key={n.id} className="p-4 border-b border-gray-50 hover:bg-indigo-50/30 transition-all cursor-default group">
                                                <div className="flex space-x-4">
                                                    <div className="mt-1 transition-transform group-hover:scale-110 duration-200">
                                                        {icon}
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="flex justify-between items-start">
                                                            <p className="text-sm font-bold text-gray-900 leading-none">
                                                                {label}
                                                            </p>
                                                            <span className="text-[10px] text-gray-400 font-medium">
                                                                {formatDate(n.created_at)}
                                                            </span>
                                                        </div>
                                                        <p className="text-xs text-gray-600 mt-1.5 leading-relaxed">
                                                            Device <span className="font-mono text-indigo-600 bg-indigo-50 px-1 rounded">{n.device_uid}</span> {n.description}
                                                        </p>
                                                        {n.branch_name && (
                                                            <div className="mt-2 flex items-center text-[10px] text-gray-400">
                                                                <CircleDot size={8} className="mr-1 text-gray-300" />
                                                                {n.branch_name}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>

                            <div className="p-4 bg-gray-50/50 text-center">
                                <button className="text-[11px] font-black text-indigo-600 hover:text-indigo-800 uppercase tracking-widest transition-colors">
                                    View Monitoring Dashboard
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* User Profile Info */}
                <div className="flex items-center space-x-4 border-l pl-6 border-gray-100">
                    <div className="text-right hidden lg:block">
                        <p className="text-xs font-black text-gray-900 tracking-tight leading-none">{user?.email}</p>
                        <p className="text-[9px] text-green-500 mt-1.5 uppercase font-bold flex items-center justify-end">
                            <span className="h-1 w-1 bg-green-500 rounded-full mr-1"></span>
                            Verified Account
                        </p>
                    </div>
                    <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-700 shadow-[0_10px_20px_-5px_rgba(79,70,229,0.4)] flex items-center justify-center text-white font-black text-lg transition-transform hover:scale-105 duration-200 cursor-pointer">
                        {user?.full_name?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || 'A'}
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Navbar;



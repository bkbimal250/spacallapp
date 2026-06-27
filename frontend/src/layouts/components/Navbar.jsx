import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
    Bell,
    AlertTriangle,
    ShieldCheck,
    Smartphone,
    WifiOff,
    BatteryLow,
    CircleDot,
    Check,
    Trash2,
    CheckCircle2,
    Menu,
    PanelLeftClose,
    PanelLeftOpen
} from 'lucide-react';
import { monitoringAPI } from '../../modules/monitoring/api';
import { formatDate } from '../../shared/utils/formatDate';

const Navbar = ({ sidebarCollapsed = false, onToggleSidebar, onOpenMobileSidebar }) => {

    const { user } = useSelector((state) => state.auth);

    const [notifications, setNotifications] = useState([]);
    const [showNotifications, setShowNotifications] = useState(false);

    const notificationRef = useRef(null);

    const fetchNotifications = async () => {
        try {
            const response = await monitoringAPI.getAlerts({ resolved: false });
            const data = response.data.results || response.data;
            setNotifications(data.slice(0, 8));
        } catch (error) {
            console.error("Failed to fetch notifications", error);
        }
    };

    const handleResolve = async (id, e) => {
        e?.stopPropagation();
        try {
            await monitoringAPI.resolveAlert(id);
            setNotifications(notifications.filter(n => n.id !== id));
        } catch (error) {
            console.error("Resolve failed", error);
        }
    };

    const handleResolveAll = async () => {
        try {
            await monitoringAPI.resolveAllAlerts();
            setNotifications([]);
        } catch (error) {
            console.error("Resolve all failed", error);
        }
    };

    const handleDelete = async (id, e) => {
        e?.stopPropagation();
        try {
            await monitoringAPI.deleteAlert(id);
            setNotifications(notifications.filter(n => n.id !== id));
        } catch (error) {
            console.error("Delete failed", error);
        }
    };

    useEffect(() => {
        const initialFetch = setTimeout(fetchNotifications, 0);
        const interval = setInterval(fetchNotifications, 30000);
        return () => {
            clearTimeout(initialFetch);
            clearInterval(interval);
        };
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
            case 'offline':
                return { icon: <WifiOff size={16} className="text-danger" />, label: 'Device Offline' };
            case 'app_uninstall_suspected':
                return { icon: <AlertTriangle size={16} className="text-danger" />, label: 'Possible App Uninstall' };
            case 'battery_low':
                return { icon: <BatteryLow size={16} className="text-warning" />, label: 'Battery Low' };
            case 'sim_change':
                return { icon: <Smartphone size={16} className="text-accent-purple" />, label: 'SIM Changed' };
            default:
                return { icon: <CircleDot size={16} className="text-primary" />, label: 'System Event' };
        }
    };

    const handleNotificationToggle = async () => {
        if (!showNotifications) {
            await fetchNotifications();
        }
        setShowNotifications((prev) => !prev);
    };

    return (
        <header className="z-30 flex h-16 shrink-0 items-center justify-between border-b border-border bg-sidebar px-3 sm:px-4 lg:px-6">

            {/* USER INFO */}
            <div className="flex min-w-0 items-center gap-3">

                <button
                    type="button"
                    onClick={onOpenMobileSidebar}
                    className="rounded-lg p-2 text-text-secondary transition hover:bg-card hover:text-text-primary lg:hidden"
                    aria-label="Open sidebar"
                >
                    <Menu size={20} />
                </button>

                <button
                    type="button"
                    onClick={onToggleSidebar}
                    className="hidden rounded-lg p-2 text-text-secondary transition hover:bg-card hover:text-text-primary lg:inline-flex"
                    aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                    {sidebarCollapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
                </button>

                <div className="min-w-0 flex flex-col">

                    <span className="truncate text-sm font-semibold text-text-primary">
                        {user?.full_name || "Admin"}
                    </span>

                    <span className="flex items-center text-xs text-primary font-medium">
                        <ShieldCheck size={12} className="mr-1" />
                        {user?.role?.replace('_', ' ') || "Super Admin"}
                    </span>

                </div>

            </div>

            {/* RIGHT SECTION */}
            <div className="flex shrink-0 items-center gap-2 sm:gap-4 lg:gap-6">

                {/* NOTIFICATIONS */}
                <div className="relative" ref={notificationRef}>

                    <button
                        onClick={handleNotificationToggle}
                        className="relative p-2 rounded-lg hover:bg-card transition"
                        aria-label="Notifications"
                        title="Notifications"
                    >

                        <Bell size={20} className="text-text-secondary" />

                        {notifications.length > 0 && (
                            <span className="absolute -top-1 -right-1 bg-danger text-white text-[10px] h-4 w-4 flex items-center justify-center rounded-full">
                                {notifications.length}
                            </span>
                        )}

                    </button>

                    {showNotifications && (
                        <div className="absolute right-0 mt-4 w-[min(24rem,calc(100vw-1.5rem))] overflow-hidden rounded-xl border border-border bg-card shadow-2xl">

                            {/* HEADER */}
                            <div className="flex items-center justify-between px-4 py-3 border-b border-border">

                                <div>
                                    <p className="font-semibold text-text-primary">
                                        Notifications
                                    </p>

                                    <p className="text-xs text-text-muted">
                                        Recent system alerts
                                    </p>
                                </div>

                                {notifications.length > 0 && (
                                    <button
                                        onClick={handleResolveAll}
                                        className="text-xs text-primary hover:text-primary-hover font-medium"
                                    >
                                        Mark all read
                                    </button>
                                )}

                            </div>

                            {/* BODY */}
                            <div className="max-h-[420px] overflow-y-auto">

                                {notifications.length === 0 && (
                                    <div className="p-10 text-center">

                                        <CheckCircle2 size={36} className="text-success mx-auto mb-3" />

                                        <p className="text-sm font-medium text-text-primary">
                                            All clear
                                        </p>

                                        <p className="text-xs text-text-muted">
                                            No alerts right now
                                        </p>

                                    </div>
                                )}

                                {notifications.map((n) => {

                                    const { icon, label } = getEventDetails(n.event_type);

                                    return (
                                        <div
                                            key={n.id}
                                            className="flex gap-3 px-4 py-3 border-b border-border hover:bg-background group"
                                        >

                                            <div className="mt-1">
                                                {icon}
                                            </div>

                                            <div className="flex-1">

                                                <div className="flex justify-between">

                                                    <p className="text-sm font-medium text-text-primary">
                                                        {label}
                                                    </p>

                                                    <span className="text-xs text-text-muted">
                                                        {formatDate(n.created_at)}
                                                    </span>

                                                </div>

                                                <p className="text-xs text-text-secondary mt-1">
                                                    Device <span className="font-mono text-primary">{n.device_uid}</span> {n.description}
                                                </p>

                                                {n.branch_name && (
                                                    <p className="text-[11px] text-text-muted mt-1">
                                                        {n.branch_name}
                                                    </p>
                                                )}

                                            </div>

                                            <div className="flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition">

                                                <button
                                                    onClick={(e) => handleResolve(n.id, e)}
                                                    className="p-1 rounded-md bg-success/10 text-success hover:bg-success/20"
                                                >
                                                    <Check size={14} />
                                                </button>

                                                <button
                                                    onClick={(e) => handleDelete(n.id, e)}
                                                    className="p-1 rounded-md bg-danger/10 text-danger hover:bg-danger/20"
                                                >
                                                    <Trash2 size={14} />
                                                </button>

                                            </div>

                                        </div>
                                    );
                                })}
                            </div>

                            {/* FOOTER */}
                            <div className="text-center p-3 bg-background border-t border-border">

                                <Link
                                    to="/notifications"
                                    className="text-xs text-primary font-medium hover:text-primary-hover"
                                >
                                    View all notifications
                                </Link>

                            </div>

                        </div>
                    )}

                </div>

                {/* PROFILE */}
                <div className="flex items-center gap-3 border-l border-border pl-3 sm:pl-4 lg:pl-6">

                    <div className="hidden md:block text-right">

                        <p className="text-xs font-medium text-text-primary">
                            {user?.email}
                        </p>

                        <p className="text-[10px] text-success">
                            Verified
                        </p>

                    </div>

                    <div className="h-9 w-9 rounded-full bg-primary text-white flex items-center justify-center font-semibold">
                        {user?.full_name?.charAt(0) ||
                            user?.email?.charAt(0)?.toUpperCase() ||
                            "A"}
                    </div>

                </div>

            </div>

        </header>
    );
};

export default Navbar;

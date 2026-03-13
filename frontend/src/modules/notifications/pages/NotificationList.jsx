import React, { useState, useEffect } from 'react';
import { notificationsAPI } from '../api';
import {
    Bell,
    Send,
    CheckCircle2,
    XCircle,
    RefreshCcw,
    Smartphone,
    Zap,
    Clock,
    ShieldAlert,
    Trash2
} from 'lucide-react';
import SendNotificationModal from '../components/SendNotificationModal';

import { branchesAPI } from '../../branches/api';
import { getUser } from '../../../shared/services/tokenService';

const NotificationList = () => {
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState({ total_sent: 0, delivery_rate: '0%', active_devices: 0 });
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [filter, setFilter] = useState('');
    const [branchFilter, setBranchFilter] = useState('');
    const [branches, setBranches] = useState([]);
    const [user, setUser] = useState(getUser());

    useEffect(() => {
        fetchLogs();
        fetchStats();
    }, [filter, branchFilter]);

    useEffect(() => {
        if (user?.role !== 'branch_manager') {
            fetchBranches();
        }
    }, [user]);

    const fetchBranches = async () => {
        try {
            const res = await branchesAPI.getBranches();
            setBranches(res.data.results || res.data || []);
        } catch (err) {
            console.error('Failed to fetch branches:', err);
        }
    };

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const res = await notificationsAPI.getLogs({ 
                type: filter,
                branch: branchFilter 
            });
            setLogs(res.data.results || res.data || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const res = await notificationsAPI.getStats();
            setStats(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSendNotification = async (data) => {
        try {
            const res = await notificationsAPI.sendManual(data);
            const { sent_count, total_count } = res.data;
            
            alert(`Successfully sent ${sent_count} of ${total_count} notifications.`);
            
            fetchLogs();
            fetchStats();
        } catch (err) {
            console.error('Failed to send notification:', err);
            const errorMsg = err.response?.data?.error || 'Failed to send notification. Please try again.';
            alert(errorMsg);
            throw err;
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Delete this notification log?')) return;
        try {
            await notificationsAPI.deleteLog(id);
            setLogs(logs.filter(log => log.id !== id));
        } catch (err) {
            console.error(err);
        }
    };

    const handleDeleteAll = async () => {
        if (!window.confirm('Clear ALL notification history?')) return;
        try {
            await notificationsAPI.deleteAllLogs();
            setLogs([]);
        } catch (err) {
            console.error(err);
        }
    };

    const getStatusIcon = (notif) => {
        if (notif.is_sent) return <CheckCircle2 className="text-success" size={16} />;
        return <XCircle className="text-danger" size={16} />;
    };

    const getTypeStyles = (type) => {
        switch (type) {
            case 'alert': return 'bg-warning/10 text-warning';
            case 'sync_issue': return 'bg-danger/10 text-danger';
            case 'reminder': return 'bg-primary/10 text-primary';
            default: return 'bg-info/10 text-info';
        }
    };

    return (
        <div className="p-8 space-y-8 bg-background min-h-screen text-text-primary">

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">

                <div className="flex items-center space-x-4">
                    <div className="bg-card p-3 rounded-xl border border-border">
                        <Bell className="text-primary" size={32} />
                    </div>

                    <div>
                        <h1 className="text-2xl font-bold text-text-primary">
                            Notification Center
                        </h1>
                        <p className="text-text-secondary text-sm">
                            Manage push alerts & delivery logs
                        </p>
                    </div>
                </div>

                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-primary text-white px-6 py-3 rounded-lg font-semibold flex items-center gap-2 hover:bg-primary-hover"
                >
                    <Send size={18} />
                    Send Alert
                </button>

            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                {[
                    { label: 'Total Sent', value: stats.total_sent, icon: Zap, color: 'text-primary' },
                    { label: 'Delivery Rate', value: stats.delivery_rate, icon: CheckCircle2, color: 'text-success' },
                    { label: 'Active Devices', value: stats.active_devices, icon: Smartphone, color: 'text-info' }
                ].map((stat, i) => (
                    <div key={i} className="bg-card p-6 rounded-xl border border-border flex items-center gap-4">

                        <div className="bg-background p-3 rounded-lg">
                            <stat.icon className={stat.color} size={22} />
                        </div>

                        <div>
                            <p className="text-xs text-text-secondary uppercase">{stat.label}</p>
                            <p className="text-xl font-semibold text-text-primary">{stat.value}</p>
                        </div>

                    </div>
                ))}

            </div>

            {/* Logs */}
            <div className="bg-card rounded-xl border border-border overflow-hidden">

                <div className="p-6 border-b border-border flex items-center justify-between">

                    <div className="flex gap-2">
                        <button
                            onClick={() => setFilter('')}
                            className={`px-4 py-1 rounded-full text-xs font-medium ${!filter ? 'bg-primary text-white' : 'bg-background text-text-secondary'}`}
                        >
                            All Types
                        </button>

                        {['system', 'reminder', 'alert', 'sync_issue'].map(t => (
                            <button
                                key={t}
                                onClick={() => setFilter(t)}
                                className={`px-4 py-1 rounded-full text-xs font-medium capitalize ${filter === t ? 'bg-primary text-white' : 'bg-background text-text-secondary'}`}
                            >
                                {t.replace('_', ' ')}
                            </button>
                        ))}

                        {user?.role !== 'branch_manager' && (
                            <select
                                value={branchFilter}
                                onChange={(e) => setBranchFilter(e.target.value)}
                                className="ml-4 bg-background border border-border rounded-full px-4 py-1 text-xs font-medium outline-none focus:border-primary"
                            >
                                <option value="">All Branches</option>
                                {branches.map(b => (
                                    <option key={b.id} value={b.id}>{b.spa_name}</option>
                                ))}
                            </select>
                        )}
                    </div>

                    <div className="flex items-center gap-3">

                        <button
                            onClick={handleDeleteAll}
                            className="flex items-center gap-1 px-3 py-2 text-danger bg-danger/10 rounded-md"
                        >
                            <Trash2 size={16} />
                            Clear
                        </button>

                        <button
                            onClick={fetchLogs}
                            className="p-2 bg-background rounded-md hover:bg-cardHover"
                        >
                            <RefreshCcw size={18} />
                        </button>

                    </div>

                </div>

                <div className="overflow-x-auto">

                    <table className="w-full text-sm">

                        <thead className="bg-background">
                            <tr className="text-text-secondary text-xs uppercase">
                                <th className="px-6 py-4 text-left">Device</th>
                                <th className="px-6 py-4 text-left">Notification</th>
                                <th className="px-6 py-4 text-left">Type</th>
                                <th className="px-6 py-4 text-left">Status</th>
                                <th className="px-6 py-4 text-left">Time</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-border">

                            {loading ? (
                                <tr>
                                    <td colSpan="6" className="text-center py-10 text-text-secondary">
                                        Loading notifications...
                                    </td>
                                </tr>
                            ) : logs.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="text-center py-16">
                                        <ShieldAlert className="mx-auto text-text-secondary mb-2" size={40} />
                                        <p className="text-text-secondary">No notification history</p>
                                    </td>
                                </tr>
                            ) : (
                                logs.map(log => (

                                    <tr key={log.id} className="hover:bg-background">

                                        <td className="px-6 py-4">

                                            <div className="flex items-center gap-3">

                                                <div className="w-9 h-9 bg-background rounded-lg flex items-center justify-center">
                                                    <Smartphone size={16} className="text-text-secondary" />
                                                </div>

                                                <div>
                                                    <p className="font-medium text-text-primary">{log.device_name}</p>
                                                    <p className="text-xs text-text-secondary">{log.branch_name}</p>
                                                </div>

                                            </div>

                                        </td>

                                        <td className="px-6 py-4 max-w-xs">
                                            <p className="font-medium">{log.title}</p>
                                            <p className="text-xs text-text-secondary truncate">{log.body}</p>
                                        </td>

                                        <td className="px-6 py-4">
                                            <span className={`px-3 py-1 rounded-full text-xs ${getTypeStyles(log.notification_type)}`}>
                                                {log.notification_type.replace('_', ' ')}
                                            </span>
                                        </td>

                                        <td className="px-6 py-4 flex items-center gap-2">
                                            {getStatusIcon(log)}
                                            <span className="text-xs">{log.is_sent ? 'Delivered' : 'Failed'}</span>
                                        </td>

                                        <td className="px-6 py-4 text-text-secondary text-xs flex items-center gap-1">
                                            <Clock size={14} />
                                            {new Date(log.created_at).toLocaleDateString()}{" "}
                                            {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </td>

                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => handleDelete(log.id)}
                                                className="p-2 text-text-secondary hover:text-danger"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </td>

                                    </tr>

                                ))
                            )}

                        </tbody>

                    </table>

                </div>

            </div>

            <SendNotificationModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSend={handleSendNotification}
            />

        </div>
    );
};

export default NotificationList;
import React, { useState, useEffect } from 'react';
import { notificationsAPI } from '../api';
import { Bell, Send, Filter, CheckCircle2, XCircle, RefreshCcw, Smartphone, Zap, Clock, ShieldAlert } from 'lucide-react';
import SendNotificationModal from '../components/SendNotificationModal';

const NotificationList = () => {
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState({ total_sent: 0, delivery_rate: '0%', active_devices: 0 });
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [filter, setFilter] = useState('');

    useEffect(() => {
        fetchLogs();
        fetchStats();
    }, [filter]);

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const res = await notificationsAPI.getLogs({ type: filter });
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
            await notificationsAPI.sendManual(data);
            fetchLogs();
        } catch (err) {
            console.error(err);
            throw err;
        }
    };

    const getStatusIcon = (notif) => {
        if (notif.is_sent) return <CheckCircle2 className="text-emerald-500" size={16} />;
        return <XCircle className="text-rose-500" size={16} />;
    };

    const getTypeStyles = (type) => {
        switch (type) {
            case 'alert': return 'bg-orange-50 text-orange-600 border-orange-100';
            case 'sync_issue': return 'bg-rose-50 text-rose-600 border-rose-100';
            case 'reminder': return 'bg-indigo-50 text-indigo-600 border-indigo-100';
            default: return 'bg-sky-50 text-sky-600 border-sky-100';
        }
    };

    return (
        <div className="p-8 space-y-8 bg-gray-50/50 min-h-screen">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center space-x-4">
                    <div className="bg-white p-3 rounded-2xl shadow-sm border border-gray-100">
                        <Bell className="text-sky-600" size={32} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-black text-gray-900 leading-tight">Notification Center</h1>
                        <p className="text-gray-400 text-sm font-medium">Manage push alerts & delivery logs</p>
                    </div>
                </div>
                
                <button 
                    onClick={() => setIsModalOpen(true)}
                    className="bg-gray-900 text-white px-8 py-4 rounded-2xl font-black flex items-center justify-center space-x-3 hover:bg-black transition-all shadow-xl shadow-gray-900/10 active:scale-95"
                >
                    <Send size={18} />
                    <span>Send New Alert</span>
                </button>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { label: 'Total Sent', value: stats.total_sent, icon: Zap, color: 'text-sky-600', bg: 'bg-sky-50' },
                    { label: 'Delivery Rate', value: stats.delivery_rate, icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                    { label: 'Active Devices', value: stats.active_devices, icon: Smartphone, color: 'text-indigo-600', bg: 'bg-indigo-50' }
                ].map((stat, i) => (
                    <div key={i} className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm flex items-center space-x-4">
                        <div className={`${stat.bg} p-4 rounded-2xl`}>
                            <stat.icon className={stat.color} size={24} />
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">{stat.label}</p>
                            <p className="text-2xl font-black text-gray-900">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Main Content */}
            <div className="bg-white rounded-[2.5rem] shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-8 border-b border-gray-50 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="flex items-center space-x-4 overflow-x-auto pb-2 md:pb-0 scrollbar-hide">
                        <button 
                            onClick={() => setFilter('')}
                            className={`px-6 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap ${!filter ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'}`}
                        >
                            All Logs
                        </button>
                        {['system', 'reminder', 'alert', 'sync_issue'].map(t => (
                            <button 
                                key={t}
                                onClick={() => setFilter(t)}
                                className={`px-6 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap capitalize ${filter === t ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'}`}
                            >
                                {t.replace('_', ' ')}
                            </button>
                        ))}
                    </div>
                    
                    <button 
                        onClick={fetchLogs}
                        className="p-3 bg-gray-50 text-gray-400 hover:text-sky-600 rounded-2xl transition-all active:rotate-180"
                    >
                        <RefreshCcw size={20} />
                    </button>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-gray-50/50">
                                <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-widest first:rounded-tl-[2rem]">Device & Branch</th>
                                <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-widest">Notification Details</th>
                                <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-widest">Type</th>
                                <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-widest">Status</th>
                                <th className="px-8 py-5 text-[10px] font-black text-gray-400 uppercase tracking-widest last:rounded-tr-[2rem]">Time Sent</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {loading ? (
                                Array(5).fill(0).map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={5} className="px-8 py-6">
                                            <div className="h-4 bg-gray-100 rounded-full w-3/4 mb-2"></div>
                                            <div className="h-4 bg-gray-50 rounded-full w-1/2"></div>
                                        </td>
                                    </tr>
                                ))
                            ) : logs.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-8 py-20 text-center">
                                        <div className="inline-flex items-center justify-center p-6 bg-gray-50 rounded-full mb-4">
                                            <ShieldAlert size={48} className="text-gray-300" />
                                        </div>
                                        <p className="text-gray-400 font-bold">No notification history found</p>
                                    </td>
                                </tr>
                            ) : (
                                logs.map((log) => (
                                    <tr key={log.id} className="group hover:bg-gray-50/80 transition-colors">
                                        <td className="px-8 py-6">
                                            <div className="flex items-center space-x-3">
                                                <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center group-hover:bg-white transition-colors border border-transparent group-hover:border-gray-100">
                                                    <Smartphone size={18} className="text-gray-400" />
                                                </div>
                                                <div>
                                                    <p className="text-sm font-bold text-gray-900 leading-none">{log.device_name}</p>
                                                    <p className="text-[10px] text-gray-400 mt-1 font-medium">{log.branch_name}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6 max-w-xs">
                                            <p className="text-sm font-bold text-gray-800 leading-tight">{log.title}</p>
                                            <p className="text-xs text-gray-500 mt-1 line-clamp-1">{log.body}</p>
                                        </td>
                                        <td className="px-8 py-6">
                                            <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border border-transparent ${getTypeStyles(log.notification_type)}`}>
                                                {log.notification_type.replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex items-center space-x-2">
                                                {getStatusIcon(log)}
                                                <span className="text-xs font-bold text-gray-700">{log.is_sent ? 'Delivered' : 'Failed'}</span>
                                            </div>
                                            {log.error_message && (
                                                <p className="text-[9px] text-rose-500 mt-1 max-w-[150px] line-clamp-1">{log.error_message}</p>
                                            )}
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex items-center space-x-2 text-gray-400">
                                                <Clock size={14} />
                                                <span className="text-xs font-medium">
                                                    {new Date(log.created_at).toLocaleDateString()} {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                            </div>
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

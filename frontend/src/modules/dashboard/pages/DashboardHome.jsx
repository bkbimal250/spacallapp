import React, { useEffect, useState } from 'react';
import StatsCard from '../components/StatsCard';
import BranchPerformanceTable from '../components/BranchPerformanceTable';
import { dashboardAPI } from '../api';
import { 
    Users, 
    Smartphone, 
    Zap, 
    Target, 
    Building2, 
    UserPlus, 
    FileJson, 
    PhoneCall,
    PhoneMissed,
    Clock
} from 'lucide-react';

const DashboardHome = () => {
    const [stats, setStats] = useState({
        total_calls: 0,
        active_devices: 0,
        total_devices: 0,
        missed_calls: 0,
        total_leads: 0,
        total_branches: 0,
        total_contacts: 0,
        total_users: 0,
        total_exports: 0,
        avg_duration: '0m 0s'
    });
    const [chartData, setChartData] = useState([]);
    const [branchData, setBranchData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [leadSource, setLeadSource] = useState('all'); // 'all', 'direct', 'manual'

    useEffect(() => {
        const fetchStats = async (isBackground = false) => {
            if (!isBackground) setLoading(true);
            try {
                const params = {};
                if (leadSource !== 'all') params.lead_source = leadSource;
                
                const response = await dashboardAPI.getStats(params);
                const payload = response.data?.data || response.data;
                if (payload) {
                    setStats(payload);
                    if (payload.call_volume_trends) setChartData(payload.call_volume_trends);
                    if (payload.branch_performance) setBranchData(payload.branch_performance);
                }
            } catch (error) {
                console.error("Failed to fetch dashboard stats", error);
            } finally {
                if (!isBackground) setLoading(false);
            }
        };

        fetchStats(); // Initial fetch
        const interval = setInterval(() => {
            fetchStats(true); // Background fetch (don't set loading to true)
        }, 10000);

        return () => clearInterval(interval);
    }, [leadSource]);

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
    );

    const statCards = [
        { title: "Total Users", value: stats.total_users, icon: Users, color: "text-blue-600", bg: "bg-blue-50" },
        { title: "Total Devices", value: stats.total_devices, icon: Smartphone, color: "text-purple-600", bg: "bg-purple-50" },
        { title: "Active Devices", value: stats.active_devices, icon: Zap, color: "text-amber-600", bg: "bg-amber-50" },
        { title: "Total Leads", value: stats.total_leads, icon: Target, color: "text-emerald-600", bg: "bg-emerald-50" },
        { title: "Total Branches", value: stats.total_branches, icon: Building2, color: "text-indigo-600", bg: "bg-indigo-50" },
        { title: "Total Contacts", value: stats.total_contacts, icon: UserPlus, color: "text-sky-600", bg: "bg-sky-50" },
        { title: "Total Exports", value: stats.total_exports, icon: FileJson, color: "text-rose-600", bg: "bg-rose-50" },
        { title: "Total Calls", value: stats.total_calls, icon: PhoneCall, color: "text-cyan-600", bg: "bg-cyan-50" },
    ];

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
                
                <div className="flex items-center gap-3 bg-white p-1.5 rounded-2xl shadow-sm border border-gray-100">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-widest pl-3">Lead Source:</span>
                    <select 
                        value={leadSource}
                        onChange={(e) => setLeadSource(e.target.value)}
                        className="bg-gray-50 text-gray-900 text-xs font-bold py-2 px-4 rounded-xl border-none focus:ring-2 focus:ring-indigo-500 outline-none cursor-pointer"
                    >
                        <option value="all">All Sources</option>
                        <option value="direct">Direct Sync</option>
                        <option value="manual">Manual Entry</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {statCards.map((card, index) => (
                    <StatsCard 
                        key={index}
                        title={card.title}
                        value={card.value}
                        icon={<card.icon className={card.color} size={20} />}
                        className={card.bg}
                    />
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <StatsCard 
                    title="Missed Calls" 
                    value={stats.missed_calls} 
                    icon={<PhoneMissed className="text-red-600" size={20} />}
                    isNegative
                />
                <StatsCard 
                    title="Avg. Duration" 
                    value={stats.avg_duration} 
                    icon={<Clock className="text-indigo-600" size={20} />}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-1 gap-6">
                <BranchPerformanceTable data={branchData} />
            </div>
        </div>
    );
};

export default DashboardHome;

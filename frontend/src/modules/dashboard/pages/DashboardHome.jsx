import React, { useEffect, useState } from 'react';
import StatsCard from '../components/StatsCard';
import CallChart from '../components/CallChart';
import BranchPerformanceTable from '../components/BranchPerformanceTable';
import { dashboardAPI } from '../api';

const DashboardHome = () => {
    const [stats, setStats] = useState({
        total_calls: 0,
        active_devices: 0,
        missed_calls: 0,
        avg_duration: '0m 0s'
    });
    const [chartData, setChartData] = useState([]);
    const [branchData, setBranchData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async (isBackground = false) => {
            if (!isBackground) setLoading(true);
            try {
                const response = await dashboardAPI.getStats();
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
    }, []);

    if (loading) return <div>Loading Dashboard...</div>;

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard title="Total Calls" value={stats.total_calls} change="+12%" />
                <StatsCard title="Active Devices" value={stats.active_devices} change="+2" />
                <StatsCard title="Missed Calls" value={stats.missed_calls} change="-5%" isNegative />
                <StatsCard title="Avg. Duration" value={stats.avg_duration} change="+30s" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <CallChart data={chartData} />
                <BranchPerformanceTable data={branchData} />
            </div>
        </div>
    );
};

export default DashboardHome;

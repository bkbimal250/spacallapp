import React, { useEffect, useState, useMemo, useCallback, memo } from 'react';
import StatsCard from '../components/StatsCard';
import BranchPerformanceTable from '../components/BranchPerformanceTable';
import { dashboardAPI } from '../api';
import { branchesAPI } from '../../branches/api';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { useAuth } from '../../../shared/hooks/useAuth';
import { useNavigate } from 'react-router-dom';

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

    const { user } = useAuth();
    const navigate = useNavigate();

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
        today_total_calls: 0,
        avg_duration: '0m 0s'
    });

    const [chartData, setChartData] = useState([]);
    const [branchData, setBranchData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [leadSource, setLeadSource] = useState('all');
    const [selectedBranch, setSelectedBranch] = useState('');
    const [branches, setBranches] = useState([]);

    const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

    useEffect(() => {
        const fetchBranches = async () => {
            if (!isAdmin) return;
            try {
                const response = await branchesAPI.getBranches({ all: true });
                const data = response.data.results || response.data;
                setBranches(data.map(b => ({ value: b.id, label: b.spa_name })));
            } catch (err) {
                console.error("Failed to fetch branches", err);
            }
        };

        fetchBranches();
    }, [isAdmin]);

    const fetchStats = useCallback(async (isBackground = false) => {

        if (!isBackground) setLoading(true);

        try {

            const params = {};

            if (leadSource !== 'all') params.lead_source = leadSource;
            if (selectedBranch) params.branch = selectedBranch;

            const response = await dashboardAPI.getStats(params);
            const payload = response.data?.data || response.data;

            if (payload) {
                setStats(payload);

                if (payload.call_volume_trends)
                    setChartData(payload.call_volume_trends);

                if (payload.branch_performance)
                    setBranchData(payload.branch_performance);
            }

        } catch (error) {
            console.error("Failed to fetch dashboard stats", error);
        } finally {
            if (!isBackground) setLoading(false);
        }
    }, [leadSource, selectedBranch]);

    useEffect(() => {
        fetchStats();

        const interval = setInterval(() => {
            fetchStats(true);
        }, 10000);

        return () => clearInterval(interval);

    }, [fetchStats]);

    const statCards = useMemo(() => [
        { title: "Total Users", value: stats.total_users, icon: Users, color: "text-primary", bg: "bg-primary/10" },
        { title: "Total Devices", value: stats.total_devices, icon: Smartphone, color: "text-accent-purple", bg: "bg-accent-purple/10" },
        { title: "Active Devices", value: stats.active_devices, icon: Zap, color: "text-warning", bg: "bg-warning/10" },
        { title: "Total Leads", value: stats.total_leads, icon: Target, color: "text-success", bg: "bg-success/10" },
        { title: "Total Branches", value: stats.total_branches, icon: Building2, color: "text-info", bg: "bg-info/10" },
        { title: "Total Contacts", value: stats.total_contacts, icon: UserPlus, color: "text-cyan-400", bg: "bg-cyan-500/10" },
        { title: "Total Exports", value: stats.total_exports, icon: FileJson, color: "text-danger", bg: "bg-danger/10" },
        { title: "Total Calls", value: stats.total_calls, icon: PhoneCall, color: "text-primary", bg: "bg-primary/10" },
        { title: "Today Total Calls", value: stats.today_total_calls, icon: PhoneCall, color: "text-primary", bg: "bg-primary/10" },
    ], [stats]);

    if (loading)
        return (
            <div className="flex items-center justify-center min-h-[400px]">

                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>

            </div>
        );

    return (

        <div className="space-y-6">

            {/* PAGE HEADER */}

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">

                <div>

                    <h1 className="text-2xl font-bold text-text-primary">
                        Dashboard Overview
                    </h1>

                    <p className="text-sm text-text-secondary">
                        Real-time performance analytics
                    </p>

                </div>

                <div className="flex flex-wrap items-center gap-3">
                    {/* Filters area (future use) */}
                </div>

            </div>

            {/* STATS GRID */}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

                {statCards.map((card, index) => (

                    <StatsCard
                        key={index}
                        title={card.title}
                        value={card.value}
                        icon={<card.icon className={card.color} size={20} />}
                        className={`${card.bg} text-center flex flex-col items-center justify-center`}
                    />

                ))}

            </div>

            {/* SECONDARY STATS */}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

                <StatsCard
                    title="Missed Calls"
                    value={stats.missed_calls}
                    icon={<PhoneMissed className="text-danger" size={20} />}
                    isNegative
                />

                <StatsCard
                    title="Avg. Duration"
                    value={stats.avg_duration}
                    icon={<Clock className="text-primary" size={20} />}
                />

            </div>

            {/* BRANCH PERFORMANCE */}

            <div className="grid grid-cols-1 lg:grid-cols-1 gap-6">

                <BranchPerformanceTable data={branchData} />

            </div>

        </div>

    );
};

export default memo(DashboardHome);
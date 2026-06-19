import React, { useEffect, useState, useMemo, useCallback, memo } from 'react';
import StatsCard from '../components/StatsCard';
import BranchPerformanceTable from '../components/BranchPerformanceTable';
import { dashboardAPI } from '../api';
import { branchesAPI } from '../../branches/api';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { useAuth } from '../../../shared/hooks/useAuth';
import { useSearchParams } from 'react-router-dom';
import { useWebSocket } from '../../../shared/hooks/useWebSocket';
import LiveUsersList from '../components/LiveUsersList';
import { useDispatch } from 'react-redux';
import { setOnlineUsers } from '../../../store/slices/notificationSlice';
import axiosInstance from '../../../shared/services/axiosInstance';

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

const getListPayload = (payload) => {
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload?.results)) return payload.results;
    if (Array.isArray(payload?.data)) return payload.data;
    if (Array.isArray(payload?.items)) return payload.items;
    return [];
};

const DashboardHome = () => {

    const { user } = useAuth();
    const dispatch = useDispatch();

    // Initialize WebSocket for real-time tracking
    useWebSocket('/ws/crm/dashboard/');

    const [searchParams, setSearchParams] = useSearchParams();
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
        today_incoming_calls: 0,
        today_outgoing_calls: 0,
        today_missed_calls: 0,
    });

    const [, setChartData] = useState([]);
    const [branchData, setBranchData] = useState([]);
    const [loading, setLoading] = useState(true);

    // Filter states synced with URL
    const quickDate = searchParams.get('quick_date') || 'today';
    const selectedBranch = searchParams.get('branch') || '';
    const selectedGroup = searchParams.get('branch_group') || '';
    const leadSource = searchParams.get('lead_source') || 'all';

    const [branches, setBranches] = useState([]);
    const [groups, setGroups] = useState([]);

    const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

    const updateFilters = (newFilters) => {
        const params = new URLSearchParams(searchParams);
        Object.entries(newFilters).forEach(([key, value]) => {
            if (value) params.set(key, value);
            else params.delete(key);
        });
        setSearchParams(params);
    };

    useEffect(() => {
        const fetchBranches = async () => {
            if (!isAdmin) return;
            try {
                const params = { all: true };
                if (selectedGroup) {
                    params.branch_group = selectedGroup;
                }
                const response = await branchesAPI.getBranches(params);
                const data = getListPayload(response.data);
                setBranches(data.map(b => ({
                    value: b.id,
                    label: b.spa_name,
                    searchText: [
                        b.spa_name,
                        b.code,
                        b.city,
                        b.area,
                        b.state,
                        b.address,
                        b.phone,
                        b.branch_group_name,
                    ].filter(Boolean).join(' ')
                })));
            } catch (err) {
                console.error("Failed to fetch branches", err);
            }
        };
        fetchBranches();
    }, [isAdmin, selectedGroup]);

    useEffect(() => {
        const fetchOnlineUsers = async () => {
            try {
                const response = await axiosInstance.get('/auth/users/online/');
                dispatch(setOnlineUsers(getListPayload(response.data)));
            } catch (err) {
                console.error("Failed to fetch online users", err);
            }
        };

        const fetchGroups = async () => {
            if (!isAdmin) return;
            try {
                const response = await branchesAPI.getGroups({ all: true });
                const data = getListPayload(response.data);
                setGroups(data.map(g => ({ value: g.id, label: g.name })));
            } catch (err) {
                console.error("Failed to fetch groups", err);
            }
        };

        fetchGroups();
        fetchOnlineUsers();
    }, [isAdmin, dispatch]);

    const fetchStats = useCallback(async (isBackground = false) => {
        if (!isBackground) setLoading(true);

        try {
            const params = {
                quick_date: quickDate
            };

            if (leadSource !== 'all') params.lead_source = leadSource;
            if (selectedBranch) params.branch = selectedBranch;
            if (selectedGroup) params.branch_group = selectedGroup;

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
    }, [leadSource, selectedBranch, selectedGroup, quickDate]);

    useEffect(() => {
        fetchStats();
        const interval = setInterval(() => {
            fetchStats(true);
        }, 10000);
        return () => clearInterval(interval);
    }, [fetchStats]);

    const statCards = useMemo(() => [
        { title: "Today Incoming", value: stats.today_incoming_calls, icon: PhoneCall, color: "text-emerald-600", bg: "bg-emerald-50/50" },
        { title: "Today Outgoing", value: stats.today_outgoing_calls, icon: PhoneCall, color: "text-blue-600", bg: "bg-blue-50/50" },
        { title: "Today Missed", value: stats.today_missed_calls, icon: PhoneMissed, color: "text-rose-600", bg: "bg-rose-50/50" },
        { title: "Today Total", value: stats.today_total_calls, icon: Zap, color: "text-amber-600", bg: "bg-amber-50/50" },
        { title: "Total Users", value: stats.total_users, icon: Users, color: "text-indigo-600", bg: "bg-indigo-50/50" },
        { title: "Total Devices", value: stats.total_devices, icon: Smartphone, color: "text-violet-600", bg: "bg-violet-50/50" },
        { title: "Active Devices", value: stats.active_devices, icon: Zap, color: "text-orange-600", bg: "bg-orange-50/50" },
        { title: "Total Branches", value: stats.total_branches, icon: Building2, color: "text-cyan-600", bg: "bg-cyan-50/50" },
        { title: "Total Contacts", value: stats.total_contacts, icon: UserPlus, color: "text-teal-600", bg: "bg-teal-50/50" },
        { title: "Total Exports", value: stats.total_exports, icon: FileJson, color: "text-fuchsia-600", bg: "bg-fuchsia-50/50" },
    ], [stats]);

    if (loading && !stats.total_calls)
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="flex flex-col items-center gap-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                    <p className="text-text-secondary animate-pulse">Loading analytics...</p>
                </div>
            </div>
        );

    return (
        <div className="space-y-6 pb-10">
            {/* PAGE HEADER & FILTERS */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-text-primary">
                            Dashboard Overview
                        </h1>
                        <p className="text-sm text-text-secondary">
                            Real-time performance analytics across {selectedBranch ? 'selected branch' : 'all locations'}
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pt-4 border-t border-border/50">
                    {isAdmin && (
                        <>
                            <div className="space-y-1.5">
                                <label className="text-[11px] font-bold uppercase tracking-wider text-text-secondary px-1">Branch Group</label>
                                <SearchableSelect
                                    options={groups}
                                    value={selectedGroup}
                                    onChange={(val) => {
                                        updateFilters({ branch_group: val, branch: '' });
                                    }}
                                    placeholder="All Groups"
                                    isClearable
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-[11px] font-bold uppercase tracking-wider text-text-secondary px-1">Branch Location</label>
                                <SearchableSelect
                                    options={branches}
                                    value={selectedBranch}
                                    onChange={(val) => updateFilters({ branch: val })}
                                    placeholder="All Branches"
                                    isClearable
                                />
                            </div>
                        </>
                    )}

                    <div className="space-y-1.5">
                        <label className="text-[11px] font-bold uppercase tracking-wider text-text-secondary px-1">Date Range</label>
                        <select
                            value={quickDate}
                            onChange={(e) => updateFilters({ quick_date: e.target.value })}
                            className="w-full bg-slate-50/50 border border-border text-text-primary rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none shadow-sm hover:border-primary/50 transition-all cursor-pointer appearance-none"
                        >
                            <option value="">All Time</option>
                            <option value="today">Today</option>
                            <option value="yesterday">Yesterday</option>
                            <option value="last_7_days">Last 7 Days</option>
                        </select>
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-[11px] font-bold uppercase tracking-wider text-text-secondary px-1">Lead Type</label>
                        <select
                            value={leadSource}
                            onChange={(e) => updateFilters({ lead_source: e.target.value })}
                            className="w-full bg-slate-50/50 border border-border text-text-primary rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none shadow-sm hover:border-primary/50 transition-all cursor-pointer appearance-none"
                        >
                            <option value="all">All Leads</option>
                            <option value="new">New Leads</option>
                            <option value="followup">Follow up</option>
                            <option value="closed">Closed</option>
                        </select>
                    </div>
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
                        className={`text-center flex flex-col items-center justify-center`}
                    />

                ))}

            </div>

            {/* SECONDARY STATS */}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">



            </div>

            {/* BRANCH PERFORMANCE */}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                <div className="lg:col-span-2">
                    <BranchPerformanceTable data={branchData} />
                </div>

                <div className="lg:col-span-1">
                    <LiveUsersList />
                </div>

            </div>

        </div>

    );
};

export default memo(DashboardHome);

import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCcw, AlertCircle } from 'lucide-react';
import { monitoringAPI } from '../api';
import { devicesAPI } from '../../devices/api';
import DashboardStatsCard from '../../dashboard/components/StatsCard';
import Table from '../../../shared/components/Table';
import Pagination from '../../../shared/components/Pagination';
import Badge from '../../../shared/components/Badge';
import DeviceStatusBadge from '../../devices/components/DeviceStatusBadge';
import OfflineDeviceCard from '../components/OfflineDeviceCard';
import { formatDate } from '../../../shared/utils/formatDate';

const DeviceHealth = () => {
    const [stats, setStats] = useState({
        total_devices: 0,
        online_devices: 0,
        offline_alerts: 0,
        sim_change_alerts: 0
    });
    const [alerts, setAlerts] = useState([]);
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 100;

    const fetchData = useCallback(async (isBackground = false) => {
        if (!isBackground) setLoading(true);
        setError(null);

        try {
            // Fetch everything sequentially to precisely identify where it fails
            let healthData = { total_devices: 0, online_devices: 0, offline_alerts: 0, sim_change_alerts: 0 };
            let alertsData = { results: [], count: 0 };
            let devicesData = { results: [], count: 0 };

            try {
                const res = await monitoringAPI.getDeviceHealth();
                healthData = res.data;
                // console.log("Monitoring Stats Success:", healthData);
            } catch (err) {
                console.error("Monitoring Stats API Failed:", err);
                // Keep defaults
            }

            try {
                const res = await monitoringAPI.getAlerts({ page, page_size: pageSize });
                alertsData = res.data;
                // console.log("Monitoring Alerts Success:", alertsData);
            } catch (err) {
                console.error("Monitoring Alerts API Failed:", err);
            }

            try {
                const res = await devicesAPI.getDevices({ page_size: 10 });
                devicesData = res.data;
                // console.log("Monitoring Devices Success:", devicesData);
            } catch (err) {
                console.error("Monitoring Devices API Failed:", err);
            }

            setStats(healthData);

            const alertsList = alertsData.results || (Array.isArray(alertsData) ? alertsData : []);
            setAlerts(alertsList);
            setTotalCount(alertsData.count || alertsList.length);

            const devicesList = devicesData.results || (Array.isArray(devicesData) ? devicesData : []);
            setDevices(devicesList.slice(0, 10));

        } catch (err) {
            console.error("Device Monitoring: Unexpected error", err);
            setError("Something went wrong while fetching data.");
        } finally {
            if (!isBackground) setLoading(false);
        }
    }, [page]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(() => fetchData(true), 20000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const handleResolveAlert = async (id) => {
        try {
            await monitoringAPI.resolveAlert(id);
            fetchData(true);
        } catch (error) {
            console.error("Resolve alert failed", error);
        }
    };

    const handleDeleteAlert = async (id) => {
        if (window.confirm("Are you sure you want to delete this alert?")) {
            try {
                await monitoringAPI.deleteAlert(id);
                fetchData(true);
            } catch (error) {
                console.error("Delete alert failed", error);
            }
        }
    };

    const handlePageChange = (newPage) => {
        setPage(newPage);
    };

    const offlineAlerts = (alerts || []).filter(
        a => !a.resolved && a.event_type === 'offline'
    );

    const alertColumns = [
        { header: 'Device', accessor: 'device_uid' },
        { header: 'Branch', accessor: 'branch_name' },
        {
            header: 'Event',
            render: (row) => (
                <Badge variant={row.event_type === 'offline' ? 'danger' : 'warning'}>
                    {row.event_type}
                </Badge>
            )
        },
        { header: 'Description', accessor: 'description' },
        {
            header: 'Created Time',
            render: (row) => row.created_at ? formatDate(row.created_at, 'MMM dd, yyyy HH:mm:ss') : 'N/A'
        },
        {
            header: 'Status',
            render: (row) => (
                <Badge variant={row.resolved ? 'success' : 'danger'}>
                    {row.resolved ? 'Resolved' : 'Active'}
                </Badge>
            )
        },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex items-center gap-2">
                    {!row.resolved && (
                        <button
                            onClick={() => handleResolveAlert(row.id)}
                            className="px-2 py-1 text-xs rounded bg-success/20 text-success hover:bg-success/30 transition"
                        >
                            Resolve
                        </button>
                    )}
                    <button
                        onClick={() => handleDeleteAlert(row.id)}
                        className="px-2 py-1 text-xs rounded bg-danger/20 text-danger hover:bg-danger/30 transition"
                    >
                        Delete
                    </button>
                </div>
            )
        }
    ];

    return (
        <div className="space-y-6 text-text-primary animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Device Health & Monitoring</h1>
                    <p className="text-sm text-text-secondary mt-1">Real-time status and alerts for all registered devices.</p>
                </div>

                <button
                    onClick={() => fetchData()}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl border border-border bg-card hover:bg-cardHover transition disabled:opacity-50"
                >
                    <RefreshCcw size={16} className={loading ? "animate-spin" : ""} />
                    {loading ? "Refreshing..." : "Refresh"}
                </button>
            </div>

            {error && (
                <div className="bg-danger/10 border border-danger/20 p-4 rounded-xl flex items-center gap-3 text-danger">
                    <AlertCircle size={20} />
                    <p className="text-sm font-medium">{error}</p>
                </div>
            )}

            {/* STATS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <DashboardStatsCard
                    title="Total Devices"
                    value={stats.total_devices}
                />
                <DashboardStatsCard
                    title="Online Devices"
                    value={stats.online_devices}
                    className="border-success/20"
                />
                <DashboardStatsCard
                    title="Offline Alerts"
                    value={stats.offline_alerts}
                    isNegative={stats.offline_alerts > 0}
                    className="border-danger/20"
                />
                <DashboardStatsCard
                    title="SIM Change Alerts"
                    value={stats.sim_change_alerts}
                    className="border-warning/20"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    {/* LIVE MONITORING TABLE */}
                    <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
                        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-card">
                            <h3 className="text-lg font-semibold">Live Device Monitoring</h3>
                            <Badge variant="secondary" className="px-2 py-0.5">TOP 10</Badge>
                        </div>
                        <div className="overflow-x-auto">
                            <Table
                                columns={[
                                    { header: 'Device ID', accessor: 'device_id' },
                                    { header: 'Branch', accessor: 'branch_name' },
                                    {
                                        header: 'Status',
                                        render: (row) => (
                                            <DeviceStatusBadge
                                                isActive={row.is_active}
                                                isBlocked={row.is_blocked}
                                                isRegistered={row.is_registered}
                                                isOnline={row.is_online}
                                            />
                                        )
                                    },
                                    {
                                        header: 'Last Heartbeat',
                                        render: (row) =>
                                            row.last_heartbeat
                                                ? <span className="text-xs font-mono">{formatDate(row.last_heartbeat, 'MMM dd, yyyy HH:mm:ss')}</span>
                                                : <span className="text-xs text-text-muted italic">Never</span>
                                    }
                                ]}
                                data={devices}
                            />
                        </div>
                    </div>

                    {/* ALERTS TABLE */}
                    <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
                        <div className="px-6 py-4 border-b border-border">
                            <h3 className="text-lg font-semibold">Recent System Alerts</h3>
                        </div>
                        <div className="overflow-x-auto">
                            <Table
                                columns={alertColumns}
                                data={alerts}
                            />
                        </div>
                        {totalCount > 0 && (
                            <div className="px-6 py-4 border-t border-border flex justify-end">
                                <Pagination
                                    currentPage={page}
                                    totalPages={Math.ceil(totalCount / pageSize)}
                                    onPageChange={handlePageChange}
                                    totalCount={totalCount}
                                    pageSize={pageSize}
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* CRITICAL ISSUES SIDEBAR */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between px-1">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            Critical Issues
                        </h3>
                        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-danger/10 text-danger text-[10px] font-bold uppercase tracking-wider">
                            <span className="w-1.5 h-1.5 rounded-full bg-danger animate-pulse"></span>
                            Live
                        </span>
                    </div>

                    <div className="space-y-4">
                        {offlineAlerts.length > 0 ? (
                            offlineAlerts.slice(0, 5).map(alert => (
                                <OfflineDeviceCard
                                    key={alert.id}
                                    deviceName={alert.device_uid}
                                    location={alert.branch_name}
                                    lastSeen={formatDate(alert.created_at, 'MMM dd, yyyy HH:mm:ss')}
                                />
                            ))
                        ) : (
                            <div className="bg-card border border-dashed border-border p-8 rounded-2xl text-center">
                                <p className="text-sm text-text-muted italic">No offline devices detected</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeviceHealth;
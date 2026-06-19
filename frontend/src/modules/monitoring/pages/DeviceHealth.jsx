import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, RefreshCcw, Trash2 } from 'lucide-react';
import { monitoringAPI } from '../api';
import { devicesAPI } from '../../devices/api';
import DashboardStatsCard from '../../dashboard/components/StatsCard';
import Table from '../../../shared/components/Table';
import Pagination from '../../../shared/components/Pagination';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import DeviceStatusBadge from '../../devices/components/DeviceStatusBadge';
import OfflineDeviceCard from '../components/OfflineDeviceCard';
import MonitoringFilters from '../components/MonitoringFilters';
import { formatDate } from '../../../shared/utils/formatDate';
import { useWebSocket } from '../../../shared/hooks/useWebSocket';

const pageSize = 50;

const cleanParams = (params) => Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
);

const getDeviceParams = (filters, page) => {
    const params = {
        search: filters.search?.trim(),
        branch: filters.branch,
        page,
        page_size: pageSize,
    };

    switch (filters.deviceStatus) {
        case 'online':
            params.is_online = true;
            break;
        case 'offline':
            params.is_online = false;
            break;
        case 'registered':
            params.is_registered = true;
            break;
        case 'pending':
            params.is_registered = false;
            break;
        case 'blocked':
            params.is_blocked = true;
            break;
        default:
            break;
    }

    return cleanParams(params);
};

const getAlertParams = (filters, page) => cleanParams({
    search: filters.search?.trim(),
    branch: filters.branch,
    event_type: filters.event_type,
    resolved: filters.resolved,
    page,
    page_size: pageSize,
});

const getStatsParams = (filters) => cleanParams({
    branch: filters.branch,
});

const DeviceHealth = () => {
    const [stats, setStats] = useState({
        total_devices: 0,
        online_devices: 0,
        offline_alerts: 0,
        sim_change_alerts: 0,
        sync_failure_alerts: 0,
        battery_low_alerts: 0,
        storage_alerts: 0,
        network_alerts: 0,
        active_alerts: 0,
    });
    const [alerts, setAlerts] = useState([]);
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({});
    const [appliedFilters, setAppliedFilters] = useState({});
    const [devicePage, setDevicePage] = useState(1);
    const [alertPage, setAlertPage] = useState(1);
    const [deviceTotalCount, setDeviceTotalCount] = useState(0);
    const [alertTotalCount, setAlertTotalCount] = useState(0);
    const [selectedAlertIds, setSelectedAlertIds] = useState([]);
    const [bulkLoading, setBulkLoading] = useState(false);

    const fetchData = useCallback(async (isBackground = false) => {
        if (!isBackground) setLoading(true);
        setError(null);

        try {
            const [healthResult, alertsResult, devicesResult] = await Promise.allSettled([
                monitoringAPI.getDeviceHealth(getStatsParams(appliedFilters)),
                monitoringAPI.getAlerts(getAlertParams(appliedFilters, alertPage)),
                devicesAPI.getDevices(getDeviceParams(appliedFilters, devicePage)),
            ]);

            if (healthResult.status === 'fulfilled') {
                setStats(healthResult.value.data);
            } else {
                console.error('Monitoring stats API failed', healthResult.reason);
            }

            if (alertsResult.status === 'fulfilled') {
                const alertsData = alertsResult.value.data;
                const alertsList = alertsData.results || (Array.isArray(alertsData) ? alertsData : []);
                setAlerts(alertsList);
                setAlertTotalCount(alertsData.count || alertsList.length);
                setSelectedAlertIds(current => current.filter(id => alertsList.some(alert => alert.id === id)));
            } else {
                console.error('Monitoring alerts API failed', alertsResult.reason);
            }

            if (devicesResult.status === 'fulfilled') {
                const devicesData = devicesResult.value.data;
                const devicesList = devicesData.results || (Array.isArray(devicesData) ? devicesData : []);
                setDevices(devicesList);
                setDeviceTotalCount(devicesData.count || devicesList.length);
            } else {
                console.error('Monitoring devices API failed', devicesResult.reason);
            }

            if (
                healthResult.status === 'rejected' &&
                alertsResult.status === 'rejected' &&
                devicesResult.status === 'rejected'
            ) {
                setError('Something went wrong while fetching monitoring data.');
            }
        } catch (err) {
            console.error('Device Monitoring: unexpected error', err);
            setError('Something went wrong while fetching monitoring data.');
        } finally {
            if (!isBackground) setLoading(false);
        }
    }, [alertPage, appliedFilters, devicePage]);

    const handleRealtimeMonitoring = useCallback((message) => {
        if (message.type === 'monitoring_event' || message.type === 'monitoring_status' || message.type === 'refresh_monitoring') {
            fetchData(true);
        }
    }, [fetchData]);

    useWebSocket('/ws/crm/dashboard/', handleRealtimeMonitoring);

    useEffect(() => {
        fetchData();
        const interval = setInterval(() => fetchData(true), 20000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const applyFilters = () => {
        setAppliedFilters(filters);
        setDevicePage(1);
        setAlertPage(1);
        setSelectedAlertIds([]);
    };

    const clearFilters = () => {
        setFilters({});
        setAppliedFilters({});
        setDevicePage(1);
        setAlertPage(1);
        setSelectedAlertIds([]);
    };

    const handleResolveAlert = async (id) => {
        try {
            await monitoringAPI.resolveAlert(id);
            fetchData(true);
        } catch (resolveError) {
            console.error('Resolve alert failed', resolveError);
        }
    };

    const handleDeleteAlert = async (id) => {
        if (!window.confirm('Delete this alert?')) return;

        try {
            await monitoringAPI.deleteAlert(id);
            setSelectedAlertIds(current => current.filter(selectedId => selectedId !== id));
            fetchData(true);
        } catch (deleteError) {
            console.error('Delete alert failed', deleteError);
        }
    };

    const handleResolveAll = async () => {
        if (!window.confirm('Resolve all active alerts matching the current filters?')) return;

        setBulkLoading(true);
        try {
            await monitoringAPI.resolveAllAlerts(getAlertParams(appliedFilters));
            setSelectedAlertIds([]);
            fetchData(true);
        } catch (resolveError) {
            console.error('Resolve filtered alerts failed', resolveError);
        } finally {
            setBulkLoading(false);
        }
    };

    const handleDeleteSelected = async () => {
        if (selectedAlertIds.length === 0) return;
        if (!window.confirm(`Delete ${selectedAlertIds.length} selected alert${selectedAlertIds.length > 1 ? 's' : ''}?`)) return;

        setBulkLoading(true);
        try {
            await monitoringAPI.deleteSelectedAlerts(selectedAlertIds);
            setSelectedAlertIds([]);
            fetchData(true);
        } catch (deleteError) {
            console.error('Delete selected alerts failed', deleteError);
        } finally {
            setBulkLoading(false);
        }
    };

    const handleDeleteAll = async () => {
        if (!window.confirm('Delete all alerts matching the current filters? This cannot be undone.')) return;

        setBulkLoading(true);
        try {
            await monitoringAPI.deleteAllAlerts(getAlertParams(appliedFilters));
            setSelectedAlertIds([]);
            fetchData(true);
        } catch (deleteError) {
            console.error('Delete filtered alerts failed', deleteError);
        } finally {
            setBulkLoading(false);
        }
    };

    const criticalAlerts = useMemo(() => (
        (alerts || []).filter(alert => !alert.resolved)
    ), [alerts]);

    const eventVariant = (eventType) => {
        if (eventType === 'offline' || eventType === 'sync_failure' || eventType === 'app_crash') return 'danger';
        if (eventType === 'battery_low' || eventType === 'storage_full' || eventType === 'network_weak' || eventType === 'sim_change') return 'warning';
        return 'secondary';
    };

    const deviceColumns = [
        {
            header: 'Device',
            render: (row) => (
                <div className="space-y-1 min-w-[160px]">
                    <p className="font-mono text-xs text-text-primary break-all">{row.device_id || 'Pending registration'}</p>
                    <p className="text-xs text-text-secondary truncate max-w-[220px]">{row.phone_name || row.android_id || 'No phone name'}</p>
                </div>
            ),
        },
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
            ),
        },
        {
            header: 'Last Heartbeat',
            render: (row) => row.last_heartbeat
                ? <span className="text-xs font-mono whitespace-nowrap">{formatDate(row.last_heartbeat, 'MMM dd, yyyy HH:mm:ss')}</span>
                : <span className="text-xs text-text-muted italic">Never</span>,
        },
        {
            header: 'Last Sync',
            render: (row) => row.last_sync
                ? <span className="text-xs font-mono whitespace-nowrap">{formatDate(row.last_sync, 'MMM dd, yyyy HH:mm:ss')}</span>
                : <span className="text-xs text-text-muted italic">Never</span>,
        },
    ];

    const alertColumns = [
        {
            header: 'Device',
            render: (row) => <span className="font-mono text-xs break-all">{row.device_uid || 'N/A'}</span>,
        },
        { header: 'Branch', accessor: 'branch_name' },
        {
            header: 'Event',
            render: (row) => (
                <Badge variant={eventVariant(row.event_type)}>
                    {row.event_label || row.event_type}
                </Badge>
            ),
        },
        {
            header: 'Description',
            render: (row) => <span className="block min-w-[180px] max-w-[340px]">{row.description}</span>,
        },
        {
            header: 'Created Time',
            render: (row) => row.created_at
                ? <span className="text-xs font-mono whitespace-nowrap">{formatDate(row.created_at, 'MMM dd, yyyy HH:mm:ss')}</span>
                : 'N/A',
        },
        {
            header: 'Status',
            render: (row) => (
                <Badge variant={row.resolved ? 'success' : 'danger'}>
                    {row.resolved ? 'Resolved' : 'Active'}
                </Badge>
            ),
        },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex items-center gap-2">
                    {!row.resolved && (
                        <button
                            onClick={() => handleResolveAlert(row.id)}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded bg-success/20 text-success hover:bg-success/30 transition"
                            title="Resolve alert"
                        >
                            <CheckCircle2 size={13} />
                            Resolve
                        </button>
                    )}
                    <button
                        onClick={() => handleDeleteAlert(row.id)}
                        className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded bg-danger/20 text-danger hover:bg-danger/30 transition"
                        title="Delete alert"
                    >
                        <Trash2 size={13} />
                        Delete
                    </button>
                </div>
            ),
        },
    ];

    return (
        <div className="space-y-6 text-text-primary animate-in fade-in duration-500">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Device Health & Monitoring</h1>
                    <p className="text-sm text-text-secondary mt-1">Real-time status and alerts for registered devices.</p>
                </div>

                <Button
                    variant="secondary"
                    onClick={() => fetchData()}
                    disabled={loading}
                    className="gap-2"
                >
                    <RefreshCcw size={16} className={loading ? 'animate-spin' : ''} />
                    {loading ? 'Refreshing...' : 'Refresh'}
                </Button>
            </div>

            {error && (
                <div className="bg-danger/10 border border-danger/20 p-4 rounded-xl flex items-center gap-3 text-danger">
                    <AlertCircle size={20} />
                    <p className="text-sm font-medium">{error}</p>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                <DashboardStatsCard title="Total Devices" value={stats.total_devices} />
                <DashboardStatsCard title="Online Devices" value={stats.online_devices} className="border-success/20" />
                <DashboardStatsCard title="Active Alerts" value={stats.active_alerts} isNegative={stats.active_alerts > 0} className="border-danger/20" />
                <DashboardStatsCard title="Sync Issues" value={stats.sync_failure_alerts} isNegative={stats.sync_failure_alerts > 0} className="border-warning/20" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                <DashboardStatsCard title="Offline Alerts" value={stats.offline_alerts} isNegative={stats.offline_alerts > 0} className="border-danger/20" />
                <DashboardStatsCard title="Battery Alerts" value={stats.battery_low_alerts} isNegative={stats.battery_low_alerts > 0} className="border-warning/20" />
                <DashboardStatsCard title="Network Alerts" value={stats.network_alerts} isNegative={stats.network_alerts > 0} className="border-warning/20" />
                <DashboardStatsCard title="SIM Change Alerts" value={stats.sim_change_alerts} isNegative={stats.sim_change_alerts > 0} className="border-warning/20" />
            </div>

            <MonitoringFilters
                filters={filters}
                onChange={setFilters}
                onApply={applyFilters}
                onClear={clearFilters}
            />

            <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-6">
                <div className="space-y-6 min-w-0">
                    <section className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
                        <div className="px-6 py-4 border-b border-border flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                            <h3 className="text-lg font-semibold">Live Device Monitoring</h3>
                            <Badge variant="secondary" className="w-fit px-2 py-0.5">
                                {deviceTotalCount} devices
                            </Badge>
                        </div>
                        {loading ? (
                            <div className="p-12 text-center text-text-secondary">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
                                Loading devices...
                            </div>
                        ) : (
                            <Table columns={deviceColumns} data={devices} />
                        )}
                        {!loading && deviceTotalCount > 0 && (
                            <Pagination
                                currentPage={devicePage}
                                totalPages={Math.ceil(deviceTotalCount / pageSize)}
                                onPageChange={setDevicePage}
                                totalCount={deviceTotalCount}
                                pageSize={pageSize}
                            />
                        )}
                    </section>

                    <section className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
                        <div className="px-6 py-4 border-b border-border flex flex-col gap-3 2xl:flex-row 2xl:items-center 2xl:justify-between">
                            <div>
                                <h3 className="text-lg font-semibold">System Alerts</h3>
                                <p className="text-xs text-text-secondary mt-1">
                                    Showing {alerts.length} of {alertTotalCount} alerts matching current filters.
                                </p>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={handleResolveAll}
                                    loading={bulkLoading}
                                    disabled={alertTotalCount === 0}
                                >
                                    <CheckCircle2 size={14} className="mr-1" />
                                    Resolve Filtered
                                </Button>
                                <Button
                                    variant="danger"
                                    size="sm"
                                    onClick={handleDeleteSelected}
                                    loading={bulkLoading}
                                    disabled={selectedAlertIds.length === 0}
                                >
                                    <Trash2 size={14} className="mr-1" />
                                    Delete Selected
                                </Button>
                                <Button
                                    variant="danger"
                                    size="sm"
                                    onClick={handleDeleteAll}
                                    loading={bulkLoading}
                                    disabled={alertTotalCount === 0}
                                >
                                    <Trash2 size={14} className="mr-1" />
                                    Delete Filtered
                                </Button>
                            </div>
                        </div>
                        <Table
                            columns={alertColumns}
                            data={alerts}
                            selectable
                            selectedIds={selectedAlertIds}
                            onSelectionChange={setSelectedAlertIds}
                        />
                        {!loading && alertTotalCount > 0 && (
                            <Pagination
                                currentPage={alertPage}
                                totalPages={Math.ceil(alertTotalCount / pageSize)}
                                onPageChange={setAlertPage}
                                totalCount={alertTotalCount}
                                pageSize={pageSize}
                            />
                        )}
                    </section>
                </div>

                <aside className="space-y-4">
                    <div className="flex items-center justify-between px-1">
                        <h3 className="text-lg font-semibold">Critical Issues</h3>
                        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-danger/10 text-danger text-[10px] font-bold uppercase tracking-wider">
                            <span className="w-1.5 h-1.5 rounded-full bg-danger animate-pulse" />
                            Live
                        </span>
                    </div>

                    <div className="space-y-4">
                        {criticalAlerts.length > 0 ? (
                            criticalAlerts.slice(0, 5).map(alert => (
                                <OfflineDeviceCard
                                    key={alert.id}
                                    title={alert.event_label || alert.event_type}
                                    deviceName={alert.device_uid}
                                    location={alert.branch_name}
                                    lastSeen={formatDate(alert.created_at, 'MMM dd, yyyy HH:mm:ss')}
                                    description={alert.description}
                                />
                            ))
                        ) : (
                            <div className="bg-card border border-dashed border-border p-8 rounded-2xl text-center">
                                <p className="text-sm text-text-muted italic">No offline devices detected</p>
                            </div>
                        )}
                    </div>
                </aside>
            </div>
        </div>
    );
};

export default DeviceHealth;

import React, { useEffect, useState } from 'react';
import { monitoringAPI } from '../api';
import OfflineDeviceCard from '../components/OfflineDeviceCard';
import StatsCard from '../../dashboard/components/StatsCard';
import Table from '../../../shared/components/Table';
import Badge from '../../../shared/components/Badge';
import Pagination from '../../../shared/components/Pagination';
import { formatDate } from '../../../shared/utils/formatDate';
import { RefreshCcw, Wifi, WifiOff } from 'lucide-react';
import { devicesAPI } from '../../devices/api';
import DeviceStatusBadge from '../../devices/components/DeviceStatusBadge';

const DeviceHealth = () => {
    const [stats, setStats] = useState({
        total_devices: 0,
        active_devices: 0,
        online_devices: 0,
        offline_alerts: 0,
        sim_change_alerts: 0,
    });
    const [alerts, setAlerts] = useState([]);
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 50;

    const fetchData = async (isBackground = false) => {
        if (!isBackground) setLoading(true);
        try {
            const statsResponse = await monitoringAPI.getDeviceHealth();
            setStats(statsResponse.data);
            await fetchAlerts(page, isBackground);

            const devicesResponse = await devicesAPI.getDevices({ page_size: 10 });
            setDevices(devicesResponse.data.results || devicesResponse.data);
        } catch (error) {
            console.error("Failed to fetch monitoring data", error);
        } finally {
            if (!isBackground) setLoading(false);
        }
    };

    const fetchAlerts = async (currentPage, isBackground = false) => {
        try {
            const alertsResponse = await monitoringAPI.getAlerts({ page: currentPage });
            setAlerts(alertsResponse.data.results || alertsResponse.data);
            setTotalCount(alertsResponse.data.count || (alertsResponse.data.results ? 0 : alertsResponse.data.length));
        } catch (error) {
            console.error("Failed to fetch alerts", error);
        }
    };

    useEffect(() => {
        fetchData();

        // Real-time updates every 10 seconds
        const intervalId = setInterval(() => {
            fetchData(true);
        }, 10000);

        return () => clearInterval(intervalId);
    }, []);

    useEffect(() => {
        if (page > 1) {
            fetchAlerts(page);
        }
    }, [page]);

    const handlePageChange = (newPage) => {
        setPage(newPage);
    };

    const columns = [
        { header: 'Device', accessor: 'device_uid' },
        { header: 'Branch', accessor: 'branch_name' },
        {
            header: 'Event',
            render: (row) => (
                <Badge variant={row.event_type === 'offline' ? 'red' : 'amber'}>
                    {row.event_type}
                </Badge>
            )
        },
        { header: 'Description', accessor: 'description' },
        { header: 'Time', render: (row) => formatDate(row.created_at) },
        {
            header: 'Status',
            render: (row) => (
                <Badge variant={row.resolved ? 'green' : 'red'}>
                    {row.resolved ? 'Resolved' : 'Active'}
                </Badge>
            )
        },
    ];

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-semibold text-gray-900">Device Health & Monitoring</h1>
                <button
                    onClick={fetchData}
                    className="p-2 text-gray-500 hover:text-sky-600 rounded-full hover:bg-sky-50 transition-all"
                    title="Refresh Data"
                >
                    <RefreshCcw size={20} className={loading ? "animate-spin" : ""} />
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard title="Total Devices" value={stats.total_devices} />
                <StatsCard title="Online Devices" value={stats.online_devices !== undefined ? stats.online_devices : stats.active_devices} />
                <StatsCard title="Offline Alerts" value={stats.offline_alerts} isNegative />
                <StatsCard title="SIM Changes" value={stats.sim_change_alerts} isNegative />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 flex flex-col space-y-4">
                    <div className="bg-white shadow rounded-lg overflow-hidden flex flex-col">
                        <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                            <h3 className="text-lg font-medium text-gray-900">Live Device Monitoring</h3>
                            <span className="text-xs text-gray-500">Showing top 10 devices</span>
                        </div>
                        <div className="overflow-x-auto text-sm">
                            <Table
                                columns={[
                                    { header: 'Device', accessor: 'device_id' },
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
                                    { header: 'Last Heartbeat', render: (row) => row.last_heartbeat ? formatDate(row.last_heartbeat, 'HH:mm:ss') : 'Never' }
                                ]}
                                data={devices}
                            />
                        </div>
                    </div>

                    <div className="bg-white shadow rounded-lg overflow-hidden flex flex-col">
                        <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                            <h3 className="text-lg font-medium text-gray-900">Recent Alerts (System Logs)</h3>
                        </div>
                        <div className="overflow-x-auto text-sm">
                            <Table columns={columns} data={alerts} />
                        </div>
                        {!loading && totalCount > pageSize && (
                            <Pagination
                                currentPage={page}
                                totalPages={Math.ceil(totalCount / pageSize)}
                                onPageChange={handlePageChange}
                            />
                        )}
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-medium text-gray-900">Critical Issues</h3>
                        <span className="px-2 py-0.5 bg-red-100 text-red-600 rounded text-xs font-bold uppercase tracking-wider">Live</span>
                    </div>
                    <div className="space-y-4">
                        {alerts.filter(a => !a.resolved && a.event_type === 'offline').slice(0, 5).map(alert => (
                            <OfflineDeviceCard
                                key={alert.id}
                                deviceName={alert.device_uid}
                                location={alert.branch_name}
                                lastSeen={alert.created_at}
                            />
                        ))}
                        {alerts.filter(a => !a.resolved && a.event_type === 'offline').length === 0 && (
                            <div className="bg-white p-8 border border-dashed border-gray-200 rounded-lg text-center opacity-60">
                                <p className="text-gray-500 text-sm">No critical offline devices reported.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeviceHealth;

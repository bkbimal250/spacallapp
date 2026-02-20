import React, { useEffect, useState } from 'react';
import { monitoringAPI } from '../api';
import OfflineDeviceCard from '../components/OfflineDeviceCard';
import StatsCard from '../../dashboard/components/StatsCard'; // Reusing StatsCard
import Table from '../../../shared/components/Table';
import Badge from '../../../shared/components/Badge';
import { formatDate } from '../../../shared/utils/formatDate';

const DeviceHealth = () => {
    const [stats, setStats] = useState({
        total_devices: 0,
        active_devices: 0,
        offline_alerts: 0,
        sim_change_alerts: 0,
    });
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                // Fetch stats
                const statsResponse = await monitoringAPI.getDeviceHealth();
                setStats(statsResponse.data);

                // Fetch recent alerts
                const alertsResponse = await monitoringAPI.getAlerts();
                setAlerts(alertsResponse.data.results || alertsResponse.data);
            } catch (error) {
                console.error("Failed to fetch monitoring data", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const columns = [
        { header: 'Device', accessor: 'device_uid' },
        { header: 'Branch', accessor: 'branch_name' },
        { header: 'Event', render: (row) => <Badge variant="red">{row.event_type}</Badge> },
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

    if (loading) return <div>Loading Monitoring Dashboard...</div>;

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-semibold text-gray-900">Device Health & Monitoring</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard title="Total Devices" value={stats.total_devices} />
                <StatsCard title="Online Devices" value={stats.active_devices} />
                <StatsCard title="Offline Alerts" value={stats.offline_alerts} isNegative />
                <StatsCard title="SIM Changes" value={stats.sim_change_alerts} isNegative />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white shadow rounded-lg overflow-hidden">
                    <div className="p-4 border-b border-gray-200">
                        <h3 className="text-lg font-medium text-gray-900">Recent Alerts</h3>
                    </div>
                    <Table columns={columns} data={alerts} />
                </div>

                <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Critical Issues</h3>
                    {/* Placeholder for critical offline devices if we want to show cards */}
                    {alerts.filter(a => !a.resolved && a.event_type === 'offline').slice(0, 3).map(alert => (
                        <OfflineDeviceCard
                            key={alert.id}
                            deviceName={alert.device_uid}
                            location={alert.branch_name}
                            lastSeen={alert.created_at}
                        />
                    ))}
                    {alerts.filter(a => !a.resolved && a.event_type === 'offline').length === 0 && (
                        <p className="text-gray-500">No critical offline devices reported.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DeviceHealth;

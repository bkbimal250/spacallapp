import React from 'react';
import { RefreshCcw } from 'lucide-react';
import StatsCard from '../../dashboard/components/StatsCard';
import Table from '../../../shared/components/Table';
import Pagination from '../../../shared/components/Pagination';
import Badge from '../../../shared/components/Badge';
import DeviceStatusBadge from '../../devices/components/DeviceStatusBadge';
import OfflineDeviceCard from '../components/OfflineDeviceCard';
import { formatDate } from '../../../shared/utils/formatDate';

const DeviceHealthUI = ({
    stats = {},
    alerts = [],
    devices = [],
    loading = false,
    page = 1,
    totalCount = 0,
    pageSize = 10,
    fetchData,
    handleResolveAlert,
    handleDeleteAlert,
    handlePageChange
}) => {

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
            header: 'Time',
            render: (row) => formatDate(row.created_at)
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

        <div className="space-y-6 text-text-primary">

            <div className="flex items-center justify-between">

                <h1 className="text-2xl font-bold">
                    Device Health & Monitoring
                </h1>

                <button
                    onClick={fetchData}
                    className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-border bg-card hover:bg-cardHover transition"
                >
                    <RefreshCcw
                        size={16}
                        className={loading ? "animate-spin" : ""}
                    />
                    Refresh
                </button>

            </div>


            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

                <StatsCard
                    title="Total Devices"
                    value={stats?.total_devices || 0}
                />

                <StatsCard
                    title="Online Devices"
                    value={stats?.online_devices || 0}
                    color="success"
                />

                <StatsCard
                    title="Offline Alerts"
                    value={stats?.offline_alerts || 0}
                    color="danger"
                />

                <StatsCard
                    title="SIM Change Alerts"
                    value={stats?.sim_change_alerts || 0}
                    color="warning"
                />

            </div>


            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">


                <div className="lg:col-span-2 space-y-6">


                    <div className="bg-card border border-border rounded-xl shadow-lg">

                        <div className="flex items-center justify-between p-4 border-b border-border">

                            <h3 className="text-lg font-semibold">
                                Live Device Monitoring
                            </h3>

                            <span className="text-xs text-text-secondary">
                                Top 10 Devices
                            </span>

                        </div>

                        <div className="overflow-x-auto">

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

                                    {
                                        header: 'Last Heartbeat',
                                        render: (row) =>
                                            row.last_heartbeat
                                                ? formatDate(row.last_heartbeat, 'HH:mm:ss')
                                                : 'Never'
                                    }
                                ]}
                                data={devices || []}
                            />

                        </div>

                    </div>


                    <div className="bg-card border border-border rounded-xl shadow-lg">

                        <div className="p-4 border-b border-border">

                            <h3 className="text-lg font-semibold">
                                Recent Alerts
                            </h3>

                        </div>

                        <div className="overflow-x-auto">

                            <Table
                                columns={alertColumns}
                                data={alerts || []}
                            />

                        </div>

                        {totalCount > pageSize && (

                            <div className="p-4 border-t border-border">

                                <Pagination
                                    currentPage={page}
                                    totalPages={Math.ceil(totalCount / pageSize)}
                                    onPageChange={handlePageChange}
                                />

                            </div>

                        )}

                    </div>

                </div>


                <div className="space-y-4">


                    <div className="flex items-center justify-between">

                        <h3 className="text-lg font-semibold">
                            Critical Issues
                        </h3>

                        <span className="text-xs font-semibold px-2 py-1 rounded bg-danger/20 text-danger">
                            LIVE
                        </span>

                    </div>


                    <div className="space-y-4">

                        {offlineAlerts.slice(0, 5).map(alert => (

                            <OfflineDeviceCard
                                key={alert.id}
                                deviceName={alert.device_uid}
                                location={alert.branch_name}
                                lastSeen={alert.created_at}
                            />

                        ))}

                        {offlineAlerts.length === 0 && (

                            <div className="bg-card border border-dashed border-border p-6 rounded-lg text-center text-sm text-text-secondary">
                                No offline devices detected
                            </div>

                        )}

                    </div>

                </div>

            </div>

        </div>

    );
};

export default DeviceHealthUI;
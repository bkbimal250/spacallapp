import React, { useEffect, useState } from 'react';
import { devicesAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import DeviceStatusBadge from '../components/DeviceStatusBadge';
import DeviceForm from '../components/DeviceForm';
import DeviceFilter from '../components/DeviceFilter';
import Pagination from '../../../shared/components/Pagination';
import { Bell, CheckCircle2, Copy, Edit, Trash2, Plus, Smartphone, RefreshCcw } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';
import StatsCard from '../components/StatsCard';
import { useAuth } from '../../../shared/hooks/useAuth';
import { addItemToList, mergeExistingItemsById, removeItemFromList, updateItemInList } from '../../../shared/utils/listState';

const DeviceList = () => {
    const { user } = useAuth();
    const isSuperAdmin = user?.role === 'super_admin';

    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingDevice, setEditingDevice] = useState(null);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [rowAction, setRowAction] = useState({});
    const [saving, setSaving] = useState(false);

    const pageSize = 100;

    const fetchDevices = async (currentFilters = {}, currentPage = 1, isBackground = false) => {

        if (!isBackground) setLoading(true);

        try {

            const response = await devicesAPI.getDevices({
                ...currentFilters,
                page: currentPage,
                page_size: pageSize
            });

            const data = response.data.results || response.data;

            setDevices(prev => isBackground ? mergeExistingItemsById(prev, data) : data);
            setTotalCount(response.data.count || data.length);

        } catch (error) {

            console.error("Failed to fetch devices", error);

        } finally {

            if (!isBackground) setLoading(false);

        }

    };

    useEffect(() => {

        fetchDevices(filters, page);

        const intervalId = setInterval(() => {
            fetchDevices(filters, page, true);
        }, 10000);

        return () => clearInterval(intervalId);

    }, [filters, page]);

    const handleFilter = (newFilters) => {
        setFilters(newFilters);
        setPage(1);
    };

    const handlePageChange = (newPage) => {
        setPage(newPage);
    };

    const handleCreate = () => {
        setEditingDevice(null);
        setIsModalOpen(true);
    };

    const setActionLoading = (id, action, value) => {
        setRowAction(prev => ({ ...prev, [`${action}:${id}`]: value }));
    };

    const isActionLoading = (id, action) => Boolean(rowAction[`${action}:${id}`]);

    const deviceMatchesFilters = (device) => {
        if (!device) return false;
        if (filters.branch && device.branch !== filters.branch) return false;
        if (filters.city) return false;
        if (filters.is_registered !== undefined && String(Boolean(device.is_registered)) !== String(filters.is_registered)) return false;
        if (filters.has_android_id !== undefined && String(Boolean(device.android_id)) !== String(filters.has_android_id)) return false;
        if (filters.compliance_status && device.compliance_status !== filters.compliance_status) return false;
        if (filters.is_active !== undefined && String(Boolean(device.is_active)) !== String(filters.is_active)) return false;
        if (filters.is_blocked !== undefined && String(Boolean(device.is_blocked)) !== String(filters.is_blocked)) return false;
        if (filters.search) {
            const haystack = [
                device.device_id,
                device.phone_name,
                device.android_id,
                device.branch_name,
                device.registration_token,
            ].filter(Boolean).join(' ').toLowerCase();
            if (!haystack.includes(String(filters.search).toLowerCase())) return false;
        }
        if (filters.start_date || filters.end_date || filters.quick_date) return false;
        return true;
    };

    const handleRegenerateToken = async (id) => {
        if (!isSuperAdmin) return;
        if (window.confirm("Are you sure you want to regenerate the token? This will invalidate current registration and generate a new token.")) {
            setActionLoading(id, 'token', true);
            try {
                const response = await devicesAPI.regenerateToken(id);
                const token = response.data?.new_token;
                setDevices(prev => updateItemInList(prev, {
                    id,
                    registration_token: token,
                    is_registered: false,
                    device_id: null,
                    android_id: null,
                    fcm_present: false,
                    fcm_token: null,
                    compliance_status: 'AUTH_BROKEN',
                    compliance_reason: 'Device registration token was regenerated.',
                }));
                setEditingDevice(prev => prev?.id === id ? {
                    ...prev,
                    registration_token: token,
                    is_registered: false,
                    device_id: null,
                    android_id: null,
                } : prev);
            } catch (error) {
                console.error("Failed to regenerate token", error);
                alert("Failed to regenerate token. Please try again.");
            } finally {
                setActionLoading(id, 'token', false);
            }
        }
    };

    const handleEdit = (device) => {
        setEditingDevice(device);
        setIsModalOpen(true);
    };

    const handleDelete = async (id) => {

        if (window.confirm("Are you sure you want to delete this device?")) {

            setActionLoading(id, 'delete', true);
            try {

                await devicesAPI.deleteDevice(id);
                setDevices(prev => removeItemFromList(prev, id));
                setTotalCount(prev => Math.max(0, prev - 1));
                setEditingDevice(prev => prev?.id === id ? null : prev);
                if (devices.length === 1 && page > 1) {
                    setPage(prev => Math.max(1, prev - 1));
                }

            } catch (error) {

                console.error("Failed to delete device", error);
                alert("Failed to delete device.");
            } finally {
                setActionLoading(id, 'delete', false);

            }

        }

    };

    const handleSendUpdateNotification = async (device) => {
        setActionLoading(device.id, 'notify', true);
        try {
            const response = await devicesAPI.sendUpdateNotification(device.id);
            alert(response.data.sent ? "Update notification sent." : `Notification not sent: ${response.data.result}`);
            if (response.data.status || response.data.reason) {
                const updated = {
                    id: device.id,
                    compliance_status: response.data.status,
                    compliance_reason: response.data.reason,
                };
                setDevices(prev => updateItemInList(prev, updated));
                setEditingDevice(prev => prev?.id === device.id ? { ...prev, ...updated } : prev);
            }
        } catch (error) {
            console.error("Failed to send update notification", error);
            alert("Failed to send update notification.");
        } finally {
            setActionLoading(device.id, 'notify', false);
        }
    };

    const handleMarkFollowedUp = async (device) => {
        setActionLoading(device.id, 'followup', true);
        try {
            const response = await devicesAPI.markFollowedUp(device.id);
            const updated = {
                id: device.id,
                compliance_followed_up_at: response.data?.followed_up_at,
            };
            setDevices(prev => updateItemInList(prev, updated));
            setEditingDevice(prev => prev?.id === device.id ? { ...prev, ...updated } : prev);
        } catch (error) {
            console.error("Failed to mark followed up", error);
            alert("Failed to mark followed up.");
        } finally {
            setActionLoading(device.id, 'followup', false);
        }
    };

    const complianceClass = (status) => {
        if (!status || status === 'OK') return 'bg-success/10 text-success border-success/20';
        if (status === 'SUSPECTED_UNINSTALLED' || status === 'AUTH_BROKEN') return 'bg-danger/10 text-danger border-danger/20';
        return 'bg-warning/10 text-warning border-warning/20';
    };


    const handleSubmit = async (data) => {

        setSaving(true);
        try {

            if (editingDevice) {
                const response = await devicesAPI.updateDevice(editingDevice.id, data);
                setDevices(prev => updateItemInList(prev, response.data));
                setEditingDevice(prev => prev?.id === editingDevice.id ? { ...prev, ...response.data } : prev);
            } else {
                const response = await devicesAPI.createDevice(data);
                if (deviceMatchesFilters(response.data)) {
                    setDevices(prev => addItemToList(prev, response.data));
                    setTotalCount(prev => prev + 1);
                } else {
                    alert("Created successfully. It may not appear because current filters are active.");
                }
            }

            setIsModalOpen(false);

        } catch (error) {

            console.error("Failed to save device", error);
            alert("Failed to save device.");
        } finally {
            setSaving(false);

        }

    };

    const columns = [

        {
            header: 'Device ID',
            render: (row) => (
                <div className="flex items-center">

                    <Smartphone
                        size={16}
                        className={`mr-2 ${row.is_registered ? "text-primary" : "text-warning"
                            }`}
                    />

                    <span
                        className={`font-mono text-xs ${row.is_registered
                            ? "text-text-primary"
                            : "text-warning italic font-semibold"
                            }`}
                    >
                        {row.device_id || "PENDING REGISTRATION"}
                    </span>

                </div>
            )
        },
        {
            header: 'Phone Name',
            accessor: 'phone_name',
            render: (row) => (
                <span className="font-semibold text-text-primary capitalize">
                    {row.phone_name || "—"}
                </span>
            )
        },
        {
            header: 'Android ID',
            render: (row) => (
                <div className="space-y-1">
                    <span className="font-mono text-xs text-text-secondary">
                        {row.android_id || "—"}
                    </span>
                    <div>
                        <span
                            title={row.compliance_reason}
                            className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${complianceClass(row.compliance_status)}`}
                        >
                            {row.compliance_status || 'OK'}
                        </span>
                    </div>
                    {row.app_version && (
                        <div className="text-[10px] text-text-muted">App {row.app_version}</div>
                    )}
                    <div className="text-[10px] text-text-muted">
                        FCM {row.fcm_present ? 'Yes' : 'No'}
                    </div>
                    <div className="text-[10px] text-text-muted">
                        Last seen {formatDate(row.last_seen_at || row.last_heartbeat, 'MMM dd, HH:mm')}
                    </div>
                </div>
            )
        },
        {
            header: 'App / Phone',
            render: (row) => (
                <div className="space-y-1 min-w-[140px]">
                    <div className="text-xs font-semibold text-text-primary">
                        {row.app_version ? `App ${row.app_version}` : 'App —'}
                    </div>
                    <div className="text-[11px] text-text-secondary">
                        {[row.manufacturer, row.device_model].filter(Boolean).join(' ') || 'Model —'}
                    </div>
                </div>
            )
        },

        {
            header: 'Reg. Token',
            render: (row) => (
                <div className="flex items-center gap-3 min-w-[200px]">
                    {row.registration_token ? (
                        <div className="flex items-center gap-2 flex-1">
                            <code className="bg-primary/5 text-primary border border-primary/10 px-2 py-1 rounded text-[11px] font-mono flex-1 truncate">
                                {row.registration_token}
                            </code>
                            <div className="flex items-center gap-1 shrink-0">
                                <button
                                    onClick={() => {
                                        navigator.clipboard.writeText(row.registration_token);
                                        alert("Registration token copied!");
                                    }}
                                    className="p-1 rounded text-text-muted hover:text-primary hover:bg-primary/5 transition-colors"
                                    title="Copy Token"
                                >
                                    <Smartphone size={14} />
                                </button>
                                {isSuperAdmin && (
                                    <button
                                        onClick={() => handleRegenerateToken(row.id)}
                                        disabled={isActionLoading(row.id, 'token')}
                                        className="p-1 rounded text-text-muted hover:text-warning hover:bg-warning/5 transition-colors disabled:opacity-50"
                                        title="Regenerate Token"
                                    >
                                        <RefreshCcw size={14} className={isActionLoading(row.id, 'token') ? 'animate-spin' : ''} />
                                    </button>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center gap-3">
                            <span className="bg-success/10 text-success border border-success/20 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider">
                                Claimed
                            </span>
                            {isSuperAdmin && (
                                <button
                                    onClick={() => handleRegenerateToken(row.id)}
                                    disabled={isActionLoading(row.id, 'token')}
                                    className="p-1 rounded text-text-muted hover:text-warning hover:bg-warning/5 transition-colors disabled:opacity-50"
                                    title="Regenerate Token"
                                >
                                    <RefreshCcw size={14} className={isActionLoading(row.id, 'token') ? 'animate-spin' : ''} />
                                </button>
                            )}
                        </div>
                    )}
                </div>
            )
        },

        {
            header: 'Spa / Branch',
            render: (row) => (
                <div className="flex items-center gap-3">
                    <span className="font-bold text-text-primary text-sm whitespace-nowrap">
                        {row.branch_name || "—"}
                    </span>
                    <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border shadow-sm ${(row.branch_is_active === 'True' || row.branch_is_active === true)
                        ? 'bg-success/5 text-success border-success/20'
                        : 'bg-danger/5 text-danger border-danger/20'
                        }`}>
                        <div className={`w-1 h-1 rounded-full ${(row.branch_is_active === 'True' || row.branch_is_active === true)
                            ? 'bg-success shadow-[0_0_4px_rgba(34,197,94,0.5)]'
                            : 'bg-danger shadow-[0_0_4px_rgba(239,68,68,0.5)]'
                            }`} />
                        <span className="text-[9px] font-bold uppercase tracking-wider">
                            {(row.branch_is_active === 'True' || row.branch_is_active === true) ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                </div>
            )
        },

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
            header: 'Last Sync',
            render: (row) => (
                <span className="text-text-secondary text-sm">
                    {formatDate(row.last_sync, 'MMM dd, HH:mm')}
                </span>
            )
        },

        {
            header: 'Actions',
            render: (row) => (

                <div className="flex gap-2">

                    <button
                        onClick={() => handleEdit(row)}
                        disabled={Object.keys(rowAction).some(key => key.endsWith(`:${row.id}`) && rowAction[key])}
                        className="p-1.5 rounded-lg text-blue-500 hover:bg-blue-500/10 transition-colors"
                        title="Edit Device"
                    >
                        <Edit size={16} />
                    </button>
                    <button
                        onClick={() => handleSendUpdateNotification(row)}
                        disabled={isActionLoading(row.id, 'notify')}
                        className="p-1.5 rounded-lg text-warning hover:bg-warning/10 transition-colors disabled:opacity-50"
                        title="Send Update Notification"
                    >
                        <Bell size={16} className={isActionLoading(row.id, 'notify') ? 'animate-pulse' : ''} />
                    </button>
                    <button
                        onClick={() => handleMarkFollowedUp(row)}
                        disabled={isActionLoading(row.id, 'followup')}
                        className="p-1.5 rounded-lg text-success hover:bg-success/10 transition-colors disabled:opacity-50"
                        title="Mark Followed Up"
                    >
                        <CheckCircle2 size={16} />
                    </button>
                    <button
                        onClick={() => {
                            navigator.clipboard.writeText('https://mastercall.in/download');
                            alert('Download link copied!');
                        }}
                        className="p-1.5 rounded-lg text-primary hover:bg-primary/10 transition-colors"
                        title="Copy Download Link"
                    >
                        <Copy size={16} />
                    </button>
                    <button
                        onClick={() => handleDelete(row.id)}
                        disabled={isActionLoading(row.id, 'delete')}
                        className="p-1.5 rounded-lg text-danger hover:bg-danger/10 transition-colors disabled:opacity-50"
                        title="Delete Device"
                    >
                        <Trash2 size={16} />
                    </button>

                </div>

            )
        }

    ];

    return (

        <div className="space-y-6">

            {/* HEADER */}

            <div className="flex justify-between items-center">

                <h1 className="text-2xl font-semibold text-text-primary">
                    Devices
                </h1>

                <Button
                    onClick={handleCreate}
                    className="flex items-center gap-2"
                >
                    <Plus size={16} />
                    Add Device
                </Button>

            </div>

            {/* STATS */}
            <StatsCard />

            {/* FILTER */}

            <div className="bg-card border border-border rounded-2xl p-6 relative z-20">

                <DeviceFilter onFilter={handleFilter} />

            </div>

            {/* TABLE */}

            <div className="bg-card border border-border rounded-2xl overflow-hidden flex flex-col">

                <div className="overflow-x-auto">

                    {loading ? (

                        <div className="p-12 text-center text-text-secondary">

                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>

                            Loading devices...

                        </div>

                    ) : (

                        <Table
                            columns={columns}
                            data={devices}
                        />

                    )}

                </div>

                {!loading && totalCount > 0 && (

                    <Pagination
                        currentPage={page}
                        totalPages={Math.ceil(totalCount / pageSize)}
                        onPageChange={handlePageChange}
                        totalCount={totalCount}
                        pageSize={pageSize}
                    />

                )}

            </div>

            <DeviceForm
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleSubmit}
                initialData={editingDevice}
                saving={saving}
            />

        </div>
    );
};

export default DeviceList;

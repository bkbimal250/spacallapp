import React, { useEffect, useState } from 'react';
import { devicesAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import DeviceStatusBadge from '../components/DeviceStatusBadge';
import DeviceForm from '../components/DeviceForm';
import DeviceFilter from '../components/DeviceFilter';
import Pagination from '../../../shared/components/Pagination';
import { Edit, Trash2, Plus, Smartphone, RefreshCcw } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';
import StatsCard from '../components/StatsCard';
import { useAuth } from '../../../shared/hooks/useAuth';

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

    const pageSize = 100;

    const fetchDevices = async (currentFilters = {}, currentPage = 1, isBackground = false) => {

        if (!isBackground) setLoading(true);

        try {

            const response = await devicesAPI.getDevices({
                ...currentFilters,
                page: currentPage
            });

            const data = response.data.results || response.data;

            setDevices(data);
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

    const handleRegenerateToken = async (id) => {
        if (!isSuperAdmin) return;
        if (window.confirm("Are you sure you want to regenerate the token? This will invalidate current registration and generate a new token.")) {
            try {
                await devicesAPI.regenerateToken(id);
                fetchDevices(filters, page);
            } catch (error) {
                console.error("Failed to regenerate token", error);
                alert("Failed to regenerate token. Please try again.");
            }
        }
    };

    const handleEdit = (device) => {
        setEditingDevice(device);
        setIsModalOpen(true);
    };

    const handleDelete = async (id) => {

        if (window.confirm("Are you sure you want to delete this device?")) {

            try {

                await devicesAPI.deleteDevice(id);
                fetchDevices(filters, page);

            } catch (error) {

                console.error("Failed to delete device", error);

            }

        }

    };


    const handleSubmit = async (data) => {

        try {

            if (editingDevice) {
                await devicesAPI.updateDevice(editingDevice.id, data);
            } else {
                await devicesAPI.createDevice(data);
            }

            setIsModalOpen(false);
            fetchDevices(filters, page);

        } catch (error) {

            console.error("Failed to save device", error);

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
                                        className="p-1 rounded text-text-muted hover:text-warning hover:bg-warning/5 transition-colors"
                                        title="Regenerate Token"
                                    >
                                        <RefreshCcw size={14} />
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
                                    className="p-1 rounded text-text-muted hover:text-warning hover:bg-warning/5 transition-colors"
                                    title="Regenerate Token"
                                >
                                    <RefreshCcw size={14} />
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
                        className="p-1.5 rounded-lg text-blue-500 hover:bg-blue-500/10 transition-colors"
                        title="Edit Device"
                    >
                        <Edit size={16} />
                    </button>
                    <button
                        onClick={() => handleDelete(row.id)}
                        className="p-1.5 rounded-lg text-danger hover:bg-danger/10 transition-colors"
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
            />

        </div>
    );
};

export default DeviceList;
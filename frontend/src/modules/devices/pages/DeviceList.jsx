import React, { useEffect, useState } from 'react';
import { devicesAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import DeviceStatusBadge from '../components/DeviceStatusBadge';
import DeviceForm from '../components/DeviceForm';
import DeviceFilter from '../components/DeviceFilter';
import Pagination from '../../../shared/components/Pagination';
import { Edit, Trash2, Plus, Smartphone } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';
import StatsCard from '../components/StatsCard';

const DeviceList = () => {

    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingDevice, setEditingDevice] = useState(null);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);

    const pageSize = 50;

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
            header: 'Reg. Token',
            render: (row) => row.is_registered ? (

                <span className="text-text-muted text-xs">
                    — Registered —
                </span>

            ) : (

                <div className="flex items-center group">

                    {row.registration_token ? (

                        <>
                            <code className="bg-primary/10 text-primary px-2 py-1 rounded-md text-xs font-mono">
                                {row.registration_token}
                            </code>

                            <button
                                onClick={() => {
                                    navigator.clipboard.writeText(row.registration_token);
                                    alert("Registration token copied!");
                                }}
                                className="ml-2 p-1 rounded-md text-text-muted hover:text-primary hover:bg-primary/10 transition"
                                title="Copy Token"
                            >
                                📋
                            </button>
                        </>

                    ) : (

                        <span className="text-warning text-xs italic">
                            Token Unassigned
                        </span>

                    )}

                </div>

            )
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
                        className="p-1 rounded-md text-info hover:bg-info/10"
                        title="Edit"
                    >
                        <Edit size={16} />
                    </button>

                    <button
                        onClick={() => handleDelete(row.id)}
                        className="p-1 rounded-md text-danger hover:bg-danger/10"
                        title="Delete"
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

            <div className="bg-card border border-border rounded-2xl p-6">

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

                {!loading && totalCount > 0 && Math.ceil(totalCount / pageSize) > 1 && (

                    <Pagination
                        currentPage={page}
                        totalPages={Math.ceil(totalCount / pageSize)}
                        onPageChange={handlePageChange}
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
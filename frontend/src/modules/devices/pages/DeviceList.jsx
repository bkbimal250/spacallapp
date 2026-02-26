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

const DeviceList = () => {
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingDevice, setEditingDevice] = useState(null);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 20;

    const fetchDevices = async (currentFilters = {}, currentPage = 1) => {
        setLoading(true);
        try {
            const response = await devicesAPI.getDevices({ ...currentFilters, page: currentPage });
            if (response.data.results) {
                setDevices(response.data.results);
                setTotalCount(response.data.count);
            } else {
                setDevices(response.data);
                setTotalCount(response.data.length);
            }
        } catch (error) {
            console.error("Failed to fetch devices", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDevices(filters, page);
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
                    <Smartphone size={16} className={`mr-2 ${row.is_registered ? 'text-indigo-500' : 'text-amber-400'}`} />
                    <span className={`font-mono text-xs ${row.is_registered ? 'text-gray-900' : 'text-amber-600 italic font-bold'}`}>
                        {row.device_id || 'PENDING REGISTRATION'}
                    </span>
                </div>
            )
        },
        {
            header: 'Reg. Token',
            render: (row) => row.is_registered ? (
                <span className="text-gray-300 text-[10px]">—</span>
            ) : (
                <div className="flex items-center group">
                    <code className="bg-indigo-50 text-indigo-700 px-2 py-1 rounded border border-indigo-100 font-black text-xs tracking-wider">
                        {row.registration_token}
                    </code>
                    <button
                        onClick={() => {
                            navigator.clipboard.writeText(row.registration_token);
                            alert('Token copied!');
                        }}
                        className="ml-2 p-1 text-gray-400 hover:text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Copy Token"
                    >
                        <svg size={12} fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-3 h-3"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg>
                    </button>
                </div>
            )
        },
        { header: 'Branch', accessor: 'branch_name' },
        {
            header: 'Status',
            render: (row) => <DeviceStatusBadge isActive={row.is_active} isBlocked={row.is_blocked} isRegistered={row.is_registered} />
        },
        { header: 'Last Sync', render: (row) => formatDate(row.last_sync, 'MMM dd, HH:mm') },

        {
            header: 'Actions',
            render: (row) => (
                <div className="flex space-x-2">
                    <button onClick={() => handleEdit(row)} className="text-blue-600 hover:text-blue-800 p-1 hover:bg-blue-50 rounded transition-colors" title="Edit">
                        <Edit size={16} />
                    </button>
                    <button onClick={() => handleDelete(row.id)} className="text-red-600 hover:text-red-800 p-1 hover:bg-red-50 rounded transition-colors" title="Delete">
                        <Trash2 size={16} />
                    </button>
                </div>
            ),
        },
    ];

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-semibold text-gray-900">Devices</h1>
                <Button onClick={handleCreate} className="flex items-center space-x-2">
                    <Plus size={16} />
                    <span>Add Device</span>
                </Button>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
                <DeviceFilter onFilter={handleFilter} />
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden flex flex-col">
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-12 text-center text-gray-500">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500 mx-auto mb-4"></div>
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

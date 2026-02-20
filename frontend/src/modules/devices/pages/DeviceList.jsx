import React, { useEffect, useState } from 'react';
import { devicesAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import DeviceStatusBadge from '../components/DeviceStatusBadge';
import DeviceForm from '../components/DeviceForm'; // Assuming you have this or will create it
import { Edit, Trash2, Plus, Smartphone } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';

const DeviceList = () => {
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingDevice, setEditingDevice] = useState(null);

    const fetchDevices = async () => {
        setLoading(true);
        try {
            const response = await devicesAPI.getDevices();
            setDevices(response.data?.results || response.data || []);
        } catch (error) {
            console.error("Failed to fetch devices", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDevices();
    }, []);

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
                fetchDevices();
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
            fetchDevices();
        } catch (error) {
            console.error("Failed to save device", error);
        }
    };

    const columns = [
        {
            header: 'Device ID',
            render: (row) => (
                <div className="flex items-center">
                    <Smartphone size={16} className="mr-2 text-gray-400" />
                    <span className="font-medium text-gray-900">{row.device_id}</span>
                </div>
            )
        },
        { header: 'Branch', accessor: 'branch_name' },
        { header: 'SIM 1', accessor: 'sim_1_number' },
        { header: 'SIM 2', accessor: 'sim_2_number' },
        { header: 'Status', render: (row) => <DeviceStatusBadge isActive={row.is_active} isBlocked={row.is_blocked} /> },
        { header: 'Last Sync', render: (row) => formatDate(row.last_sync) },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex space-x-2">
                    <button onClick={() => handleEdit(row)} className="text-blue-600 hover:text-blue-800">
                        <Edit size={16} />
                    </button>
                    <button onClick={() => handleDelete(row.id)} className="text-red-600 hover:text-red-800">
                        <Trash2 size={16} />
                    </button>
                </div>
            ),
        },
    ];

    if (loading) return <div>Loading...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-semibold text-gray-900">Devices</h1>
                <Button onClick={handleCreate} className="flex items-center space-x-2">
                    <Plus size={16} />
                    <span>Add Device</span>
                </Button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
                <Table
                    columns={columns}
                    data={devices}
                />
            </div>

            {/* Reusing the DeviceForm component created earlier or ensuring it handles the props correctly */}
            <DeviceForm
                isOpen={isModalOpen} // Ensure DeviceForm supports 'isOpen' for modal behavior or wrap it
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleSubmit}
                initialData={editingDevice}
            />
        </div>
    );
};

export default DeviceList;

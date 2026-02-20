import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';
import { branchesAPI } from '../../branches/api';

const DeviceForm = ({ isOpen, onClose, onSubmit, initialData }) => {
    const [branches, setBranches] = useState([]);
    const [formData, setFormData] = useState({
        device_id: '',
        branch: '',
        sim_1_number: '',
        sim_2_number: '',
        is_active: true,
        is_blocked: false,
    });

    useEffect(() => {
        const fetchBranches = async () => {
            try {
                const response = await branchesAPI.getBranches();
                setBranches(response.data?.results || response.data || []);
            } catch (error) {
                console.error("Failed to load branches for device form", error);
            }
        };
        fetchBranches();
    }, []);

    useEffect(() => {
        if (initialData) {
            setFormData({
                device_id: initialData.device_id || '',
                branch: initialData.branch || '',
                sim_1_number: initialData.sim_1_number || '',
                sim_2_number: initialData.sim_2_number || '',
                is_active: initialData.is_active !== undefined ? initialData.is_active : true,
                is_blocked: initialData.is_blocked || false,
            });
        } else {
            setFormData({
                device_id: '',
                branch: '',
                sim_1_number: '',
                sim_2_number: '',
                is_active: true,
                is_blocked: false,
            });
        }
    }, [initialData, isOpen]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const submitData = { ...formData };
        if (!submitData.branch) {
            submitData.branch = null;
        }
        onSubmit(submitData);
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={initialData ? 'Edit Device' : 'Register Device'}>
            <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                    label="Device ID"
                    name="device_id"
                    value={formData.device_id}
                    onChange={handleChange}
                    required
                    disabled={!!initialData}
                />

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Assigned Branch</label>
                    <select
                        name="branch"
                        value={formData.branch}
                        onChange={handleChange}
                        className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border text-sm"
                    >
                        <option value="">Select a branch</option>
                        {branches.map(b => (
                            <option key={b.id} value={b.id}>{b.spa_name} ({b.code})</option>
                        ))}
                    </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <Input
                        label="SIM 1 Number"
                        name="sim_1_number"
                        value={formData.sim_1_number}
                        onChange={handleChange}
                        required
                    />
                    <Input
                        label="SIM 2 Number"
                        name="sim_2_number"
                        value={formData.sim_2_number}
                        onChange={handleChange}
                    />
                </div>

                <div className="flex space-x-6 pt-2">
                    <div className="flex items-center">
                        <input
                            type="checkbox"
                            id="is_active"
                            name="is_active"
                            checked={formData.is_active}
                            onChange={handleChange}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                            Is Active
                        </label>
                    </div>

                    <div className="flex items-center">
                        <input
                            type="checkbox"
                            id="is_blocked"
                            name="is_blocked"
                            checked={formData.is_blocked}
                            onChange={handleChange}
                            className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                        />
                        <label htmlFor="is_blocked" className="ml-2 block text-sm text-gray-900">
                            Is Blocked
                        </label>
                    </div>
                </div>

                <div className="flex justify-end space-x-2 mt-6">
                    <Button variant="secondary" onClick={onClose} type="button">
                        Cancel
                    </Button>
                    <Button type="submit">
                        {initialData ? 'Update' : 'Register'}
                    </Button>
                </div>
            </form>
        </Modal>
    );
};

export default DeviceForm;

import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';
import { branchesAPI } from '../../branches/api';
import SearchableSelect from '../../../shared/components/SearchableSelect';

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
                {!initialData && (
                    <div className="bg-indigo-50/50 p-4 rounded-xl border border-indigo-100 mb-6">
                        <h4 className="text-xs font-black text-indigo-700 uppercase tracking-widest mb-1 flex items-center">
                            <span className="h-2 w-2 bg-indigo-500 rounded-full mr-2 animate-pulse"></span>
                            Smart Registration Mode
                        </h4>
                        <p className="text-[11px] text-indigo-600 leading-relaxed font-medium">
                            Creating this device will automatically generate a <b>Registration Token</b>.
                            Provide this token to the installer to securely link the Android device.
                        </p>
                    </div>
                )}

                <Input
                    label="Device ID (Auto-generated after registration)"
                    name="device_id"
                    value={formData.device_id}
                    onChange={handleChange}
                    placeholder="Pending activation..."
                    disabled={true} // Now always disabled as it's auto-generated via claim
                />

                <div className="grid grid-cols-2 gap-4">


                    <div className="col-span-1">
                        <SearchableSelect
                            label="Assigned Branch"
                            options={branches.map(b => ({
                                value: b.id,
                                label: `${b.spa_name} (${b.code})`
                            }))}
                            value={formData.branch}
                            onChange={(value) => setFormData(prev => ({ ...prev, branch: value }))}
                            placeholder="Search & select branch..."
                        />
                    </div>


                    <div className="flex flex-col justify-end">
                        <div className="flex space-x-4 pb-2 ml-1">
                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    id="is_active"
                                    name="is_active"
                                    checked={formData.is_active}
                                    onChange={handleChange}
                                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded-lg cursor-pointer transition-all"
                                />
                                <label htmlFor="is_active" className="ml-2 block text-xs font-bold text-gray-700 cursor-pointer">
                                    Enabled
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <Input
                        label="SIM 1 Number (Optional)"
                        name="sim_1_number"
                        value={formData.sim_1_number}
                        onChange={handleChange}
                        placeholder="+91..."
                    />
                    <Input
                        label="SIM 2 Number (Optional)"
                        name="sim_2_number"
                        value={formData.sim_2_number}
                        onChange={handleChange}
                        placeholder="+91..."
                    />
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

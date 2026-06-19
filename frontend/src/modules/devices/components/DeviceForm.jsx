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
        phone_name: '',
        branch: '',
        sim_1_number: '',
        sim_2_number: '',
        is_active: true,
        is_blocked: false,
    });

    useEffect(() => {

        const fetchBranches = async () => {

            try {

                const response = await branchesAPI.getBranches({ all: true });

                setBranches(
                    response.data?.results ||
                    response.data ||
                    []
                );

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
                phone_name: initialData.phone_name || '',
                branch: initialData.branch || '',
                sim_1_number: initialData.sim_1_number || '',
                sim_2_number: initialData.sim_2_number || '',
                is_active: initialData.is_active !== undefined ? initialData.is_active : true,
                is_blocked: initialData.is_blocked || false,
            });

        } else {

            setFormData({
                device_id: '',
                phone_name: '',
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

        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={initialData ? 'Edit Device' : 'Register Device'}
        >

            <form
                onSubmit={handleSubmit}
                className="space-y-6"
            >

                {/* REGISTRATION INFO */}

                {!initialData && (

                    <div className="bg-primary/10 p-4 rounded-xl border border-primary/20 mb-6">

                        <h4 className="text-xs font-bold text-primary uppercase tracking-widest mb-1 flex items-center">

                            <span className="h-2 w-2 bg-primary rounded-full mr-2 animate-pulse"></span>

                            Smart Registration Mode

                        </h4>

                        <p className="text-xs text-text-secondary leading-relaxed">

                            Creating this device will generate a <b>Registration Token</b>.
                            Provide this token to the installer to securely link the Android device.

                        </p>

                    </div>

                )}

                {/* DEVICE ID */}

                <Input
                    label="Device ID"
                    name="device_id"
                    value={formData.device_id}
                    onChange={handleChange}
                    placeholder="Pending activation..."
                    disabled
                />

                <Input
                    label="Phone Name (e.g. Reception Desk)"
                    name="phone_name"
                    value={formData.phone_name}
                    onChange={handleChange}
                    placeholder="Enter phone name..."
                />

                {/* BRANCH + STATUS */}

                <div className="grid grid-cols-1 gap-4">

                    <div >

                        <SearchableSelect
                            label="Assigned Branch"
                            options={branches.map(b => ({
                                value: b.id,
                                label: `${b.spa_name} (${b.code})`,
                                searchText: [
                                    b.spa_name,
                                    b.code,
                                    b.city,
                                    b.area,
                                    b.state,
                                    b.address,
                                    b.phone,
                                    b.branch_group_name,
                                ].filter(Boolean).join(' ')
                            }))}
                            value={formData.branch}
                            onChange={(value) =>
                                setFormData(prev => ({
                                    ...prev,
                                    branch: value
                                }))
                            }
                            placeholder="Search & select branch..."
                        />

                    </div>

                    <div className="flex flex-col justify-end">

                        <div className="flex items-center pb-2 ml-1">

                            <input
                                type="checkbox"
                                id="is_active"
                                name="is_active"
                                checked={formData.is_active}
                                onChange={handleChange}
                                className="h-4 w-4 rounded border-border bg-background text-primary focus:ring-primary"
                            />

                            <label
                                htmlFor="is_active"
                                className="ml-2 text-xs font-semibold text-text-primary cursor-pointer"
                            >
                                Enabled
                            </label>

                        </div>

                    </div>

                </div>

                {/* SIM NUMBERS */}

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

                {/* ACTIONS */}

                <div className="flex justify-end gap-2 pt-4">

                    <Button
                        variant="secondary"
                        onClick={onClose}
                        type="button"
                    >
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

import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';
import { branchesAPI } from '../api';

const BranchForm = ({ isOpen, onClose, onSubmit, initialData }) => {

    const [formData, setFormData] = useState({
        spa_name: '',
        code: '',
        state: '',
        city: '',
        area: '',
        postal_code: '',
        address: '',
        is_active: true,
        branch_group: '',
    });

    const [groups, setGroups] = useState([]);

    useEffect(() => {
        const fetchGroups = async () => {
            try {
                const response = await branchesAPI.getGroups({ all: true });
                setGroups(response.data.results || response.data || []);
            } catch (error) {
                console.error("Failed to fetch branch groups", error);
            }
        };
        if (isOpen) {
            fetchGroups();
        }
    }, [isOpen]);

    useEffect(() => {

        if (initialData) {

            setFormData({
                spa_name: initialData.spa_name || '',
                code: initialData.code || '',
                state: initialData.state || '',
                city: initialData.city || '',
                area: initialData.area || '',
                postal_code: initialData.postal_code || '',
                address: initialData.address || '',
                is_active: initialData.is_active !== undefined ? initialData.is_active : true,
                branch_group: initialData.branch_group || '',
            });

        } else {

            setFormData({
                spa_name: '',
                code: '',
                state: '',
                city: '',
                area: '',
                postal_code: '',
                address: '',
                is_active: true,
                branch_group: '',
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
        
        const data = {
            ...formData,
            branch_group: formData.branch_group === '' ? null : formData.branch_group
        };
        
        onSubmit(data);
    };

    return (

        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={initialData ? 'Edit Branch' : 'Create Branch'}
        >

            <form onSubmit={handleSubmit} className="space-y-4">

                <Input
                    label="Spa Name"
                    name="spa_name"
                    value={formData.spa_name}
                    onChange={handleChange}
                    required
                />

                <Input
                    label="Branch Code"
                    name="code"
                    value={formData.code}
                    onChange={handleChange}
                    required
                />

                <div className="grid grid-cols-2 gap-4">

                    <Input
                        label="State"
                        name="state"
                        value={formData.state}
                        onChange={handleChange}
                        required
                    />

                    <Input
                        label="City"
                        name="city"
                        value={formData.city}
                        onChange={handleChange}
                        required
                    />

                </div>

                <div className="grid grid-cols-2 gap-4">

                    <Input
                        label="Area (Optional)"
                        name="area"
                        value={formData.area}
                        onChange={handleChange}
                    />

                    <Input
                        label="Postal Code"
                        name="postal_code"
                        type="number"
                        value={formData.postal_code}
                        onChange={handleChange}
                        required
                    />

                </div>

                {/* ADDRESS */}
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                        Address
                    </label>
                    <textarea
                        name="address"
                        value={formData.address}
                        onChange={handleChange}
                        required
                        rows="3"
                        className="w-full px-3 py-2 bg-background border border-border rounded-md
                                   text-text-primary text-sm
                                   focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                    />
                </div>
                {/* BRANCH GROUP */}
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                        Branch Group
                    </label>
                    <select
                        name="branch_group"
                        value={formData.branch_group}
                        onChange={handleChange}
                        className="w-full px-3 py-2 bg-background border border-border rounded-md
                                   text-text-primary text-sm
                                   focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                    >
                        <option value="">Select Group (Optional)</option>
                        {groups.map(group => (
                            <option key={group.id} value={group.id}>
                                {group.name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* STATUS */}

                <div className="flex items-center">

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
                        className="ml-2 text-sm text-text-primary"
                    >
                        Is Active
                    </label>

                </div>

                {/* ACTION BUTTONS */}

                <div className="flex justify-end gap-2 pt-4">

                    <Button
                        variant="secondary"
                        onClick={onClose}
                        type="button"
                    >
                        Cancel
                    </Button>

                    <Button type="submit">
                        {initialData ? 'Update' : 'Create'}
                    </Button>

                </div>

            </form>

        </Modal>
    );
};

export default BranchForm;
import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

const UserForm = ({ isOpen, onClose, onSubmit, initialData }) => {
    const { user } = useSelector(state => state.auth);
    const [branches, setBranches] = useState([]);

    const [formData, setFormData] = useState({
        email: '',
        first_name: '',
        last_name: '',
        role: 'branch_manager',
        branch: '',
        password: '',
    });

    useEffect(() => {
        const fetchBranches = async () => {
            try {
                const response = await branchesAPI.getBranches({ all: true });
                setBranches(response.data.results || response.data);
            } catch (error) {
                console.error("Failed to fetch branches", error);
            }
        };

        if (isOpen) fetchBranches();
    }, [isOpen]);

    useEffect(() => {
        if (initialData) {
            setFormData({
                email: initialData.email || '',
                first_name: initialData.first_name || '',
                last_name: initialData.last_name || '',
                role: initialData.role || 'branch_manager',
                branch: initialData.branch || '',
                password: '',
            });
        } else {
            setFormData({
                email: '',
                first_name: '',
                last_name: '',
                role: 'branch_manager',
                branch: '',
                password: '',
            });
        }
    }, [initialData, isOpen]);

    const handleChange = (e) => {
        const { name, value } = e.target;

        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        const data = { ...formData };

        if (initialData && !data.password) {
            delete data.password;
        }

        if (data.role !== 'branch_manager') {
            data.branch = null;
        }

        onSubmit(data);
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={initialData ? 'Edit User' : 'Create User'}
        >

            <form
                onSubmit={handleSubmit}
                className="space-y-4 text-text-primary"
            >

                <Input
                    label="Email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="bg-card border-border text-text-primary"
                />

                <div className="grid grid-cols-2 gap-4">

                    <Input
                        label="First Name"
                        name="first_name"
                        value={formData.first_name}
                        onChange={handleChange}
                        required
                        className="bg-card border-border text-text-primary"
                    />

                    <Input
                        label="Last Name"
                        name="last_name"
                        value={formData.last_name}
                        onChange={handleChange}
                        required
                        className="bg-card border-border text-text-primary"
                    />

                </div>

                <div>

                    <label className="block text-sm text-text-secondary mb-1">
                        Role
                    </label>

                    <select
                        name="role"
                        value={formData.role}
                        onChange={handleChange}
                        className="w-full px-3 py-2 bg-card border border-border rounded-md text-text-primary focus:border-primary"
                    >
                        <option value="super_admin">Super Admin</option>
                        <option value="admin">Admin</option>
                        <option value="branch_manager">Branch Manager</option>
                    </select>

                </div>

                {formData.role === 'branch_manager' && (
                    <div>
                        <SearchableSelect
                            label="Assign Branch"
                            options={branches.map(branch => ({
                                value: branch.id,
                                label: `${branch.spa_name}${branch.code ? ` (${branch.code})` : ''} ${branch.city ? `(${branch.city})` : ''}`
                            }))}
                            value={formData.branch}
                            onChange={(value) => setFormData(prev => ({ ...prev, branch: value }))}
                            placeholder="Search & select branch..."
                            className="mt-1"
                        />
                    </div>
                )}

                {(user?.role === 'super_admin' || !initialData) && (
                    <Input
                        label={initialData ? "New Password (leave blank to keep current)" : "Password"}
                        name="password"
                        type="password"
                        value={formData.password}
                        onChange={handleChange}
                        required={!initialData}
                        placeholder={initialData ? "••••••••" : "Create a password"}
                        className="bg-card border-border text-text-primary"
                    />
                )}

                <div className="flex justify-end gap-2 mt-6">

                    <Button
                        variant="outline"
                        onClick={onClose}
                        type="button"
                        className="border-border text-text-secondary hover:bg-cardHover"
                    >
                        Cancel
                    </Button>

                    <Button
                        type="submit"
                        className="bg-primary text-white hover:bg-primary-hover"
                    >
                        {initialData ? 'Update' : 'Create'}
                    </Button>

                </div>

            </form>

        </Modal>
    );
};

export default UserForm;
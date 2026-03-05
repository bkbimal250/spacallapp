import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';
import { branchesAPI } from '../../branches/api';

const UserForm = ({ isOpen, onClose, onSubmit, initialData }) => {
    const [branches, setBranches] = useState([]);
    const [formData, setFormData] = useState({
        email: '',
        first_name: '',
        last_name: '',
        role: 'viewer',
        branch: '',
        assigned_branches: [],
        password: '',
    });

    useEffect(() => {
        const fetchBranches = async () => {
            try {
                const response = await branchesAPI.getBranches({ page_size: 100 });
                setBranches(response.data.results || response.data);
            } catch (error) {
                console.error("Failed to fetch branches", error);
            }
        };
        if (isOpen) {
            fetchBranches();
        }
    }, [isOpen]);

    useEffect(() => {
        if (initialData) {
            setFormData({
                email: initialData.email || '',
                first_name: initialData.first_name || '',
                last_name: initialData.last_name || '',
                role: initialData.role || 'viewer',
                branch: initialData.branch || '',
                assigned_branches: initialData.assigned_branches || [],
                password: '', // Don't show password
            });
        } else {
            setFormData({
                email: '',
                first_name: '',
                last_name: '',
                role: 'viewer',
                branch: '',
                assigned_branches: [],
                password: '',
            });
        }
    }, [initialData, isOpen]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleMultiSelectChange = (e) => {
        const { options } = e.target;
        const selectedValues = [];
        for (let i = 0; i < options.length; i++) {
            if (options[i].selected) {
                selectedValues.push(options[i].value);
            }
        }
        setFormData(prev => ({ ...prev, assigned_branches: selectedValues }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const data = { ...formData };
        if (initialData && !data.password) {
            delete data.password;
        }

        if (data.role === 'branch_manager' || data.role === 'viewer') {
            data.assigned_branches = [];
            if (data.role === 'viewer' && !data.branch) {
                data.branch = null; // Gloal viewer
            }
        } else if (data.role === 'regional_manager') {
            data.branch = null;
        } else {
            // Super Admin or Admin
            data.branch = null;
            data.assigned_branches = [];
        }

        onSubmit(data);
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={initialData ? 'Edit User' : 'Create User'}>
            <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                    label="Email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                />
                <div className="grid grid-cols-2 gap-4">
                    <Input
                        label="First Name"
                        name="first_name"
                        value={formData.first_name}
                        onChange={handleChange}
                        required
                    />
                    <Input
                        label="Last Name"
                        name="last_name"
                        value={formData.last_name}
                        onChange={handleChange}
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                    <select
                        name="role"
                        value={formData.role}
                        onChange={handleChange}
                        className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    >
                        <option value="super_admin">Super Admin</option>
                        <option value="admin">Admin</option>
                        <option value="regional_manager">Regional Manager</option>
                        <option value="branch_manager">Branch Manager</option>
                        <option value="viewer">Viewer</option>
                    </select>
                </div>

                {(formData.role === 'branch_manager' || formData.role === 'viewer') && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Assign Branch {formData.role === 'branch_manager' ? '(Required)' : '(Optional - leave blank for Global)'}
                        </label>
                        <select
                            name="branch"
                            value={formData.branch}
                            onChange={handleChange}
                            required={formData.role === 'branch_manager'}
                            className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        >
                            <option value="">Select Branch</option>
                            {branches.map(branch => (
                                <option key={branch.id} value={branch.id}>
                                    {branch.spa_name} {branch.city ? `(${branch.city})` : ''}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {formData.role === 'regional_manager' && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Assign Branches (Multiple)</label>
                        <select
                            name="assigned_branches"
                            multiple
                            value={formData.assigned_branches}
                            onChange={handleMultiSelectChange}
                            required
                            className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 h-32"
                        >
                            {branches.map(branch => (
                                <option key={branch.id} value={branch.id}>
                                    {branch.spa_name} {branch.city ? `(${branch.city})` : ''}
                                </option>
                            ))}
                        </select>
                        <p className="text-xs text-gray-500 mt-1">Hold Ctrl (Cmd on Mac) to select multiple</p>
                    </div>
                )}

                {!initialData && (
                    <Input
                        label="Password"
                        name="password"
                        type="password"
                        value={formData.password}
                        onChange={handleChange}
                        required
                    />
                )}
                <div className="flex justify-end space-x-2 mt-6">
                    <Button variant="secondary" onClick={onClose} type="button">
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

export default UserForm;


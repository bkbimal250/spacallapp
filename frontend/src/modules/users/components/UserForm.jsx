import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';
import { Search, X } from 'lucide-react';

const BranchMultiSelect = ({ branches, value, onChange }) => {
    const [search, setSearch] = useState('');

    const selectedIds = value || [];
    const selectedBranches = branches.filter(branch => selectedIds.includes(branch.id));
    const filteredBranches = branches.filter(branch => {
        const label = `${branch.spa_name || ''} ${branch.code || ''} ${branch.city || ''}`.toLowerCase();
        return label.includes(search.toLowerCase());
    });

    const toggleBranch = (branchId) => {
        onChange(
            selectedIds.includes(branchId)
                ? selectedIds.filter(id => id !== branchId)
                : [...selectedIds, branchId]
        );
    };

    return (
        <div className="space-y-2">
            <label className="block text-xs font-semibold text-text-secondary mb-1 ml-1 uppercase tracking-wider">
                Assign SPA Branches
            </label>

            <div className="relative">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                    type="search"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search branches..."
                    className="w-full bg-background border border-border rounded-lg py-2.5 pl-9 pr-3 text-sm outline-none focus:border-primary"
                />
            </div>

            {selectedBranches.length > 0 && (
                <div className="flex flex-wrap gap-2">
                    {selectedBranches.map(branch => (
                        <button
                            key={branch.id}
                            type="button"
                            onClick={() => toggleBranch(branch.id)}
                            className="inline-flex items-center gap-1 rounded-full bg-primary/10 text-primary px-2.5 py-1 text-xs font-medium"
                        >
                            {branch.spa_name}
                            <X size={12} />
                        </button>
                    ))}
                </div>
            )}

            <div className="border border-border rounded-lg bg-background max-h-52 overflow-y-auto divide-y divide-border">
                {filteredBranches.length === 0 ? (
                    <div className="py-8 px-4 text-text-muted italic text-center text-sm">
                        No branches found.
                    </div>
                ) : (
                    filteredBranches.map(branch => (
                        <label
                            key={branch.id}
                            className="flex items-start gap-3 px-3 py-2.5 cursor-pointer hover:bg-cardHover"
                        >
                            <input
                                type="checkbox"
                                checked={selectedIds.includes(branch.id)}
                                onChange={() => toggleBranch(branch.id)}
                                className="mt-0.5 h-4 w-4 accent-primary"
                            />
                            <span className="text-sm text-text-primary">
                                {branch.spa_name}
                                <span className="text-text-muted">
                                    {branch.code ? ` (${branch.code})` : ''}{branch.city ? ` - ${branch.city}` : ''}
                                </span>
                            </span>
                        </label>
                    ))
                )}
            </div>

            <p className="text-xs text-text-secondary">
                {selectedBranches.length} branch(es) selected for this Area Manager.
            </p>
        </div>
    );
};

const UserForm = ({ isOpen, onClose, onSubmit, initialData, loading = false }) => {
    const { user } = useSelector(state => state.auth);
    const [branches, setBranches] = useState([]);

    const [formData, setFormData] = useState({
        email: '',
        phone_number: '',
        first_name: '',
        last_name: '',
        role: 'spa_manager',
        branch: '',
        area_branches: [],
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
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setFormData({
                email: initialData.email || '',
                phone_number: initialData.phone_number || '',
                first_name: initialData.first_name || '',
                last_name: initialData.last_name || '',
                role: initialData.role || 'spa_manager',
                branch: initialData.branch || '',
                area_branches: initialData.area_branches || [],
                password: '',
            });
        } else {
            setFormData({
                email: '',
                phone_number: '',
                first_name: '',
                last_name: '',
                role: 'spa_manager',
                branch: '',
                area_branches: [],
                password: '',
            });
        }
    }, [initialData, isOpen]);

    const handleChange = (e) => {
        const { name, value } = e.target;

        setFormData(prev => ({
            ...prev,
            [name]: value,
            ...(name === 'role' && value !== 'spa_manager' ? { branch: '' } : {}),
            ...(name === 'role' && value !== 'area_manager' ? { area_branches: [] } : {}),
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        const data = { ...formData };

        if (initialData && !data.password) {
            delete data.password;
        }

        if (data.role !== 'spa_manager') {
            data.branch = null;
        }
        if (data.role !== 'area_manager') {
            data.area_branches = [];
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

                <Input
                    label="Phone Number"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleChange}
                    placeholder="10 digit mobile number"
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
                        <option value="area_manager">Area Manager</option>
                        <option value="spa_manager">SPA Manager</option>
                    </select>

                </div>

                {formData.role === 'spa_manager' && (
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

                {formData.role === 'area_manager' && (
                    <BranchMultiSelect
                        branches={branches}
                        value={formData.area_branches}
                        onChange={(value) => setFormData(prev => ({ ...prev, area_branches: value }))}
                    />
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
                        className="bg-primary text-white hover:bg-primary-hover min-w-[100px]"
                        loading={loading}
                    >
                        {initialData ? 'Update' : 'Create'}
                    </Button>

                </div>

            </form>

        </Modal>
    );
};

export default UserForm;

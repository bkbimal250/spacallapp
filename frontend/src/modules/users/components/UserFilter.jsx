import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

const UserFilter = ({ onFilter }) => {
    const [search, setSearch] = useState('');
    const [selectedBranch, setSelectedBranch] = useState('');
    const [role, setRole] = useState('');
    const [branches, setBranches] = useState([]);

    useEffect(() => {
        const fetchBranches = async () => {
            try {
                const response = await branchesAPI.getBranches();
                const branchData = response.data.results || response.data;
                setBranches(branchData.map(b => ({
                    value: b.id,
                    label: b.spa_name
                })));
            } catch (error) {
                console.error("Failed to fetch branches for filter", error);
            }
        };
        fetchBranches();
    }, []);

    const handleFilter = () => {
        const filters = {};
        if (search) filters.search = search;
        if (selectedBranch) filters.branch = selectedBranch;
        if (role) filters.role = role;
        onFilter(filters);
    };

    const handleClear = () => {
        setSearch('');
        setSelectedBranch('');
        setRole('');
        onFilter({});
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Search name/email</label>
                <Input
                    placeholder="Search users..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            <div>
                <SearchableSelect
                    label="Branch"
                    placeholder="All Branches"
                    options={branches}
                    value={selectedBranch}
                    onChange={setSelectedBranch}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                >
                    <option value="">All Roles</option>
                    <option value="super_admin">Super Admin</option>
                    <option value="admin">Admin</option>
                    <option value="branch_manager">Branch Manager</option>
                </select>
            </div>

            <div className="flex space-x-2">
                <Button variant="secondary" onClick={handleClear} className="w-1/2">Clear</Button>
                <Button onClick={handleFilter} className="w-1/2">Filter</Button>
            </div>
        </div>
    );
};

export default UserFilter;

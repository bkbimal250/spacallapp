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
                const response = await branchesAPI.getBranches({ all: true });
                const branchData = response.data.results || response.data;

                setBranches(
                    branchData.map(b => ({
                        value: b.id,
                        label: b.code ? `${b.spa_name} (${b.code})` : b.spa_name,
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
                    }))
                );

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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end text-text-primary">

            <div>
                <label className="block text-sm text-text-secondary mb-1">
                    Search name/email
                </label>

                <Input
                    placeholder="Search users..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="bg-card border-border text-text-primary"
                />
            </div>

            <div>
                <SearchableSelect
                    label="Branch"
                    placeholder="All Branches"
                    options={branches}
                    value={selectedBranch}
                    onChange={setSelectedBranch}
                    className="bg-card border-border"
                />
            </div>

            <div>

                <label className="block text-sm text-text-secondary mb-1">
                    Role
                </label>

                <select
                    className="block w-full px-3 py-2 bg-card border border-border rounded-md text-text-primary focus:border-primary"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                >
                    <option value="">All Roles</option>
                    <option value="super_admin">Super Admin</option>
                    <option value="admin">Admin</option>
                    <option value="area_manager">Area Manager</option>
                    <option value="spa_manager">SPA Manager</option>
                </select>

            </div>

            <div className="flex gap-2">

                <Button
                    variant="outline"
                    onClick={handleClear}
                    className="w-1/2 border-border text-text-secondary hover:bg-cardHover"
                >
                    Clear
                </Button>

                <Button
                    onClick={handleFilter}
                    className="w-1/2 bg-primary hover:bg-primary-hover text-white"
                >
                    Filter
                </Button>

            </div>

        </div>
    );
};

export default UserFilter;

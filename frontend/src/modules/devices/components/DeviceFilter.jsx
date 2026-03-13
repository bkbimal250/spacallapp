import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

const DeviceFilter = ({ onFilter }) => {

    const [search, setSearch] = useState('');
    const [selectedBranch, setSelectedBranch] = useState('');
    const [registrationStatus, setRegistrationStatus] = useState('');
    const [branches, setBranches] = useState([]);

    useEffect(() => {

        const fetchBranches = async () => {

            try {

                const response = await branchesAPI.getBranches();
                const branchData = response.data.results || response.data;

                setBranches(
                    branchData.map(b => ({
                        value: b.id,
                        label: b.spa_name
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
        if (registrationStatus !== '') filters.is_registered = registrationStatus;

        onFilter(filters);

    };

    const handleClear = () => {

        setSearch('');
        setSelectedBranch('');
        setRegistrationStatus('');

        onFilter({});

    };

    return (

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">

            {/* SEARCH */}

            <div>

                <label className="block text-sm font-medium text-text-secondary mb-1">
                    Search ID / Token
                </label>

                <Input
                    placeholder="e.g. SPA-..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />

            </div>

            {/* BRANCH SELECT */}

            <div>

                <SearchableSelect
                    label="Branch"
                    placeholder="All Branches"
                    options={branches}
                    value={selectedBranch}
                    onChange={setSelectedBranch}
                />

            </div>

            {/* REGISTRATION STATUS */}

            <div>

                <label className="block text-sm font-medium text-text-secondary mb-1">
                    Reg. Status
                </label>

                <select
                    className="block w-full px-3 py-2 bg-background border border-border rounded-md
                               text-text-primary text-sm
                               focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                    value={registrationStatus}
                    onChange={(e) => setRegistrationStatus(e.target.value)}
                >

                    <option value="">All</option>
                    <option value="true">Registered</option>
                    <option value="false">Pending</option>

                </select>

            </div>

            {/* BUTTONS */}

            <div className="flex gap-2">

                <Button
                    variant="secondary"
                    onClick={handleClear}
                    className="w-1/2"
                >
                    Clear
                </Button>

                <Button
                    onClick={handleFilter}
                    className="w-1/2"
                >
                    Filter
                </Button>

            </div>

        </div>

    );
};

export default DeviceFilter;
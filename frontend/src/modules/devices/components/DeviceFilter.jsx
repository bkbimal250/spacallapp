import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

const DeviceFilter = ({ onFilter }) => {

    const [search, setSearch] = useState('');
    const [selectedBranch, setSelectedBranch] = useState('');
    const [city, setCity] = useState('');
    const [state, setState] = useState('');
    const [registrationStatus, setRegistrationStatus] = useState('');
    const [branches, setBranches] = useState([]);

    useEffect(() => {

        const fetchBranches = async () => {

            try {

                const response = await branchesAPI.getBranches({ all: true });
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
        if (city) filters.city = city;
        if (state) filters.state = state;
        if (registrationStatus !== '') filters.is_registered = registrationStatus;

        onFilter(filters);

    };

    const handleClear = () => {

        setSearch('');
        setSelectedBranch('');
        setCity('');
        setState('');
        setRegistrationStatus('');

        onFilter({});

    };

    return (

        <div className="space-y-6">

            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 items-end">

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

                {/* STATE */}
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                        State
                    </label>
                    <Input
                        placeholder="Branch state..."
                        value={state}
                        onChange={(e) => setState(e.target.value)}
                    />
                </div>

                {/* CITY */}
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                        City
                    </label>
                    <Input
                        placeholder="Branch city..."
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
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

            </div>

            {/* BUTTONS */}

            <div className="flex justify-end gap-3 pt-4 border-t border-border/50">

                <Button
                    variant="secondary"
                    onClick={handleClear}
                    className="w-full md:w-32"
                >
                    Clear
                </Button>

                <Button
                    onClick={handleFilter}
                    className="w-full md:w-32"
                >
                    Apply Filter
                </Button>

            </div>

        </div>

    );
};

export default DeviceFilter;
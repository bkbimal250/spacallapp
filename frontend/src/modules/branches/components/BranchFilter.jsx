import React, { useState, memo, useMemo, useCallback, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../api';

const BranchFilter = ({ onFilter, externalFilters = {} }) => {

    const [search, setSearch] = useState('');
    const [city, setCity] = useState('');
    const [state, setState] = useState('');
    const [area, setArea] = useState('');
    const [status, setStatus] = useState('');
    const [group, setGroup] = useState('');
    const [groups, setGroups] = useState([]);

    const groupOptions = useMemo(() =>
        groups.map(g => ({ value: g.id, label: g.name })),
        [groups]
    );

    useEffect(() => {
        const fetchGroups = async () => {
            try {
                const response = await branchesAPI.getGroups({ all: true });
                setGroups(response.data.results || response.data || []);
            } catch (error) {
                console.error("Failed to fetch groups", error);
            }
        };
        fetchGroups();
    }, []);

    // Sync external filters (like from BranchGroupFilter)
    useEffect(() => {
        if (externalFilters.group !== undefined) {
            setGroup(externalFilters.group);
        }
    }, [externalFilters.group]);

    const handleGroupChange = useCallback((e) => setGroup(e.target.value), []);

    const handleSearchChange = useCallback((e) => setSearch(e.target.value), []);
    const handleCityChange = useCallback((e) => setCity(e.target.value), []);
    const handleStateChange = useCallback((e) => setState(e.target.value), []);
    const handleAreaChange = useCallback((e) => setArea(e.target.value), []);
    const handleStatusChange = useCallback((e) => setStatus(e.target.value), []);

    const handleFilter = useCallback(() => {

        const filters = {};

        if (search) filters.search = search;
        if (city) filters.city = city;
        if (state) filters.state = state;
        if (area) filters.area = area;
        if (status !== '') filters.status = status;
        if (group) filters.group = group;

        onFilter(filters);
    }, [search, city, state, area, status, group, onFilter]);

    const handleClear = useCallback(() => {

        setSearch('');
        setCity('');
        setState('');
        setArea('');
        setStatus('');
        setGroup('');

        onFilter({});
    }, [onFilter]);

    return (

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">

            {/* SEARCH */}

            <div>

                <label className="block text-sm font-medium text-text-secondary mb-1">
                    Master Search
                </label>

                <Input
                    placeholder="Search branch, city, area, spa code..."
                    value={search}
                    onChange={handleSearchChange}
                />

            </div>


            {/* States */}

            <div>

                <label className="block text-sm font-medium text-text-secondary mb-1">
                    States
                </label>

                <Input
                    placeholder="Filter by state..."
                    value={state}
                    onChange={handleStateChange}
                />

            </div>

            {/* CITY */}

            <div>

                <label className="block text-sm font-medium text-text-secondary mb-1">
                    City
                </label>

                <Input
                    placeholder="Filter by city..."
                    value={city}
                    onChange={handleCityChange}
                />

            </div>

            <div>

                <label className="block text-sm font-medium text-text-secondary mb-1">
                    Area
                </label>

                <Input
                    placeholder="Filter by area..."
                    value={area}
                    onChange={handleAreaChange}
                />

            </div>

            <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                    Status
                </label>
                <select
                    className="block w-full px-3 py-2 bg-background border border-border rounded-md
                               text-text-primary text-sm
                               focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                    value={status}
                    onChange={handleStatusChange}
                >
                    <option value="">All Statuses</option>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                </select>
            </div>

            {/* GROUP */}

            <div>
                <SearchableSelect
                    label="Branch Group"
                    options={groupOptions}
                    value={group}
                    onChange={(val) => setGroup(val)}
                    placeholder="All Groups"
                />
            </div>

            {/* ACTION BUTTONS */}

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
                    Apply Filter
                </Button>

            </div>

        </div>

    );
};

export default memo(BranchFilter);

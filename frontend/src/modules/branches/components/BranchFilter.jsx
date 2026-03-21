import React, { useState } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';

const BranchFilter = ({ onFilter }) => {

    const [search, setSearch] = useState('');
    const [city, setCity] = useState('');
    const [state, setState] = useState('');
    const [status, setStatus] = useState('');

    const handleFilter = () => {

        const filters = {};

        if (search) filters.search = search;
        if (city) filters.city = city;
        if (state) filters.state = state;
        if (status !== '') filters.status = status;

        onFilter(filters);
    };

    const handleClear = () => {

        setSearch('');
        setCity('');
        setState('');
        setStatus('');

        onFilter({});
    };

    return (

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">

            {/* SEARCH */}

            <div>

                <label className="block text-sm font-medium text-text-secondary mb-1">
                    Search name/code
                </label>

                <Input
                    placeholder="Search branches..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
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
                    onChange={(e) => setState(e.target.value)}
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
                    onChange={(e) => setCity(e.target.value)}
                />

            </div>

            {/* STATUS */}

            <div>

                <label className="block text-sm font-medium text-text-secondary mb-1">
                    Status
                </label>

                <select
                    className="block w-full px-3 py-2 bg-background border border-border rounded-md
                               text-text-primary text-sm
                               focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                >

                    <option value="">All Statuses</option>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>

                </select>

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

export default BranchFilter;
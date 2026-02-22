import React, { useState } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';

const BranchFilter = ({ onFilter }) => {
    const [search, setSearch] = useState('');
    const [city, setCity] = useState('');
    const [status, setStatus] = useState('');

    const handleFilter = () => {
        const filters = {};
        if (search) filters.search = search;
        if (city) filters.city = city;
        if (status !== '') filters.status = status;
        onFilter(filters);
    };

    const handleClear = () => {
        setSearch('');
        setCity('');
        setStatus('');
        onFilter({});
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Search name/code</label>
                <Input
                    placeholder="Search branches..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                <Input
                    placeholder="Filter by city..."
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm"
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                >
                    <option value="">All Statuses</option>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                </select>
            </div>

            <div className="flex space-x-2">
                <Button variant="secondary" onClick={handleClear} className="w-1/2">Clear</Button>
                <Button onClick={handleFilter} className="w-1/2">Filter</Button>
            </div>
        </div>
    );
};

export default BranchFilter;

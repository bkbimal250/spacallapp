import React, { useState } from 'react';
import Button from '../../../shared/components/Button';

const ContactFilter = ({ onFilter }) => {
    const [search, setSearch] = useState('');

    const handleApply = () => {
        const filters = {};
        if (search.trim()) filters.search = search.trim();
        onFilter(filters);
    };

    const handleClear = () => {
        setSearch('');
        onFilter({});
    };

    return (
        <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="w-full md:w-1/3">
                <label className="block text-sm font-medium text-gray-700 mb-1">Search Contacts</label>
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by name, phone, or email..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') handleApply();
                    }}
                />
            </div>

            <div className="flex space-x-2 w-full md:w-auto">
                <Button onClick={handleApply} className="flex-1 md:flex-none">
                    Filter
                </Button>
                <Button onClick={handleClear} variant="outline" className="flex-1 md:flex-none">
                    Clear
                </Button>
            </div>
        </div>
    );
};

export default ContactFilter;

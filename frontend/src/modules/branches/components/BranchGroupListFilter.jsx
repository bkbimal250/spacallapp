import React, { useState, useEffect, useCallback, memo } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { useDebounce } from '../../../shared/hooks/useDebounce';

const statusOptions = [
    { value: 'true', label: 'Active Only' },
    { value: 'false', label: 'Inactive Only' },
];

const BranchGroupListFilter = ({ onFilter }) => {
    const [search, setSearch] = useState('');
    const [status, setStatus] = useState('');
    
    const debouncedSearch = useDebounce(search, 500);

    // Auto-filter when debounced search or status changes
    useEffect(() => {
        const filters = {};
        if (debouncedSearch) filters.search = debouncedSearch;
        if (status) filters.status = status;
        onFilter(filters);
    }, [debouncedSearch, status, onFilter]);

    const handleClear = useCallback(() => {
        setSearch('');
        setStatus('');
        onFilter({});
    }, [onFilter]);

    return (
        <div className="bg-card border border-border p-5 rounded-2xl shadow-sm mb-6 transition-all duration-300 hover:shadow-md">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
                <div className="md:col-span-6">
                    <label className="block text-xs font-semibold text-text-secondary mb-1.5 ml-1 uppercase tracking-wider">
                        Search Groups
                    </label>
                    <Input
                        placeholder="Search by name, description..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="!py-2.5 bg-background/50 border-border/50 focus:bg-background"
                    />
                </div>

                <div className="md:col-span-4">
                    <SearchableSelect
                        label="Status"
                        options={statusOptions}
                        value={status}
                        onChange={setStatus}
                        placeholder="All Statuses"
                        isClearable
                    />
                </div>

                <div className="md:col-span-2">
                    <Button
                        variant="secondary"
                        onClick={handleClear}
                        className="w-full py-2.5 border-dashed border-2 hover:bg-danger/5 hover:text-danger hover:border-danger/30 transition-all"
                    >
                        Reset
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default memo(BranchGroupListFilter);

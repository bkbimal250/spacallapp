import React, { useState, useEffect, memo, useCallback } from 'react';
import { Search } from 'lucide-react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';

const LeadFilter = ({ 
    filters: initialFilters, 
    onFilter, 
    isAdmin, 
    branches 
}) => {
    const [localFilters, setLocalFilters] = useState(initialFilters);

    // Update local state when initialFilters change (e.g. from URL)
    useEffect(() => {
        setLocalFilters(initialFilters);
    }, [initialFilters]);

    const handleChange = useCallback((field, value) => {
        setLocalFilters(prev => ({ ...prev, [field]: value }));
    }, []);

    // Effect for auto-applying search with debounce
    useEffect(() => {
        const timer = setTimeout(() => {
            if (localFilters.search !== initialFilters.search) {
                onFilter(localFilters);
            }
        }, 600); 

        return () => clearTimeout(timer);
    }, [localFilters.search, initialFilters.search, onFilter, localFilters]);

    const handleApply = useCallback(() => {
        onFilter(localFilters);
    }, [localFilters, onFilter]);

    const handleClear = useCallback(() => {
        const cleared = { branch: '', status: '', search: '' };
        setLocalFilters(cleared);
        onFilter(cleared);
    }, [onFilter]);

    return (
        <div className="flex flex-col mb-6 p-5 bg-background rounded-xl border border-border">
            <div className="flex items-center gap-2 mb-6">
                <Search size={18} className="text-primary" />
                <h2 className="text-lg font-semibold text-text-primary">
                    Search & Filter
                </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
                <div className="space-y-2">
                    <label className="text-xs font-semibold text-text-secondary uppercase">
                        Search Contact
                    </label>
                    <Input
                        placeholder="Name or number..."
                        className="!bg-card h-11 border-border text-text-primary focus:border-primary rounded-lg"
                        value={localFilters.search}
                        onChange={(e) => handleChange('search', e.target.value)}
                    />
                </div>

                {isAdmin && (
                    <div className="space-y-2">
                        <label className="text-xs font-semibold text-text-secondary uppercase">
                            Branch
                        </label>
                        <SearchableSelect
                            placeholder="Search branch, city, area, spa code..."
                            options={branches}
                            value={localFilters.branch}
                            onChange={(val) => handleChange('branch', val)}
                            className="!bg-card border-border"
                        />
                    </div>
                )}

                <div className="space-y-2">
                    <label className="text-xs font-semibold text-text-secondary uppercase">
                        Lead Status
                    </label>

                    <select
                        className="block w-full px-3 py-2 bg-card border border-border rounded-lg text-sm text-text-primary focus:border-primary outline-none h-11"
                        value={localFilters.status}
                        onChange={(e) => handleChange('status', e.target.value)}
                    >
                        <option value="">All Statuses</option>
                        <option value="pending">Pending</option>
                        <option value="ringing">Ringing</option>
                        <option value="coming">Coming</option>
                        <option value="interested">Interested</option>
                        <option value="not_interested">Not Interested</option>
                    </select>
                </div>

                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={handleClear}
                        className="flex-1 h-11 rounded-lg border-border text-text-secondary hover:bg-cardHover"
                    >
                        Clear
                    </Button>
                    <Button
                        onClick={handleApply}
                        className="flex-1 h-11 rounded-lg bg-primary text-white hover:bg-primary-hover shadow-md"
                    >
                        Apply
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default memo(LeadFilter);

import React, { useState } from 'react';
import Button from '../../../shared/components/Button';
import BranchSearchSelect from './BranchSearchSelect';

const WebsiteFormFilters = ({ onFilter }) => {
    const [filters, setFilters] = useState({});

    const update = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));

    return (
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            <BranchSearchSelect
                value={filters.branch || ''}
                onChange={(value) => update('branch', value)}
                allPlaceholder="All branches"
                placeholder="Search branch, area, or city"
            />
            <input className="rounded-lg border border-border bg-background px-3 py-2 text-sm" placeholder="Website search" value={filters.search || ''} onChange={(e) => update('search', e.target.value)} />
            <input className="rounded-lg border border-border bg-background px-3 py-2 text-sm" placeholder="Form key" value={filters.form_key || ''} onChange={(e) => update('form_key', e.target.value)} />
            <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.is_active ?? ''} onChange={(e) => update('is_active', e.target.value)}>
                <option value="">All status</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
            </select>
            <input type="date" className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.start_date || ''} onChange={(e) => update('start_date', e.target.value)} />
            <div className="flex gap-2">
                <input type="date" className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.end_date || ''} onChange={(e) => update('end_date', e.target.value)} />
                <Button type="button" onClick={() => onFilter(filters)}>Apply</Button>
            </div>
        </div>
    );
};

export default WebsiteFormFilters;

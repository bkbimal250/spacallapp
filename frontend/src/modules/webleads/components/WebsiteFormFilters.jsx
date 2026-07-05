import React, { useEffect, useState } from 'react';
import Button from '../../../shared/components/Button';
import { branchesAPI } from '../../branches/api';

const WebsiteFormFilters = ({ onFilter }) => {
    const [branches, setBranches] = useState([]);
    const [filters, setFilters] = useState({});

    useEffect(() => {
        branchesAPI.getBranches({ page_size: 500 }).then((res) => setBranches(res.data.results || res.data || [])).catch(() => setBranches([]));
    }, []);

    const update = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));

    return (
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.branch || ''} onChange={(e) => update('branch', e.target.value)}>
                <option value="">All branches</option>
                {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.spa_name || branch.name}</option>)}
            </select>
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

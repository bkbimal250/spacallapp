import React, { useEffect, useState } from 'react';
import Button from '../../../shared/components/Button';
import BranchSearchSelect from './BranchSearchSelect';

const EMPTY_FILTERS = {};

const WebsiteLeadFilters = ({ onFilter, pendingOnly = false, initialFilters = EMPTY_FILTERS }) => {
    const [filters, setFilters] = useState(initialFilters);

    useEffect(() => {
        setFilters(initialFilters);
    }, [initialFilters]);

    const update = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));

    return (
        <div className="space-y-3">
            <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
                <BranchSearchSelect
                    value={filters.branch || ''}
                    onChange={(value) => update('branch', value)}
                    allPlaceholder="All branches"
                    placeholder="Search branch, area, or city"
                />
                <input className="rounded-lg border border-border bg-background px-3 py-2 text-sm" placeholder="Name, phone, address" value={filters.search || ''} onChange={(e) => update('search', e.target.value)} />
                <input className="rounded-lg border border-border bg-background px-3 py-2 text-sm" placeholder="Website name" value={filters.website_name || ''} onChange={(e) => update('website_name', e.target.value)} />
                <input className="rounded-lg border border-border bg-background px-3 py-2 text-sm" placeholder="Website URL" value={filters.website_url || ''} onChange={(e) => update('website_url', e.target.value)} />
                <input className="rounded-lg border border-border bg-background px-3 py-2 text-sm" placeholder="Form key" value={filters.form_key || ''} onChange={(e) => update('form_key', e.target.value)} />
                {!pendingOnly && (
                    <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.status || ''} onChange={(e) => update('status', e.target.value)}>
                        <option value="">All lead status</option>
                        {['new', 'contacted', 'converted', 'rejected', 'duplicate'].map((status) => <option key={status} value={status}>{status}</option>)}
                    </select>
                )}
            </div>
            <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
                <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.routing_status || ''} onChange={(e) => update('routing_status', e.target.value)}>
                    <option value="">Routing status</option>
                    {['routed', 'pending_configuration', 'unassigned'].map((status) => <option key={status} value={status}>{status}</option>)}
                </select>
                <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.notification_status || ''} onChange={(e) => update('notification_status', e.target.value)}>
                    <option value="">Notifications</option>
                    {['pending', 'sent', 'failed', 'not_required'].map((status) => <option key={status} value={status}>{status}</option>)}
                </select>
                <input type="date" className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.start_date || ''} onChange={(e) => update('start_date', e.target.value)} />
                <input type="date" className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.end_date || ''} onChange={(e) => update('end_date', e.target.value)} />
                <Button type="button" onClick={() => onFilter(filters)}>Apply Filters</Button>
            </div>
        </div>
    );
};

export default WebsiteLeadFilters;

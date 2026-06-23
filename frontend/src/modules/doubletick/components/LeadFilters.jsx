import React, { useEffect, useState } from 'react';
import { Calendar, Filter, RotateCcw, Search } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';

const LeadFilters = ({ filters, onChange, onReset, onRefresh }) => {
    const [search, setSearch] = useState(filters.search || '');
    const update = (key, value) => onChange({ ...filters, [key]: value });

    useEffect(() => {
        const timer = setTimeout(() => {
            if (search !== (filters.search || '')) update('search', search);
        }, 350);
        return () => clearTimeout(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [search]);

    return (
        <div className="space-y-3 rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                <Filter size={16} className="text-primary" /> Lead Filters
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
                <Input placeholder="Search name, phone, message..." value={search} onChange={(event) => setSearch(event.target.value)} />
                <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.status} onChange={(event) => update('status', event.target.value)}>
                    <option value="">All statuses</option><option value="unassigned">Unassigned</option><option value="qualified">Qualified</option>
                    <option value="available">Available</option><option value="claimed">Claimed</option><option value="contacting">Contacting</option>
                    <option value="follow_up">Follow up</option><option value="booked">Booked</option><option value="lost">Lost</option><option value="closed">Closed</option>
                </select>
                <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.classification} onChange={(event) => update('classification', event.target.value)}>
                    <option value="">All classifications</option><option value="area">Area</option><option value="branch">Branch</option>
                    <option value="city">City</option><option value="location_group">Group</option><option value="greeting">Greeting</option>
                    <option value="job_inquiry">Job inquiry</option><option value="service_action">Service/action</option><option value="unknown">Unknown</option>
                </select>
                <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.match_method} onChange={(event) => update('match_method', event.target.value)}>
                    <option value="">All match methods</option><option value="exact">Exact</option><option value="fuzzy">RapidFuzz</option><option value="manual">Manual</option><option value="none">None</option>
                </select>
                <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.android_visible} onChange={(event) => update('android_visible', event.target.value)}>
                    <option value="">Android visibility</option><option value="true">Visible on Android</option><option value="false">Not visible</option>
                </select>
                <Input placeholder="City" value={filters.city} onChange={(event) => update('city', event.target.value)} />
                <Input placeholder="Group" value={filters.group} onChange={(event) => update('group', event.target.value)} />
                <Input placeholder="Area" value={filters.area} onChange={(event) => update('area', event.target.value)} />
                <Input placeholder="Branch / Spa" value={filters.spa} onChange={(event) => update('spa', event.target.value)} />
                <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm" value={filters.pending_reason} onChange={(event) => update('pending_reason', event.target.value)}>
                    <option value="">All pending reasons</option><option value="greeting_only">Greeting</option><option value="missing_location">Missing location</option>
                    <option value="unmatched_location">Unmatched location</option><option value="manual_reply_required">Manual reply</option>
                </select>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-[1fr_1fr_auto]">
                {['created_from', 'created_to'].map((key) => (
                    <label className="relative" key={key}>
                        <Calendar size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
                        <input type="date" className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-sm"
                            value={filters[key]} onChange={(event) => update(key, event.target.value)} />
                    </label>
                ))}
                <div className="flex gap-2">
                    <Button variant="secondary" className="flex-1 gap-2" onClick={onRefresh}><Search size={16} /> Refresh</Button>
                    <Button variant="ghost" onClick={() => { setSearch(''); onReset(); }} title="Reset filters"><RotateCcw size={16} /></Button>
                </div>
            </div>
        </div>
    );
};

export default LeadFilters;

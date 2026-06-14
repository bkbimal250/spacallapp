import React from 'react';
import { Search, RotateCcw } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';

const LeadFilters = ({ filters, onChange, onReset, onRefresh }) => {
    const update = (key, value) => onChange({ ...filters, [key]: value });

    return (
        <div className="bg-card border border-border rounded-lg p-4 grid grid-cols-1 md:grid-cols-5 gap-3">
            <Input placeholder="Search leads" value={filters.search || ''} onChange={(event) => update('search', event.target.value)} />
            <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.status || ''} onChange={(event) => update('status', event.target.value)}>
                <option value="">All Status</option>
                <option value="qualified">Qualified</option>
                <option value="available">Available</option>
                <option value="claimed">Claimed</option>
                <option value="contacting">Contacting</option>
                <option value="contacted">Contacted</option>
                <option value="follow_up">Follow Up</option>
                <option value="booked">Booked</option>
                <option value="lost">Lost</option>
                <option value="closed">Closed</option>
            </select>
            <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.available || ''} onChange={(event) => update('available', event.target.value)}>
                <option value="">Availability</option>
                <option value="true">Available</option>
                <option value="false">Not Available</option>
            </select>
            <Input placeholder="Matched area id" value={filters.matched_area || ''} onChange={(event) => update('matched_area', event.target.value)} />
            <div className="flex gap-2">
                <Button type="button" variant="secondary" className="gap-2 flex-1" onClick={onRefresh}>
                    <Search size={16} />
                    Apply
                </Button>
                <Button type="button" variant="ghost" onClick={onReset} title="Reset filters">
                    <RotateCcw size={16} />
                </Button>
            </div>
        </div>
    );
};

export default LeadFilters;

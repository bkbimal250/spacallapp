import React from 'react';
import { Search, RotateCcw } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';

const ConversationFilters = ({ filters, onChange, onReset, onRefresh }) => {
    const update = (key, value) => onChange({ ...filters, [key]: value });

    return (
        <div className="bg-card border border-border rounded-lg p-4 grid grid-cols-1 md:grid-cols-5 gap-3">
            <Input
                placeholder="Search conversations"
                value={filters.search || ''}
                onChange={(event) => update('search', event.target.value)}
            />
            <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.status || ''} onChange={(event) => update('status', event.target.value)}>
                <option value="">All Status</option>
                <option value="awaiting_location">Awaiting Location</option>
                <option value="awaiting_customer">Awaiting Customer</option>
                <option value="manual_attention">Manual Attention</option>
                <option value="area_unmatched">Unmatched Area</option>
                <option value="qualified">Qualified</option>
                <option value="distributed">Distributed</option>
                <option value="closed">Closed</option>
            </select>
            <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.pending_reason || ''} onChange={(event) => update('pending_reason', event.target.value)}>
                <option value="">All Reasons</option>
                <option value="greeting_only">Greeting Only</option>
                <option value="missing_location">Missing Location</option>
                <option value="unmatched_location">Unmatched Location</option>
                <option value="customer_stopped_replying">Stopped Replying</option>
            </select>
            <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.requires_manual_attention || ''} onChange={(event) => update('requires_manual_attention', event.target.value)}>
                <option value="">All Queues</option>
                <option value="true">Manual Attention</option>
                <option value="false">No Manual Flag</option>
            </select>
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

export default ConversationFilters;

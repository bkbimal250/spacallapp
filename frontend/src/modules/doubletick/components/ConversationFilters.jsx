import React from 'react';
import { Calendar, Filter, RotateCcw, Search } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';

const ConversationFilters = ({ filters, onChange, onReset, onRefresh }) => {
    const update = (key, value) => onChange({ ...filters, [key]: value });

    return (
        <div className="bg-card border border-border rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                <Filter size={16} className="text-primary" />
                Pending Queue Filters
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-6 gap-3">
                <Input
                    placeholder="Phone, message, name..."
                    value={filters.search || ''}
                    onChange={(event) => update('search', event.target.value)}
                />
                <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.status || ''} onChange={(event) => update('status', event.target.value)}>
                    <option value="">All Status</option>
                    <option value="awaiting_location">⏳ Awaiting Location</option>
                    <option value="awaiting_customer">⏳ Awaiting Customer</option>
                    <option value="manual_attention">⚠️ Manual Attention</option>
                    <option value="area_unmatched">🚫 Unmatched Area</option>
                    <option value="qualified">✓ Qualified</option>
                    <option value="distributed">📤 Distributed</option>
                    <option value="closed">🔒 Closed</option>
                </select>
                <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.pending_reason || ''} onChange={(event) => update('pending_reason', event.target.value)}>
                    <option value="">All Reasons</option>
                    <option value="greeting_only">👋 Greeting Only</option>
                    <option value="missing_location">📍 Missing Location</option>
                    <option value="unmatched_location">📍 Unmatched Location</option>
                    <option value="customer_stopped_replying">⏸️ Stopped Replying</option>
                    <option value="manual_reply_required">💬 Manual Reply</option>
                </select>
                <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.requires_manual_attention || ''} onChange={(event) => update('requires_manual_attention', event.target.value)}>
                    <option value="">All Queues</option>
                    <option value="true">🚩 Manual Attention</option>
                    <option value="false">✓ No Manual Flag</option>
                </select>
                <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.has_unread_messages || ''} onChange={(event) => update('has_unread_messages', event.target.value)}>
                    <option value="">Unread Status</option>
                    <option value="true">📬 Has Unread</option>
                    <option value="false">📭 No Unread</option>
                </select>
                <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm" value={filters.is_unmatched || ''} onChange={(event) => update('is_unmatched', event.target.value)}>
                    <option value="">Matched State</option>
                    <option value="true">🚫 Unmatched Only</option>
                    <option value="false">✓ Matched</option>
                </select>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1fr_1fr_auto] gap-3">
                <Input placeholder="Phone number" value={filters.phone_number || ''} onChange={(event) => update('phone_number', event.target.value)} />
                <Input placeholder="WABA number" value={filters.waba_number || ''} onChange={(event) => update('waba_number', event.target.value)} />
                <label className="relative">
                    <Calendar size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
                    <input
                        type="date"
                        className="w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-background text-sm"
                        value={filters.created_from || ''}
                        onChange={(event) => update('created_from', event.target.value)}
                    />
                </label>
                <label className="relative">
                    <Calendar size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
                    <input
                        type="date"
                        className="w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-background text-sm"
                        value={filters.created_to || ''}
                        onChange={(event) => update('created_to', event.target.value)}
                    />
                </label>
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
        </div>
    );
};

export default ConversationFilters;

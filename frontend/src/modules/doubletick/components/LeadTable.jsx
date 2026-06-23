import React, { useMemo, useState } from 'react';
import { ArrowUpRight, MapPin, MessageSquareText, Send, Smartphone, Sparkles } from 'lucide-react';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import { doubletickAPI } from '../api';
import { customerName, customerPhone, leadArea, leadBranch, leadMessage, leadOwner, leadTime } from '../display';
import DoubleTickStatusBadge from './DoubleTickStatusBadge';
import MatchConfidenceBadge from './MatchConfidenceBadge';

const TextLine = ({ label, value }) => (
    <p className="text-xs text-text-secondary"><span className="font-medium text-text-primary">{label}:</span> {value || '-'}</p>
);

const LeadTable = ({ leads, onOpen, onCorrect, onChanged }) => {
    const [working, setWorking] = useState('');

    const act = async (event, key, action) => {
        event.stopPropagation();
        setWorking(key);
        try {
            await action();
            await onChanged?.();
        } catch (error) {
            alert(error.response?.data?.detail || error.message || 'Action failed.');
        } finally {
            setWorking('');
        }
    };

    const applySuggestion = (row) => {
        const item = row.suggested_match;
        if (!item || !row.conversation) return Promise.resolve();
        if (item.type === 'area') return doubletickAPI.manualCorrect(row.conversation, { action: 'correct_area', area_id: item.id, alias_text: leadMessage(row), save_alias: true });
        if (item.type === 'branch') return doubletickAPI.manualCorrect(row.conversation, { action: 'correct_branch', branch_id: item.id });
        if (item.type === 'city') return doubletickAPI.manualCorrect(row.conversation, { action: 'correct_city', city_name: item.name });
        if (item.type === 'location_group') return doubletickAPI.manualCorrect(row.conversation, { action: 'correct_group', group_name: item.name });
        return doubletickAPI.matchArea(row.conversation, { lead_area_id: item.id, raw_alias: leadMessage(row), save_alias: true, qualify_as_lead: false });
    };

    const columns = useMemo(() => [
        {
            header: 'Customer',
            render: (row) => (
                <div className="min-w-[220px]">
                    <p className="font-semibold text-text-primary">{customerName(row)}</p>
                    <p className="text-xs text-text-secondary">{customerPhone(row)}</p>
                    <p className="mt-2 line-clamp-2 text-xs text-text-secondary"><MessageSquareText size={12} className="mr-1 inline" />{leadMessage(row)}</p>
                </div>
            ),
        },
        {
            header: 'Match',
            render: (row) => (
                <div className="min-w-[180px] space-y-2">
                    <div className="flex flex-wrap gap-1">
                        <span className="rounded bg-info/10 px-2 py-1 text-xs font-semibold text-info">{row.classification || 'unknown'}</span>
                        <span className="rounded bg-card px-2 py-1 text-xs text-text-secondary">{row.match_method || 'none'}</span>
                    </div>
                    <MatchConfidenceBadge confidence={row.match_confidence} />
                    {row.match_reason && <p className="line-clamp-2 text-xs text-text-secondary">{row.match_reason}</p>}
                </div>
            ),
        },
        {
            header: 'Raw Location',
            render: (row) => (
                <div className="min-w-[180px] space-y-1">
                    <TextLine label="City" value={row.raw_city} />
                    <TextLine label="Group" value={row.raw_group} />
                    <TextLine label="Area" value={row.raw_area} />
                </div>
            ),
        },
        {
            header: 'Matched',
            render: (row) => (
                <div className="min-w-[180px] space-y-1">
                    <p className="flex items-center gap-1 font-medium text-text-primary"><MapPin size={14} className="text-primary" />{leadArea(row)}</p>
                    <TextLine label="Branch" value={leadBranch(row)} />
                    <TextLine label="Owner" value={leadOwner(row)} />
                </div>
            ),
        },
        {
            header: 'Android',
            render: (row) => (
                <div className="min-w-[130px] space-y-1">
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold ${row.sent_to_android ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>
                        <Smartphone size={12} /> {row.sent_to_android ? 'Visible' : 'Not sent'}
                    </span>
                    <p className="text-xs text-text-secondary">{row.android_device_count || 0} devices · {row.android_user_count || 0} users</p>
                </div>
            ),
        },
        {
            header: 'Status',
            render: (row) => (
                <div className="min-w-[130px] space-y-2">
                    <DoubleTickStatusBadge status={row.status} type="lead" />
                    <p className="text-xs text-text-secondary">{row.pending_reason || leadTime(row)}</p>
                </div>
            ),
        },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex min-w-[180px] flex-col gap-1.5">
                    {row.suggested_match && (
                        <Button size="sm" className="justify-start" loading={working === `suggest-${row.id}`}
                            onClick={(event) => act(event, `suggest-${row.id}`, () => applySuggestion(row))}>
                            <Sparkles size={14} /> Apply Suggestion
                        </Button>
                    )}
                    <Button size="sm" variant="secondary" className="justify-start" onClick={(event) => { event.stopPropagation(); onCorrect(row); }}>
                        <MapPin size={14} /> Correct Location
                    </Button>
                    {row.conversation && (
                        <Button size="sm" variant="secondary" className="justify-start" loading={working === `request-${row.id}`}
                            onClick={(event) => act(event, `request-${row.id}`, () => doubletickAPI.requestLocation(row.conversation))}>
                            <Send size={14} /> Request Location
                        </Button>
                    )}
                    <button type="button" onClick={(event) => { event.stopPropagation(); onOpen(row); }}
                        className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold text-primary">
                        View <ArrowUpRight size={13} />
                    </button>
                </div>
            ),
        },
    ], [working]);

    return <Table columns={columns} data={leads} onRowClick={onOpen} />;
};

export default LeadTable;

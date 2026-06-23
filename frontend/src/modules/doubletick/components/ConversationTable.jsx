import React, { useMemo } from 'react';
import { AlertTriangle, ArrowUpRight, MapPin, MessageCircle, Zap, Clock } from 'lucide-react';
import Table from '../../../shared/components/Table';
import { formatDate } from '../../../shared/utils/formatDate';
import DoubleTickStatusBadge from './DoubleTickStatusBadge';
import { customerName, customerPhone, leadArea, leadLocation, pendingReason, wabaNumber } from '../display';

const ConversationTable = ({ conversations, onOpen }) => {
    const getReasonIcon = (reason) => {
        if (reason === 'missing_location' || reason === 'unmatched_location') return <MapPin size={14} className="text-danger" />;
        if (reason === 'manual_reply_required') return <Zap size={14} className="text-warning" />;
        if (reason === 'customer_stopped_replying') return <Clock size={14} className="text-info" />;
        return <AlertTriangle size={14} className="text-text-secondary" />;
    };

    const columns = useMemo(() => [
        {
            header: 'Customer',
            render: (row) => (
                <div className="flex items-start gap-3 min-w-[280px]">
                    <div className="bg-primary/10 text-primary rounded-lg p-2 flex-shrink-0">
                        <MessageCircle size={16} />
                    </div>
                    <div className="min-w-0">
                        <p className="font-semibold text-text-primary truncate">{customerName(row)}</p>
                        <p className="text-xs text-text-secondary truncate">{customerPhone(row)}</p>
                        <p className="text-xs text-text-secondary line-clamp-2 mt-1">{row.latest_customer_message || row.last_message || 'No message on record'}</p>
                    </div>
                </div>
            ),
        },
        {
            header: 'Status & Reason',
            render: (row) => (
                <div className="space-y-2 min-w-[200px]">
                    <div className="flex items-center gap-2">
                        <DoubleTickStatusBadge status={row.status} />
                        {row.requires_manual_attention && (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-warning/10 border border-warning/20 rounded text-xs text-warning font-medium">
                                <AlertTriangle size={12} />
                                Manual
                            </span>
                        )}
                    </div>
                    <div className={`text-xs font-medium flex items-center gap-1.5 ${row.requires_manual_attention ? 'text-warning' : 'text-text-secondary'}`}>
                        {getReasonIcon(row.pending_reason)}
                        {pendingReason(row)}
                    </div>
                </div>
            ),
        },
        {
            header: 'Location Info',
            render: (row) => (
                <div className="text-sm min-w-[170px] flex items-start gap-2">
                    <MapPin size={15} className="text-primary mt-0.5 flex-shrink-0" />
                    <div className="min-w-0">
                        <p className="font-medium text-text-primary truncate">{leadLocation(row)}</p>
                        <p className="text-xs text-text-secondary truncate">{leadArea(row)}</p>
                        <p className="text-xs text-text-secondary">{row.raw_service || 'Service pending'}</p>
                    </div>
                </div>
            ),
        },
        {
            header: 'Activity',
            render: (row) => (
                <div className="min-w-[140px] space-y-1">
                    {row.unread_count > 0 ? (
                        <span className="inline-flex items-center gap-1 text-sm font-semibold text-danger bg-danger/10 px-2 py-1 rounded">
                            <MessageCircle size={14} />
                            {row.unread_count} unread
                        </span>
                    ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-text-secondary">
                            <MessageCircle size={12} />
                            All read
                        </span>
                    )}
                    <p className="text-xs text-text-secondary">WABA: {wabaNumber(row)}</p>
                    <p className="text-xs text-text-secondary">{row.last_message_at ? formatDate(row.last_message_at, 'MMM dd, HH:mm') : '-'}</p>
                </div>
            ),
        },
        {
            header: 'Action',
            render: () => (
                <span className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs font-semibold text-primary hover:bg-primary/5 transition">
                    Work Queue
                    <ArrowUpRight size={13} />
                </span>
            ),
        },
    ], []);

    return <Table columns={columns} data={conversations} onRowClick={onOpen} />;
};

export default ConversationTable;

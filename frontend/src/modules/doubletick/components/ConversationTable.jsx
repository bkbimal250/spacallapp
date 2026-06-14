import React, { useMemo } from 'react';
import { MessageCircle, UserRound } from 'lucide-react';
import Table from '../../../shared/components/Table';
import { formatDate } from '../../../shared/utils/formatDate';
import DoubleTickStatusBadge from './DoubleTickStatusBadge';
import { formatLabel } from '../utils';

const ConversationTable = ({ conversations, onOpen }) => {
    const columns = useMemo(() => [
        {
            header: 'Customer',
            render: (row) => (
                <div className="flex items-center gap-3 min-w-[220px]">
                    <div className="bg-primary/10 text-primary rounded-lg p-2">
                        <UserRound size={16} />
                    </div>
                    <div>
                        <p className="font-semibold text-text-primary">{row.customer_name || row.phone_number || 'Unknown'}</p>
                        <p className="text-xs text-text-secondary">{row.phone_number || row.normalized_phone || '-'}</p>
                    </div>
                </div>
            ),
        },
        {
            header: 'Queue',
            render: (row) => (
                <div className="space-y-1">
                    <DoubleTickStatusBadge status={row.status} />
                    <p className="text-xs text-text-secondary">{formatLabel(row.pending_reason)}</p>
                </div>
            ),
        },
        {
            header: 'Area / Service',
            render: (row) => (
                <div className="text-sm">
                    <p className="text-text-primary">{row.matched_area_name || row.raw_area || '-'}</p>
                    <p className="text-xs text-text-secondary">{row.raw_city || row.raw_service || '-'}</p>
                </div>
            ),
        },
        {
            header: 'Unread',
            render: (row) => (
                <span className={`inline-flex items-center gap-1 text-sm font-semibold ${row.unread_count > 0 ? 'text-primary' : 'text-text-secondary'}`}>
                    <MessageCircle size={14} />
                    {row.unread_count || 0}
                </span>
            ),
        },
        {
            header: 'Last Activity',
            render: (row) => <span className="text-sm text-text-secondary">{row.last_message_at ? formatDate(row.last_message_at, 'MMM dd, HH:mm') : '-'}</span>,
        },
    ], []);

    return <Table columns={columns} data={conversations} onRowClick={onOpen} />;
};

export default ConversationTable;

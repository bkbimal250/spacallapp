import React from 'react';
import { ExternalLink, Eye } from 'lucide-react';
import Table from '../../../shared/components/Table';
import { formatDate } from '../../../shared/utils/formatDate';
import CopyButton from './CopyButton';
import LeadStatusBadge from './LeadStatusBadge';
import RoutingStatusBadge from './RoutingStatusBadge';
import NotificationStatusBadge from './NotificationStatusBadge';

const quickStatuses = ['contacted', 'converted', 'rejected'];

const WebsiteLeadTable = ({ leads, onView, onStatus, onAssign, canAssign = false, pendingOnly = false }) => {
    const columns = [
        { header: 'Customer Name', render: (row) => <span className="font-semibold">{row.customer_name}</span> },
        { header: 'Phone', render: (row) => <div className="flex items-center gap-2"><span>{row.phone}</span><CopyButton value={row.phone} label="Phone" /></div> },
        { header: 'Address', accessor: 'address' },
        { header: 'Notes', render: (row) => row.notes || '-' },
        { header: 'Website Name', accessor: 'website_name' },
        { header: 'Website URL', render: (row) => <a className="inline-flex items-center gap-1 text-primary" href={row.website_url} target="_blank" rel="noreferrer">Open<ExternalLink size={13} /></a> },
        { header: 'Branch/Spa', render: (row) => row.branch_name || 'Unassigned' },
        ...(!pendingOnly ? [{ header: 'Status', render: (row) => <LeadStatusBadge status={row.status} /> }] : []),
        { header: 'Routing Status', render: (row) => <RoutingStatusBadge status={row.routing_status} /> },
        ...(!pendingOnly ? [{ header: 'Notification', render: (row) => <NotificationStatusBadge status={row.notification_status} /> }] : []),
        { header: 'Created At', render: (row) => formatDate(row.created_at, 'MMM dd, HH:mm') },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex flex-wrap gap-1">
                    <button className="rounded p-1.5 text-primary hover:bg-primary/10" onClick={() => onView(row)} title="View"><Eye size={16} /></button>
                    {quickStatuses.map((status) => (
                        <button key={status} className="rounded border border-border px-2 py-1 text-xs text-text-secondary hover:bg-background" onClick={() => onStatus(row, status)}>
                            {status}
                        </button>
                    ))}
                    {canAssign && <button className="rounded border border-warning/30 px-2 py-1 text-xs font-semibold text-warning hover:bg-warning/10" onClick={() => onAssign(row)}>Assign</button>}
                </div>
            )
        },
    ];

    return <Table columns={columns} data={leads} />;
};

export default WebsiteLeadTable;

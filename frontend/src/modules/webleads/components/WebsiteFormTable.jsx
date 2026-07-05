import React from 'react';
import { BarChart3, Edit, Eye, ExternalLink, Power, Trash2 } from 'lucide-react';
import Table from '../../../shared/components/Table';
import { formatDate } from '../../../shared/utils/formatDate';
import CopyButton from './CopyButton';
import { buildReactExample, buildWidgetCode } from './WebsiteFormIntegrationCode';

const WebsiteFormTable = ({ forms, onView, onEdit, onToggle, onDelete, onLeads, onAnalytics }) => {
    const columns = [
        { header: 'Website Name', render: (row) => <span className="font-semibold">{row.website_name}</span> },
        { header: 'Website URL', render: (row) => <a className="inline-flex items-center gap-1 text-primary" href={row.website_url} target="_blank" rel="noreferrer">{row.website_url}<ExternalLink size={13} /></a> },
        { header: 'Branch/Spa', render: (row) => row.branch_name || 'Unassigned' },
        { header: 'Form Key', render: (row) => <div className="flex items-center gap-2"><code className="rounded bg-primary/10 px-2 py-1 text-xs text-primary">{row.form_key}</code><CopyButton value={row.form_key} label="Key" /></div> },
        { header: 'Status', render: (row) => <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${row.is_active ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>{row.is_active ? 'Active' : 'Inactive'}</span> },
        { header: 'Today Leads', render: (row) => row.today_leads || 0 },
        { header: 'Total Leads', render: (row) => row.total_leads || 0 },
        { header: 'Last Lead At', render: (row) => formatDate(row.last_lead_at, 'MMM dd, HH:mm') || '-' },
        { header: 'Created At', render: (row) => formatDate(row.created_at, 'MMM dd, yyyy') },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex flex-wrap gap-1">
                    <button className="rounded p-1.5 text-primary hover:bg-primary/10" onClick={() => onView(row)} title="View"><Eye size={16} /></button>
                    <button className="rounded p-1.5 text-warning hover:bg-warning/10" onClick={() => onEdit(row)} title="Edit"><Edit size={16} /></button>
                    <button className="rounded p-1.5 text-success hover:bg-success/10" onClick={() => onToggle(row)} title="Activate/Deactivate"><Power size={16} /></button>
                    <CopyButton value={buildWidgetCode(row)} label="Widget" />
                    <CopyButton value={buildReactExample(row)} label="React" />
                    <button className="rounded p-1.5 text-info hover:bg-info/10" onClick={() => onLeads(row)} title="View leads"><ExternalLink size={16} /></button>
                    <button className="rounded p-1.5 text-primary hover:bg-primary/10" onClick={() => onAnalytics(row)} title="Analytics"><BarChart3 size={16} /></button>
                    <button className="rounded p-1.5 text-danger hover:bg-danger/10" onClick={() => onDelete(row)} title="Delete"><Trash2 size={16} /></button>
                </div>
            )
        },
    ];

    return <Table columns={columns} data={forms} />;
};

export default WebsiteFormTable;

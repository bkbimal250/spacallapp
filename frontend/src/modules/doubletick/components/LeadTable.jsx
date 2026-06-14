import React, { useMemo } from 'react';
import { MapPin, UserCheck } from 'lucide-react';
import Table from '../../../shared/components/Table';
import { formatDate } from '../../../shared/utils/formatDate';
import DoubleTickStatusBadge from './DoubleTickStatusBadge';

const LeadTable = ({ leads, onOpen }) => {
    const columns = useMemo(() => [
        {
            header: 'Lead',
            render: (row) => (
                <div className="min-w-[220px]">
                    <p className="font-semibold text-text-primary">{row.customer_name || row.phone_number || 'Unknown'}</p>
                    <p className="text-xs text-text-secondary">{row.phone_number || row.normalized_phone || '-'}</p>
                </div>
            ),
        },
        {
            header: 'Area',
            render: (row) => (
                <div className="flex items-start gap-2">
                    <MapPin size={16} className="text-primary mt-0.5" />
                    <div>
                        <p className="text-sm text-text-primary">{row.matched_area_name || row.raw_area || row.area || '-'}</p>
                        <p className="text-xs text-text-secondary">{row.raw_city || row.city || row.service_name || '-'}</p>
                    </div>
                </div>
            ),
        },
        {
            header: 'Status',
            render: (row) => <DoubleTickStatusBadge status={row.status} type="lead" />,
        },
        {
            header: 'Owner',
            render: (row) => (
                <div className="flex items-start gap-2">
                    <UserCheck size={16} className="text-info mt-0.5" />
                    <div>
                        <p className="text-sm text-text-primary">{row.current_user_name || row.assigned_user_name || 'Unclaimed'}</p>
                        <p className="text-xs text-text-secondary">{row.current_branch_name || row.assigned_branch_name || '-'}</p>
                    </div>
                </div>
            ),
        },
        {
            header: 'Created',
            render: (row) => <span className="text-sm text-text-secondary">{row.created_at ? formatDate(row.created_at, 'MMM dd, HH:mm') : '-'}</span>,
        },
    ], []);

    return <Table columns={columns} data={leads} onRowClick={onOpen} />;
};

export default LeadTable;

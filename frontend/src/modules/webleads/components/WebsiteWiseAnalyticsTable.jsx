import React from 'react';
import Table from '../../../shared/components/Table';
import { formatDate } from '../../../shared/utils/formatDate';

const WebsiteWiseAnalyticsTable = ({ data = [] }) => (
    <Table
        data={data}
        columns={[
            { header: 'Website Name', accessor: 'website_name' },
            { header: 'Website URL', accessor: 'website_url' },
            { header: 'Branch/Spa', render: (row) => row.branch__spa_name || 'Unassigned' },
            { header: 'Total Leads', accessor: 'total_leads' },
            { header: 'Today', accessor: 'today_leads' },
            { header: 'This Month', accessor: 'monthly_leads' },
            { header: 'Converted', accessor: 'converted_leads' },
            { header: 'Duplicate', accessor: 'duplicate_leads' },
            { header: 'Last Lead At', render: (row) => formatDate(row.last_lead_received_at, 'MMM dd, HH:mm') },
        ]}
    />
);

export default WebsiteWiseAnalyticsTable;

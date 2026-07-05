import React from 'react';
import Table from '../../../shared/components/Table';

const BranchWiseAnalyticsTable = ({ data = [] }) => (
    <Table
        data={data}
        columns={[
            { header: 'Branch/Spa', render: (row) => row.branch__spa_name || 'Unassigned' },
            { header: 'Total Leads', accessor: 'total_leads' },
            { header: 'Today', accessor: 'today_leads' },
            { header: 'This Month', accessor: 'monthly_leads' },
            { header: 'Converted', accessor: 'converted_leads' },
            { header: 'Duplicate', accessor: 'duplicate_leads' },
            { header: 'Notification Failed', accessor: 'notification_failed_count' },
        ]}
    />
);

export default BranchWiseAnalyticsTable;

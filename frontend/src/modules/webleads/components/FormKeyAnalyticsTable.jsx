import React from 'react';
import Table from '../../../shared/components/Table';
import { formatDate } from '../../../shared/utils/formatDate';
import CopyButton from './CopyButton';

const FormKeyAnalyticsTable = ({ data = [] }) => (
    <Table
        data={data}
        columns={[
            { header: 'Form Key', render: (row) => <div className="flex items-center gap-2"><code className="rounded bg-primary/10 px-2 py-1 text-xs text-primary">{row.form_key}</code><CopyButton value={row.form_key} label="Key" /></div> },
            { header: 'Website Name', accessor: 'website_name' },
            { header: 'Website URL', accessor: 'website_url' },
            { header: 'Branch/Spa', render: (row) => row.branch__spa_name || 'Unassigned' },
            { header: 'Total Submissions', render: (row) => row.total_submissions || row.total_leads || 0 },
            { header: 'Successful', accessor: 'successful_submissions' },
            { header: 'Duplicate', accessor: 'duplicate_submissions' },
            { header: 'Rejected', accessor: 'rejected_submissions' },
            { header: 'Last Submitted At', render: (row) => formatDate(row.last_submitted_at, 'MMM dd, HH:mm') },
        ]}
    />
);

export default FormKeyAnalyticsTable;

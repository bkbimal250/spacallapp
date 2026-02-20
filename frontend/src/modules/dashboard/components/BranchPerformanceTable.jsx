import React from 'react';
import Table from '../../../shared/components/Table';
import Badge from '../../../shared/components/Badge';

const BranchPerformanceTable = ({ data = [] }) => {
    const columns = [
        { header: 'Branch Name', accessor: 'name' },
        { header: 'Total Calls', accessor: 'calls' },
        {
            header: 'Conversion Rate',
            render: (row) => `${row.conversion}%`
        },
        {
            header: 'Status',
            render: (row) => (
                <Badge variant={row.status === 'Active' ? 'green' : 'red'}>
                    {row.status}
                </Badge>
            )
        },
    ];

    return (
        <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Branch Performance</h3>
            </div>
            <Table columns={columns} data={data} />
        </div>
    );
};

export default BranchPerformanceTable;

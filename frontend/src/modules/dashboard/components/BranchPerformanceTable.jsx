import React, { useState } from 'react';
import Table from '../../../shared/components/Table';
import Badge from '../../../shared/components/Badge';
import Input from '../../../shared/components/Input';
import { Search } from 'lucide-react';

const BranchPerformanceTable = ({ data = [] }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredData = data.filter(branch =>
        branch.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const columns = [
        { header: 'Branch Name', accessor: 'name' },
        {
            header: 'Total Calls',
            render: (row) => (
                <span className="font-bold text-gray-900">{row.calls}</span>
            )
        },
        {
            header: 'Incoming',
            accessor: 'incoming',
            render: (row) => (
                <span className="text-emerald-600 font-medium">{row.incoming}</span>
            )
        },
        {
            header: 'Outgoing',
            accessor: 'outgoing',
            render: (row) => (
                <span className="text-blue-600 font-medium">{row.outgoing}</span>
            )
        },
        {
            header: 'Missed',
            accessor: 'missed',
            render: (row) => (
                <span className="text-rose-600 font-medium">{row.missed}</span>
            )
        },
        {
            header: 'Conv. Rate',
            render: (row) => (
                <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                        <div
                            className="bg-indigo-600 h-full rounded-full"
                            style={{ width: `${row.conversion}%` }}
                        ></div>
                    </div>
                    <span className="text-xs font-bold text-gray-700">{row.conversion}%</span>
                </div>
            )
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
        <div className="bg-white shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2rem] border border-gray-100 overflow-hidden flex flex-col">
            <div className="px-8 py-6 border-b border-gray-50 flex flex-col md:flex-row justify-between items-start md:items-center bg-gray-50/30 gap-4">
                <div>
                    <h3 className="text-lg font-black text-gray-900 tracking-tight">Branch Performance</h3>
                    <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest mt-1">Performance by call volume</p>
                </div>

                <div className="flex items-center gap-4 w-full md:w-auto">
                    <div className="relative w-full md:w-64">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <Input
                            placeholder="Search branch..."
                            className="pl-10"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <Badge variant="indigo" className="whitespace-nowrap">{filteredData.length} Branches</Badge>
                </div>
            </div>
            <div className="max-h-[500px] overflow-y-auto custom-scrollbar">
                <Table columns={columns} data={filteredData} />
            </div>
        </div>
    );
};

export default BranchPerformanceTable;

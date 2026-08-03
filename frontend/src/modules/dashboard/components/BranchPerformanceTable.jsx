import React, { useState } from 'react';
import Table from '../../../shared/components/Table';
import Badge from '../../../shared/components/Badge';
import Input from '../../../shared/components/Input';
import { Search, ChevronRight, Building2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const BranchPerformanceTable = ({ data = [] }) => {

    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');

    const topBranches = data.slice(0, 20);

    const filteredData = topBranches.filter(branch => {
        const haystack = [
            branch.name,
            branch.code,
            branch.city,
            branch.area,
            branch.state,
            branch.status,
        ].filter(Boolean).join(' ').toLowerCase();
        return haystack.includes(searchTerm.toLowerCase());
    });

    const columns = [
        {
            header: 'Branch Name',
            render: (row) => (
                <button
                    onClick={() => navigate(`/calllogs/details?branch=${row.id}`)}
                    className="flex flex-col items-start p-2 -m-2 rounded-xl transition-all group text-left w-full border border-transparent hover:border-primary/30 hover:bg-background"
                >
                    <div className="flex flex-wrap items-center gap-2">

                        <div className="flex items-center">
                            <div className="p-1.5 bg-background rounded-lg group-hover:bg-primary/10 group-hover:text-primary transition-colors mr-2">
                                <Building2 size={14} />
                            </div>

                            <span className="font-semibold text-text-primary group-hover:text-primary uppercase text-sm">
                                {row.name}
                            </span>

                            <ChevronRight
                                size={14}
                                className="ml-1 text-text-muted group-hover:text-primary group-hover:translate-x-0.5 transition-all"
                            />
                        </div>

                        <Badge variant={row.status === 'Active' ? 'green' : 'red'} size="sm">
                            {row.status}
                        </Badge>

                    </div>
                </button>
            )
        },

        {
            header: 'Total Calls',
            render: (row) => (
                <span className="font-semibold text-text-primary">
                    {row.calls || 0}
                </span>
            )
        },

        {
            header: 'Incoming',
            accessor: 'incoming',
            render: (row) => (
                <span className="text-success font-medium">
                    {row.incoming || 0}
                </span>
            )
        },

        {
            header: 'Outgoing',
            accessor: 'outgoing',
            render: (row) => (
                <span className="text-info font-medium">
                    {row.outgoing || 0}
                </span>
            )
        },

        {
            header: 'Missed',
            accessor: 'missed',
            render: (row) => (
                <span className="text-danger font-medium">
                    {row.missed || 0}
                </span>
            )
        },

        {
            header: 'Conv. Rate',
            render: (row) => (
                <div className="flex items-center space-x-2">

                    <div className="w-16 bg-background rounded-full h-1.5 overflow-hidden">

                        <div
                            className="bg-primary h-full rounded-full"
                            style={{ width: `${row.conversion || 0}%` }}
                        ></div>

                    </div>

                    <span className="text-xs font-semibold text-text-secondary">
                        {row.conversion || 0}%
                    </span>

                </div>
            )
        },
    ];

    return (

        <div className="bg-card border border-border rounded-2xl overflow-hidden flex flex-col">

            {/* HEADER */}

            <div className="px-6 py-5 border-b border-border flex flex-col md:flex-row justify-between items-start md:items-center gap-4">

                <div>
                    <h3 className="text-lg font-semibold text-text-primary">
                        Branch Performance
                    </h3>

                    <p className="text-xs text-text-muted uppercase tracking-wider mt-1">
                        Today performance by call volume
                    </p>
                </div>

                <div className="flex items-center gap-4 w-full md:w-auto">

                    <div className="relative w-full md:w-64">

                        <Search
                            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
                            size={16}
                        />

                        <Input
                            placeholder="Search branch, city, area, spa code..."
                            className="pl-10"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />

                    </div>

                    <Badge variant="primary" className="whitespace-nowrap">
                        Top {filteredData.length} / 20
                    </Badge>

                </div>

            </div>

            {/* TABLE */}

            <div className="max-h-[500px] overflow-y-auto">

                <Table
                    columns={columns}
                    data={filteredData}
                />

            </div>

        </div>

    );
};

export default BranchPerformanceTable;

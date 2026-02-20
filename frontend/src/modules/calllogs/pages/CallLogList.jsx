import React, { useEffect, useState } from 'react';
import { callLogsAPI } from '../api';
import Table from '../../../shared/components/Table';
import CallLogFilter from '../components/CallLogFilter';
import Badge from '../../../shared/components/Badge';
import { formatDate } from '../../../shared/utils/formatDate';
import { PhoneIncoming, PhoneOutgoing, PhoneMissed } from 'lucide-react';

const CallLogList = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({});

    const fetchLogs = async (currentFilters = {}) => {
        setLoading(true);
        try {
            const response = await callLogsAPI.getCallLogs(currentFilters);
            setLogs(response.data.results || response.data); // Handle pagination structure
        } catch (error) {
            console.error("Failed to fetch call logs", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs(filters);
    }, [filters]);

    const handleFilter = (newFilters) => {
        setFilters(prev => ({ ...prev, ...newFilters }));
    };

    const getCallIcon = (type) => {
        switch (type) {
            case 'incoming': return <PhoneIncoming size={16} className="text-green-500" />;
            case 'outgoing': return <PhoneOutgoing size={16} className="text-blue-500" />;
            case 'missed': return <PhoneMissed size={16} className="text-red-500" />;
            default: return <PhoneIncoming size={16} className="text-gray-500" />;
        }
    };

    const columns = [
        {
            header: 'Type',
            render: (row) => (
                <div className="flex items-center space-x-2">
                    {getCallIcon(row.call_type)}
                    <span className="capitalize">{row.call_type}</span>
                </div>
            )
        },
        { header: 'Number', accessor: 'phone_number' },
        {
            header: 'Duration',
            render: (row) => `${row.duration}s`
        },
        { header: 'Branch', accessor: 'branch_name' },
        { header: 'Device', accessor: 'device_uid' },
        {
            header: 'Time',
            render: (row) => formatDate(row.call_time)
        },
        {
            header: 'Status',
            render: (row) => (
                <Badge variant={row.call_type === 'missed' ? 'red' : 'green'}>
                    {row.call_type === 'missed' ? 'Missed' : 'Completed'}
                </Badge>
            )
        },
    ];

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-semibold text-gray-900">Call Logs</h1>

            <div className="bg-white shadow rounded-lg p-4">
                <CallLogFilter onFilter={handleFilter} />
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
                {loading ? (
                    <div className="p-4 text-center">Loading call logs...</div>
                ) : (
                    <Table
                        columns={columns}
                        data={logs}
                    />
                )}
            </div>
        </div>
    );
};

export default CallLogList;

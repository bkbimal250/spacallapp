import React, { useEffect, useState } from 'react';
import { callLogsAPI } from '../api';
import Table from '../../../shared/components/Table';
import CallLogFilter from '../components/CallLogFilter';
import Badge from '../../../shared/components/Badge';
import Pagination from '../../../shared/components/Pagination';
import Button from '../../../shared/components/Button';
import { formatDate } from '../../../shared/utils/formatDate';
import { useAuth } from '../../../shared/hooks/useAuth';
import { PhoneIncoming, PhoneOutgoing, PhoneMissed, PhoneForwarded, Trash2, FileDown } from 'lucide-react';

const CallLogList = () => {
    const { user } = useAuth();
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [statsLoading, setStatsLoading] = useState(true);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [selectedLogs, setSelectedLogs] = useState([]);
    const [exporting, setExporting] = useState(false);
    const pageSize = 20;

    const isSuperAdmin = user?.role === 'super_admin';
    const isAdmin = user?.role === 'admin' || isSuperAdmin;

    const fetchLogs = async (currentFilters = {}, currentPage = 1) => {
        setLoading(true);
        try {
            const response = await callLogsAPI.getCallLogs({ ...currentFilters, page: currentPage });
            setLogs(response.data.results);
            setTotalCount(response.data.count);
            setSelectedLogs([]);
        } catch (error) {
            console.error("Failed to fetch call logs", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async (currentFilters = {}) => {
        setStatsLoading(true);
        try {
            const response = await callLogsAPI.getCallLogStats(currentFilters);
            setStats(response.data);
        } catch (error) {
            console.error("Failed to fetch call log stats", error);
        } finally {
            setStatsLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs(filters, page);
    }, [filters, page]);

    useEffect(() => {
        fetchStats(filters);
    }, [filters]);

    const handleFilter = (newFilters) => {
        setFilters(newFilters);
        setPage(1);
    };

    const handlePageChange = (newPage) => {
        setPage(newPage);
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this call log? This action cannot be undone.')) {
            try {
                await callLogsAPI.deleteCallLog(id);
                fetchLogs(filters, page);
            } catch (error) {
                console.error("Failed to delete call log", error);
                alert("Failed to delete call log. Only Super Admins can perform this action.");
            }
        }
    };

    const handleBulkDelete = async () => {
        if (window.confirm(`Are you sure you want to delete ${selectedLogs.length} selected call logs? This action cannot be undone.`)) {
            try {
                await callLogsAPI.bulkDeleteCallLogs(selectedLogs);
                setSelectedLogs([]);
                fetchLogs(filters, page);
            } catch (error) {
                console.error("Bulk delete failed", error);
                alert("Failed to perform bulk delete. Only Super Admins can perform this action.");
            }
        }
    };

    const handleExport = async () => {
        setExporting(true);
        try {
            const response = await callLogsAPI.exportExcel(filters);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            const timestamp = new Date().toISOString().slice(0, 10);
            link.setAttribute('download', `call_logs_${timestamp}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Export failed", error);
            alert("Failed to export call logs. Please try again.");
        } finally {
            setExporting(false);
        }
    };

    const getCallIcon = (type) => {
        switch (type) {
            case 'incoming': return <PhoneIncoming size={16} className="text-green-500" />;
            case 'outgoing': return <PhoneOutgoing size={16} className="text-blue-500" />;
            case 'missed': return <PhoneMissed size={16} className="text-red-500" />;
            case 'rejected': return <PhoneForwarded size={16} className="text-orange-500" />;
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
        {
            header: 'SIM / Received On',
            render: (row) => (
                <div className="flex flex-col">
                    <span className="px-1.5 py-0.5 bg-indigo-50 text-indigo-700 rounded text-[10px] font-black uppercase w-fit mb-0.5">
                        Slot {row.sim_slot}
                    </span>
                    <span className="text-[11px] font-bold text-gray-400 tracking-tight">
                        {row.receiver_number || 'Unknown'}
                    </span>
                </div>
            )
        },
        { header: 'Branch', accessor: 'branch_name' },
        { header: 'Device', accessor: 'device_uid' },
        {
            header: 'Time',
            render: (row) => formatDate(row.call_time, 'MMM dd, yyyy HH:mm:ss')
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

    if (isSuperAdmin) {
        columns.push({
            header: 'Actions',
            render: (row) => (
                <button
                    onClick={() => handleDelete(row.id)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Delete Call Log"
                >
                    <Trash2 size={16} />
                </button>
            )
        });
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-semibold text-gray-900">Call Logs</h1>
                <div className="flex items-center space-x-3">
                    <Button
                        variant="white"
                        onClick={handleExport}
                        disabled={exporting || loading}
                        className="flex items-center space-x-2 border border-gray-200"
                    >
                        <FileDown size={16} className={exporting ? 'animate-bounce' : ''} />
                        <span>{exporting ? 'Exporting...' : 'Export Excel'}</span>
                    </Button>
                    {isSuperAdmin && selectedLogs.length > 0 && (
                        <Button
                            variant="red"
                            onClick={handleBulkDelete}
                            className="flex items-center space-x-2"
                        >
                            <Trash2 size={16} />
                            <span>Delete Selected ({selectedLogs.length})</span>
                        </Button>
                    )}
                </div>
            </div>

            {/* Stats Summary Bar */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                    <p className="text-xs font-medium text-gray-500 uppercase">Total Calls</p>
                    <p className="text-xl font-bold text-gray-900 mt-1">{statsLoading ? '...' : stats?.total || 0}</p>
                </div>
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-3">
                    <div className="p-2 bg-green-50 rounded-lg">
                        <PhoneIncoming size={18} className="text-green-600" />
                    </div>
                    <div>
                        <p className="text-xs font-medium text-gray-500 uppercase">Incoming</p>
                        <p className="text-xl font-bold text-green-600 mt-1">{statsLoading ? '...' : stats?.incoming || 0}</p>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-3">
                    <div className="p-2 bg-blue-50 rounded-lg">
                        <PhoneOutgoing size={18} className="text-blue-600" />
                    </div>
                    <div>
                        <p className="text-xs font-medium text-gray-500 uppercase">Outgoing</p>
                        <p className="text-xl font-bold text-blue-600 mt-1">{statsLoading ? '...' : stats?.outgoing || 0}</p>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-3">
                    <div className="p-2 bg-red-50 rounded-lg">
                        <PhoneMissed size={18} className="text-red-600" />
                    </div>
                    <div>
                        <p className="text-xs font-medium text-gray-500 uppercase">Missed</p>
                        <p className="text-xl font-bold text-red-600 mt-1">{statsLoading ? '...' : stats?.missed || 0}</p>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-3">
                    <div className="p-2 bg-orange-50 rounded-lg">
                        <PhoneForwarded size={18} className="text-orange-600" />
                    </div>
                    <div>
                        <p className="text-xs font-medium text-gray-500 uppercase">Rejected</p>
                        <p className="text-xl font-bold text-orange-600 mt-1">{statsLoading ? '...' : stats?.rejected || 0}</p>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                    <p className="text-xs font-medium text-gray-500 uppercase">Total Duration</p>
                    <p className="text-xl font-bold text-sky-600 mt-1">
                        {statsLoading ? '...' : `${Math.floor((stats?.total_duration || 0) / 60)}m ${(stats?.total_duration || 0) % 60}s`}
                    </p>
                </div>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
                <CallLogFilter onFilter={handleFilter} />
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden flex flex-col">
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-12 text-center text-gray-500">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500 mx-auto mb-4"></div>
                            Loading call logs...
                        </div>
                    ) : (
                        <Table
                            columns={columns}
                            data={logs}
                            selectable={isSuperAdmin}
                            selectedIds={selectedLogs}
                            onSelectionChange={setSelectedLogs}
                        />
                    )}
                </div>

                {!loading && totalCount > 0 && (
                    <Pagination
                        currentPage={page}
                        totalPages={Math.ceil(totalCount / pageSize)}
                        onPageChange={handlePageChange}
                    />
                )}
            </div>
        </div>
    );
};

export default CallLogList;

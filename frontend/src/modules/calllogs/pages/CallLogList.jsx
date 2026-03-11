import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { callLogsAPI } from '../api';
import Table from '../../../shared/components/Table';
import CallLogFilter from '../components/CallLogFilter';
import Badge from '../../../shared/components/Badge';
import Pagination from '../../../shared/components/Pagination';
import Button from '../../../shared/components/Button';
import { formatDate } from '../../../shared/utils/formatDate';
import { useAuth } from '../../../shared/hooks/useAuth';
import { leadManagementAPI } from '../../leadManagement/api';
import LeadForm from '../../leadManagement/components/LeadForm';
import { Edit, FileDown, PhoneIncoming, PhoneOutgoing, PhoneMissed, PhoneForwarded, Trash2, UserPlus, UserCheck, ExternalLink, X, Filter } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { contactApi } from '../../contacts/api';
import ContactForm from '../../contacts/components/ContactForm';

const CallLogList = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const initialBranch = queryParams.get('branch') || '';
    const initialSearch = queryParams.get('search') || '';

    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [statsLoading, setStatsLoading] = useState(true);
    const [filters, setFilters] = useState({ 
        branch: initialBranch, 
        search: initialSearch 
    });
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [selectedLogs, setSelectedLogs] = useState([]);
    const [exporting, setExporting] = useState(false);
    const [selectedLead, setSelectedLead] = useState(null);
    const [isLeadFormOpen, setIsLeadFormOpen] = useState(false);
    const [isContactFormOpen, setIsContactFormOpen] = useState(false);
    const [quickContactData, setQuickContactData] = useState(null);
    const pageSize = 50;

    const isSuperAdmin = user?.role === 'super_admin';
    const isAdmin = user?.role === 'admin' || isSuperAdmin;

    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const searchVal = queryParams.get('search') || '';
        const branchVal = queryParams.get('branch') || '';
        
        setFilters(prev => ({
            ...prev,
            search: searchVal,
            branch: branchVal
        }));
        setPage(1);
    }, [location.search]);

    const fetchLogs = async (currentFilters = {}, currentPage = 1, isBackground = false) => {
        if (!isBackground) setLoading(true);
        try {
            const response = await callLogsAPI.getCallLogs({ ...currentFilters, page: currentPage });
            setLogs(response.data.results);
            setTotalCount(response.data.count);
        } catch (error) {
            console.error("Failed to fetch call logs", error);
        } finally {
            if (!isBackground) setLoading(false);
        }
    };

    const fetchStats = async (currentFilters = {}, isBackground = false) => {
        if (!isBackground) setStatsLoading(true);
        try {
            const response = await callLogsAPI.getCallLogStats(currentFilters);
            setStats(response.data);
        } catch (error) {
            console.error("Failed to fetch call log stats", error);
        } finally {
            if (!isBackground) setStatsLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs(filters, page);
        fetchStats(filters);

        // Real-time polling every 10 seconds
        const intervalId = setInterval(() => {
            fetchLogs(filters, page, true);
            fetchStats(filters, true);
        }, 10000);

        return () => clearInterval(intervalId);
    }, [filters, page]);

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

    const handleQuickContact = (row) => {
        setQuickContactData({
            phone_number: row.phone_number,
            name: ''
        });
        setIsContactFormOpen(true);
    };

    const handleContactSubmit = async (data) => {
        try {
            await contactApi.createContact(data);
            setIsContactFormOpen(false);
            fetchLogs(filters, page);
        } catch (error) {
            console.error("Failed to create contact", error);
            alert("Failed to create contact. It might already exist.");
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

    const getStatusColor = (status) => {
        switch (status) {
            case 'pending': return 'gray';
            case 'calling': return 'blue';
            case 'coming': return 'purple';
            case 'interested': return 'green';
            case 'not_interested': return 'red';
            default: return 'gray';
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
        {
            header: 'Number / Contact',
            render: (row) => (
                <div className="flex flex-col group">
                    <div className="flex items-center space-x-2">
                        <span className="font-bold text-gray-900 tracking-tight">{row.phone_number}</span>
                        {row.contact ? (
                            <UserCheck size={14} className="text-green-500" />
                        ) : (
                            <button 
                                onClick={() => handleQuickContact(row)}
                                className="opacity-0 group-hover:opacity-100 p-0.5 bg-sky-50 text-sky-600 rounded-full transition-all hover:bg-sky-100"
                                title="Quick Add Contact"
                            >
                                <UserPlus size={12} />
                            </button>
                        )}
                    </div>
                    {row.contact_name ? (
                        <button 
                            onClick={() => navigate('/contacts')} 
                            className="text-[11px] text-sky-600 hover:underline flex items-center mt-0.5"
                        >
                            {row.contact_name}
                            <ExternalLink size={10} className="ml-1" />
                        </button>
                    ) : (
                        <span className="text-[11px] text-gray-400 italic mt-0.5">Unknown Contact</span>
                    )}
                </div>
            )
        },
        {
            header: 'Duration',
            render: (row) => `${row.duration}s`
        },
        {
            header: 'SIM / Received On',
            render: (row) => (
                <div className="flex flex-col">
                    <span className="px-1.5 py-0.5 bg-sky-50 text-sky-700 rounded text-[10px] font-black uppercase w-fit mb-0.5">
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
        {
            header: 'Lead Status',
            render: (row) => (
                <div className="flex items-center space-x-2">
                    {row.lead_status ? (
                        <Badge variant={getStatusColor(row.lead_status)}>
                            {row.lead_status.replace('_', ' ').toUpperCase()}
                        </Badge>
                    ) : (
                        <span className="text-xs text-gray-400 italic">No Lead</span>
                    )}
                    <button
                        onClick={() => handleEditLead(row)}
                        className="p-1 text-indigo-600 hover:bg-indigo-50 rounded"
                        title="Update Lead"
                    >
                        <Edit size={14} />
                    </button>
                </div>
            )
        },
    ];

    const handleEditLead = (row) => {
        if (row.lead_id) {
            setSelectedLead({
                id: row.lead_id,
                status: row.lead_status,
                branch: row.branch,
                // Add more if needed by LeadForm
            });
        } else {
            // Should not happen with auto-leads, but just in case
            setSelectedLead({
                calllog: row.id,
                branch: row.branch,
                status: 'pending'
            });
        }
        setIsLeadFormOpen(true);
    };

    const handleLeadSubmit = async (data) => {
        try {
            if (selectedLead?.id) {
                await leadManagementAPI.updateLead(selectedLead.id, data);
            } else {
                await leadManagementAPI.createLead({ ...data, calllog: selectedLead.calllog });
            }
            setIsLeadFormOpen(false);
            fetchLogs(filters, page);
        } catch (error) {
            console.error("Failed to update lead", error);
            alert("Failed to update lead status.");
        }
    };

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

            {(filters.search || filters.branch || filters.start_date) && (
                <div className="flex flex-wrap items-center gap-2 px-1 py-2">
                    <div className="flex items-center text-[10px] font-black text-gray-400 mr-2 uppercase tracking-widest">
                        <Filter size={10} className="mr-1" />
                        Active View
                    </div>
                    {filters.search && (
                        <div className="inline-flex items-center bg-sky-50 text-sky-700 px-3 py-1 rounded-lg text-xs font-bold border border-sky-100">
                            <span className="opacity-50 font-medium mr-1 uppercase text-[9px]">Search:</span>
                            {filters.search}
                            <button onClick={() => {
                                const newFilters = { ...filters };
                                delete newFilters.search;
                                handleFilter(newFilters);
                            }} className="ml-2 hover:bg-sky-200 rounded p-0.5">
                                <X size={12} />
                            </button>
                        </div>
                    )}
                    {filters.branch && (
                        <div className="inline-flex items-center bg-green-50 text-green-700 px-3 py-1 rounded-lg text-xs font-bold border border-green-100">
                            <span className="opacity-50 font-medium mr-1 uppercase text-[9px]">Branch ID:</span>
                            {filters.branch.substring(0, 8)}...
                            <button onClick={() => {
                                const newFilters = { ...filters };
                                delete newFilters.branch;
                                handleFilter(newFilters);
                            }} className="ml-2 hover:bg-green-200 rounded p-0.5">
                                <X size={12} />
                            </button>
                        </div>
                    )}
                    <button 
                        onClick={() => {
                            navigate('/calllogs/details');
                            handleFilter({});
                        }} 
                        className="text-[10px] font-bold text-gray-400 hover:text-red-500 uppercase tracking-widest hover:underline ml-2"
                    >
                        Reset All Filters
                    </button>
                </div>
            )}

            <div className="bg-white shadow rounded-lg p-6">
                <CallLogFilter 
                    onFilter={handleFilter} 
                    initialBranch={initialBranch} 
                    initialSearch={initialSearch}
                />
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
            <LeadForm
                isOpen={isLeadFormOpen}
                onClose={() => setIsLeadFormOpen(false)}
                onSubmit={handleLeadSubmit}
                initialData={selectedLead}
            />
            <ContactForm
                isOpen={isContactFormOpen}
                onClose={() => setIsContactFormOpen(false)}
                onSubmit={handleContactSubmit}
                initialData={quickContactData}
            />
        </div>
    );
};

export default CallLogList;

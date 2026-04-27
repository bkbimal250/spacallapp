import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { callLogsAPI } from '../api';
import Table from '../../../shared/components/Table';
import CallLogFilter from '../components/CallLogFilter';
import CallLogStats from '../components/CallLogStats';
import Badge from '../../../shared/components/Badge';
import Pagination from '../../../shared/components/Pagination';
import Button from '../../../shared/components/Button';
import { formatDate } from '../../../shared/utils/formatDate';
import { useAuth } from '../../../shared/hooks/useAuth';
import { leadManagementAPI } from '../../leadManagement/api';
import LeadForm from '../../leadManagement/components/LeadForm';
import {
    Edit,
    FileDown,
    PhoneIncoming,
    PhoneOutgoing,
    PhoneMissed,
    PhoneForwarded,
    Trash2,
    UserPlus,
    UserCheck,
    ExternalLink,
    X,
    MapPin,
    Filter
} from 'lucide-react';
import { contactApi } from '../../contacts/api';
import ContactForm from '../../contacts/components/ContactForm';
import { branchesAPI } from '../../branches/api';
import { PageSpinner, ContentSkeleton, SubtleLoader } from '../../../shared/components/loaders';

const CallLogList = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const queryParams = new URLSearchParams(location.search);
    const initialBranch = queryParams.get('branch') || '';
    const initialDevice = queryParams.get('device') || '';
    const initialSearch = queryParams.get('search') || '';
    const initialCallType = queryParams.get('call_type') || '';
    const initialFollowupStatus = queryParams.get('followup_status') || '';

    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [statsLoading, setStatsLoading] = useState(true);
    const [filters, setFilters] = useState({
        branch: initialBranch,
        device: initialDevice,
        search: initialSearch,
        quick_date: queryParams.has('quick_date') ? queryParams.get('quick_date') : (queryParams.has('start_date') || queryParams.has('end_date') ? '' : 'today'),
        start_date: queryParams.get('start_date') || '',
        end_date: queryParams.get('end_date') || '',
        is_unique: queryParams.get('is_unique') === 'true'
    });

    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [selectedLogs, setSelectedLogs] = useState([]);
    const [exporting, setExporting] = useState(false);

    const [selectedLead, setSelectedLead] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: 'call_time', direction: 'desc' });
    const [isLeadFormOpen, setIsLeadFormOpen] = useState(false);

    const [isContactFormOpen, setIsContactFormOpen] = useState(false);
    const [quickContactData, setQuickContactData] = useState(null);

    const [branches, setBranches] = useState([]);

    const pageSize = 25;

    const isSuperAdmin = user?.role === 'super_admin';
    const isAdmin = user?.role === 'admin' || isSuperAdmin;

    useEffect(() => {
        const fetchBranches = async () => {
            if (!isAdmin) return;
            try {
                const response = await branchesAPI.getBranches({ all: true });
                const data = response.data.results || response.data;
                setBranches(data);
            } catch (err) {
                console.error(err);
            }
        };
        fetchBranches();
    }, [isAdmin]);

    const getBranchName = (id) => {
        const branch = branches.find(b => b.id === id);
        return branch ? branch.spa_name : id;
    };

    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);

        setFilters(prev => ({
            ...prev,
            search: queryParams.get('search') || '',
            branch: queryParams.get('branch') || '',
            device: queryParams.get('device') || '',
            quick_date: queryParams.has('quick_date') ? queryParams.get('quick_date') : (queryParams.has('start_date') || queryParams.has('end_date') ? '' : 'today'),
            start_date: queryParams.get('start_date') || '',
            end_date: queryParams.get('end_date') || '',
            is_unique: queryParams.get('is_unique') === 'true'
        }));

        setPage(1);
    }, [location.search]);

    const fetchLogs = useCallback(async (currentFilters = {}, currentPage = 1, background = false) => {
        if (!background) setLoading(true);
        else setRefreshing(true);

        const ordering = sortConfig.key ? (sortConfig.direction === 'desc' ? `-${sortConfig.key}` : sortConfig.key) : null;

        try {
            const response = await callLogsAPI.getCallLogs({
                ...currentFilters,
                page: currentPage,
                ordering
            });

            setLogs(response.data.results);
            setTotalCount(response.data.count);

        } catch (error) {
            console.error(error);
        } finally {
            if (!background) setLoading(false);
            else setRefreshing(false);
        }
    }, [pageSize, sortConfig]);

    const fetchStats = useCallback(async (currentFilters = {}, background = false) => {
        if (!background) setStatsLoading(true);

        try {
            const response = await callLogsAPI.getCallLogStats(currentFilters);
            setStats(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            if (!background) setStatsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchLogs(filters, page);
        fetchStats(filters);

        const interval = setInterval(() => {
            fetchLogs(filters, page, true);
            fetchStats(filters, true);
        }, 10000);

        return () => clearInterval(interval);

    }, [filters, page, fetchLogs, fetchStats]);

    const handleFilter = useCallback((newFilters) => {
        const params = new URLSearchParams();
        Object.entries(newFilters).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                params.set(key, value);
            }
        });
        navigate(`?${params.toString()}`, { replace: true });
        // The useEffect watching location.search will update the filters state
    }, [navigate]);

    const handleSort = useCallback((key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
        }));
        setPage(1);
    }, []);

    const handlePageChange = useCallback((newPage) => {
        setPage(newPage);
    }, []);

    const handleDelete = useCallback(async (id) => {
        if (!window.confirm("Delete this call log?")) return;

        try {
            await callLogsAPI.deleteCallLog(id);
            fetchLogs(filters, page);
        } catch (err) {
            console.error(err);
        }
    }, [filters, page, fetchLogs]);

    const handleBulkDelete = useCallback(async () => {
        if (!window.confirm("Delete selected logs?")) return;

        try {
            await callLogsAPI.bulkDeleteCallLogs(selectedLogs);
            setSelectedLogs([]);
            fetchLogs(filters, page);
        } catch (err) {
            console.error(err);
        }
    }, [selectedLogs, filters, page, fetchLogs]);

    const handleQuickContact = useCallback((row) => {
        setQuickContactData({
            phone_number: row.phone_number,
            name: ''
        });
        setIsContactFormOpen(true);
    }, []);

    const handleContactSubmit = useCallback(async (data) => {
        try {
            await contactApi.createContact(data);
            setIsContactFormOpen(false);
            fetchLogs(filters, page);
        } catch (err) {
            console.error(err);
        }
    }, [filters, page, fetchLogs]);

    const handleExport = useCallback(async () => {
        setExporting(true);

        try {
            const response = await callLogsAPI.exportExcel(filters);

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement("a");

            link.href = url;
            link.download = `call_logs_${new Date().toISOString().slice(0, 10)}.xlsx`;

            document.body.appendChild(link);
            link.click();
            link.remove();

        } catch (err) {
            console.error(err);
        } finally {
            setExporting(false);
        }
    }, [filters]);

    const getCallIcon = useCallback((type) => {
        switch (type) {
            case "incoming": return <PhoneIncoming size={16} className="text-success" />;
            case "outgoing": return <PhoneOutgoing size={16} className="text-info" />;
            case "missed": return <PhoneMissed size={16} className="text-danger" />;
            case "rejected": return <PhoneForwarded size={16} className="text-warning" />;
            default: return null;
        }
    }, []);

    const columns = React.useMemo(() => {
        const cols = [
            {
                header: "Type",
                render: (row) => (
                    <div className="flex items-center gap-2">
                        {getCallIcon(row.call_type)}
                        <span className="capitalize">{row.call_type}</span>
                    </div>
                )
            },
            {
                header: "Phone Number",
                sortKey: "phone_number",
                render: (row) => (
                    <div className="flex flex-col">
                        <div className="flex items-center gap-2">
                            <span className="font-semibold">{row.phone_number}</span>
                            {row.contact && (
                                <Badge variant="blue" className="text-[10px] py-0">
                                    MATCHED
                                </Badge>
                            )}
                        </div>
                        {row.contact && (
                            <span className="text-xs text-text-secondary">{row.contact.name}</span>
                        )}
                    </div>
                )
            },
            {
                header: "Duration",
                sortKey: "duration",
                render: (row) => (
                    <span className="font-mono text-xs">
                        {row.duration}s
                    </span>
                )
            },
            {
                header: "Branch",
                sortKey: "branch__spa_name",
                render: (row) => (
                    <div className="flex items-center gap-1.5 opacity-80">
                        <MapPin size={12} />
                        <span className="text-xs">{row.branch_name || "N/A"}</span>
                    </div>
                )
            },
            {
                header: "Device",
                render: (row) => (
                    <div className="flex flex-col">
                        {row.phone_name && (
                            <span className="font-semibold text-primary text-xs uppercase tracking-wider">
                                {row.phone_name}
                            </span>
                        )}
                        <span className="font-mono text-xs text-text-secondary">{row.device_uid}</span>
                    </div>
                )
            },
            {
                header: "Call Time",
                sortKey: "call_time",
                render: (row) => formatDate(row.call_time, 'MMM dd, yyyy HH:mm:ss')
            },
            {
                header: "Created Time",
                sortKey: "created_at",
                render: (row) => formatDate(row.created_at, 'MMM dd, yyyy HH:mm:ss')
            },
            {
                header: "Status",
                render: (row) => (
                    <Badge variant={row.call_type === "missed" ? "red" : "green"}>
                        {row.call_type === "missed" ? "Missed" : "Completed"}
                    </Badge>
                )
            },
            {
                header: "Follow-up",
                render: (row) => {
                    if (row.call_type !== "missed") return <span className="text-gray-400 text-xs">-</span>;

                    const isFollowed = row.is_followed_up;
                    const status = row.followup_status;

                    if (isFollowed) {
                        const variant = status === 'GOOD' ? 'success' : (status === 'OK' ? 'warning' : 'danger');

                        return (
                            <div className="flex flex-col gap-1 items-center" title="Follow-up complete">
                                <Badge variant={variant} className="text-[10px] px-2 py-0.5 whitespace-nowrap shadow-sm border-none font-bold">
                                    {status || 'DONE'}
                                </Badge>
                                <div className="flex items-center gap-1 text-[10px] text-success font-black drop-shadow-sm uppercase">
                                    <UserCheck size={12} strokeWidth={3} /> Followed Up
                                </div>
                            </div>
                        );
                    }

                    return (
                        <div className="flex flex-col gap-1 items-center" title="Pending follow-up">
                            <Badge variant="gray" className="text-[10px] px-2 py-0.5 animate-pulse bg-slate-200 text-slate-600 border-none">
                                Pending...
                            </Badge>
                            <span className="text-[10px] text-text-secondary italic font-medium">Wait for Callback</span>
                        </div>
                    );
                }
            }
        ];

        if (isSuperAdmin) {
            cols.push({
                header: "Actions",
                render: (row) => (
                    <button
                        onClick={(e) => { e.stopPropagation(); handleDelete(row.id); }}
                        className="text-danger hover:bg-danger/10 p-1.5 rounded transition"
                        title="Delete Log"
                    >
                        <Trash2 size={16} />
                    </button>
                )
            });
        }
        return cols;
    }, [isSuperAdmin, navigate, handleQuickContact, handleDelete, getCallIcon]);

    return (
        <div className="space-y-6 text-text-primary">

            <div className="flex justify-between items-center">

                <h1 className="text-2xl font-semibold">
                    Call Logs
                </h1>

                <div className="flex gap-2">

                    <Button
                        onClick={handleExport}
                        loading={exporting}
                        className="flex items-center gap-2"
                    >
                        <FileDown size={16} />
                        Export Excel
                    </Button>

                    {isSuperAdmin && selectedLogs.length > 0 && (
                        <Button
                            variant="danger"
                            onClick={handleBulkDelete}
                        >
                            Delete Selected
                        </Button>
                    )}

                </div>

            </div>

            <div className="bg-card border border-border rounded-lg p-6">
                <CallLogFilter
                    onFilter={handleFilter}
                    initialBranch={initialBranch}
                    initialDevice={initialDevice}
                    initialSearch={initialSearch}
                    initialCallType={initialCallType}
                    initialFollowupStatus={initialFollowupStatus}
                    initialUnique={filters.is_unique}
                    initialQuickDate={filters.quick_date}
                    initialStartDate={filters.start_date}
                    initialEndDate={filters.end_date}
                />
            </div>

            <CallLogStats
                stats={stats}
                loading={statsLoading}
            />

            <div className="bg-card border border-border rounded-lg overflow-hidden flex flex-col">
                <SubtleLoader isVisible={refreshing} />
                <div className="overflow-x-auto min-h-[400px]">
                    {loading && logs.length === 0 ? (
                        <PageSpinner message="Loading call logs..." />
                    ) : loading && logs.length > 0 ? (
                        <ContentSkeleton rows={15} />
                    ) : (
                        <>
                            {logs.length === 0 ? (
                                <div className="p-12 text-center text-text-secondary">
                                    No call logs found.
                                </div>
                            ) : (
                                <Table
                                    columns={columns}
                                    data={logs}
                                    selectable={isSuperAdmin}
                                    selectedIds={selectedLogs}
                                    onSelectionChange={setSelectedLogs}
                                    onSort={handleSort}
                                    sortConfig={sortConfig}
                                />
                            )}
                        </>
                    )}
                </div>

                {!loading && totalCount > 0 && (
                    <Pagination
                        currentPage={page}
                        totalPages={Math.ceil(totalCount / pageSize)}
                        onPageChange={handlePageChange}
                        totalCount={totalCount}
                        pageSize={pageSize}
                    />
                )}

            </div>

            <LeadForm
                isOpen={isLeadFormOpen}
                onClose={() => setIsLeadFormOpen(false)}
                onSubmit={() => { }}
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
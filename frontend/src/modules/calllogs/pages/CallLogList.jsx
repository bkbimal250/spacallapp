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
    Filter
} from 'lucide-react';
import { contactApi } from '../../contacts/api';
import ContactForm from '../../contacts/components/ContactForm';
import { branchesAPI } from '../../branches/api';

const CallLogList = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const queryParams = new URLSearchParams(location.search);
    const initialBranch = queryParams.get('branch') || '';
    const initialDevice = queryParams.get('device') || '';
    const initialSearch = queryParams.get('search') || '';

    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [statsLoading, setStatsLoading] = useState(true);
    const [filters, setFilters] = useState({
        branch: initialBranch,
        device: initialDevice,
        search: initialSearch,
        is_unique: queryParams.get('is_unique') === 'true'
    });

    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [selectedLogs, setSelectedLogs] = useState([]);
    const [exporting, setExporting] = useState(false);

    const [selectedLead, setSelectedLead] = useState(null);
    const [isLeadFormOpen, setIsLeadFormOpen] = useState(false);

    const [isContactFormOpen, setIsContactFormOpen] = useState(false);
    const [quickContactData, setQuickContactData] = useState(null);

    const [branches, setBranches] = useState([]);

    const pageSize = 100;

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
            is_unique: queryParams.get('is_unique') === 'true'
        }));

        setPage(1);
    }, [location.search]);

    const fetchLogs = useCallback(async (currentFilters = {}, currentPage = 1, background = false) => {
        if (!background) setLoading(true);

        try {
            const response = await callLogsAPI.getCallLogs({
                ...currentFilters,
                page: currentPage
            });

            setLogs(response.data.results);
            setTotalCount(response.data.count);

        } catch (error) {
            console.error(error);
        } finally {
            if (!background) setLoading(false);
        }
    }, [pageSize]);

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
        setFilters(newFilters);
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
                header: "Number",
                render: (row) => (
                    <div className="flex flex-col group">
                        <div className="flex items-center gap-2">
                            <span className="font-semibold">{row.phone_number}</span>
                            {row.contact ? (
                                <UserCheck size={14} className="text-success" title="Verified Contact" />
                            ) : (
                                <button
                                    onClick={(e) => { e.stopPropagation(); handleQuickContact(row); }}
                                    className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-gray-100 rounded transition"
                                    title="Add Contact"
                                >
                                    <UserPlus size={14} />
                                </button>
                            )}
                        </div>
                        {row.contact_name ? (
                            <button
                                onClick={(e) => { e.stopPropagation(); navigate("/contacts"); }}
                                className="text-xs text-primary flex items-center gap-1 hover:underline"
                            >
                                {row.contact_name}
                                <ExternalLink size={10} />
                            </button>
                        ) : (
                            <span className="text-xs text-text-secondary italic">Unknown Contact</span>
                        )}
                    </div>
                )
            },
            {
                header: "Duration",
                render: (row) => `${row.duration}s`
            },
            {
                header: "Branch",
                render: (row) => (
                    <div className="flex flex-col">
                        <span className="font-semibold text-text-primary">{row.branch_name}</span>
                        <span className="text-xs text-text-secondary">Code: {row.branch_code}</span>
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
                render: (row) => formatDate(row.call_time, 'MMM dd, yyyy HH:mm:ss')
            },
            {
                header: "Created Time",
                render: (row) => formatDate(row.created_at, 'MMM dd, yyyy HH:mm:ss')
            },
            {
                header: "Status",
                render: (row) => (
                    <Badge variant={row.call_type === "missed" ? "danger" : "success"}>
                        {row.call_type === "missed" ? "Missed" : "Completed"}
                    </Badge>
                )
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
                        disabled={exporting}
                        className="flex items-center gap-2"
                    >
                        <FileDown size={16} />
                        {exporting ? "Exporting..." : "Export Excel"}
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
                    initialUnique={filters.is_unique}
                />
            </div>

            <CallLogStats 
                stats={stats} 
                loading={statsLoading} 
            />

            <div className="bg-card border border-border rounded-lg overflow-hidden">

                {loading ? (
                    <div className="p-10 text-center text-text-secondary">
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
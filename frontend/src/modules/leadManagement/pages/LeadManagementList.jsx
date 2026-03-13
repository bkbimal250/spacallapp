import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { leadManagementAPI } from '../api';
import Table from '../../../shared/components/Table';
import Badge from '../../../shared/components/Badge';
import Pagination from '../../../shared/components/Pagination';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import { formatDate } from '../../../shared/utils/formatDate';
import { useAuth } from '../../../shared/hooks/useAuth';
import { Edit, Trash2, Search, Filter, Target } from 'lucide-react';
import LeadForm from '../components/LeadForm';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';
import StatsCard from '../../dashboard/components/StatsCard';

const LeadManagementList = () => {
    const { user } = useAuth();
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const initialBranch = queryParams.get('branch') || '';
    const initialStatus = queryParams.get('status') || '';

    const [leads, setLeads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 50;

    const [filters, setFilters] = useState({
        branch: initialBranch,
        status: initialStatus,
        search: ''
    });

    const [isFormOpen, setIsFormOpen] = useState(false);
    const [selectedLead, setSelectedLead] = useState(null);
    const [updatingId, setUpdatingId] = useState(null);
    const [branches, setBranches] = useState([]);

    const isSuperAdmin = user?.role === 'super_admin';
    const isAdmin = user?.role === 'admin' || isSuperAdmin;

    useEffect(() => {
        const fetchBranches = async () => {
            if (!isAdmin) return;
            try {
                const response = await branchesAPI.getBranches();
                const data = response.data.results || response.data;
                setBranches(data.map(b => ({ value: b.id, label: b.spa_name })));
            } catch (err) {
                console.error("Failed to fetch branches", err);
            }
        };
        fetchBranches();
    }, [isAdmin]);

    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const branchVal = queryParams.get('branch') || '';
        const statusVal = queryParams.get('status') || '';
        const searchVal = queryParams.get('search') || '';

        setFilters(prev => ({
            ...prev,
            branch: branchVal,
            status: statusVal,
            search: searchVal
        }));
        setPage(1);
    }, [location.search]);

    const fetchLeads = async (currentFilters = {}, currentPage = 1, isBackground = false) => {
        if (!isBackground) setLoading(true);
        try {
            const apiFilters = { page: currentPage };

            if (currentFilters.branch) {
                if (currentFilters.branch === 'null') {
                    apiFilters.branch__isnull = 'True';
                } else {
                    apiFilters.branch = currentFilters.branch;
                }
            }

            if (currentFilters.status) apiFilters.status = currentFilters.status;
            if (currentFilters.search) apiFilters.search = currentFilters.search;

            const response = await leadManagementAPI.getLeads(apiFilters);
            setLeads(response.data.results);
            setTotalCount(response.data.count);
        } catch (error) {
            console.error("Failed to fetch leads", error);
        } finally {
            if (!isBackground) setLoading(false);
        }
    };

    useEffect(() => {
        fetchLeads(filters, page);

        const intervalId = setInterval(() => {
            fetchLeads(filters, page, true);
        }, 10000);

        return () => clearInterval(intervalId);
    }, [filters, page]);

    const handleFilterChange = (field, value) => {
        setFilters(prev => ({ ...prev, [field]: value }));
        setPage(1);
    };

    const handlePageChange = (newPage) => {
        setPage(newPage);
    };

    const handleEditLead = (lead) => {
        setSelectedLead(lead);
        setIsFormOpen(true);
    };

    const handleDeleteLead = async (id) => {
        if (window.confirm('Are you sure you want to delete this lead?')) {
            try {
                await leadManagementAPI.deleteLead(id);
                fetchLeads(filters, page);
            } catch (error) {
                console.error("Failed to delete lead", error);
                alert("Failed to delete lead.");
            }
        }
    };

    const handleFormSubmit = async (data) => {
        try {
            if (selectedLead) {
                await leadManagementAPI.updateLead(selectedLead.id, data);
            } else {
                await leadManagementAPI.createLead(data);
            }

            setIsFormOpen(false);
            fetchLeads(filters, page);
        } catch (error) {
            console.error("Failed to save lead", error);
            alert("Failed to save lead.");
        }
    };

    const handleUpdateStatus = async (id, newStatus) => {
        setUpdatingId(id);
        try {
            await leadManagementAPI.updateLead(id, { status: newStatus });
            fetchLeads(filters, page);
        } catch (error) {
            console.error("Failed to update lead status", error);
            alert("Failed to update lead status.");
        } finally {
            setUpdatingId(null);
        }
    };

    const getStatusColor = React.useCallback((status) => {
        switch (status) {
            case 'pending': return 'secondary';
            case 'ringing': return 'info';
            case 'coming': return 'accent';
            case 'interested': return 'success';
            case 'not_interested': return 'danger';
            default: return 'secondary';
        }
    }, []);

    const columns = React.useMemo(() => [
        {
            header: 'Number / Contact',
            render: (row) => (
                <div className="flex flex-col">
                    <span className="font-semibold text-text-primary">
                        {row.phone_number || 'Unknown'}
                    </span>
                    <span className="text-xs text-text-secondary">
                        {row.contact_name || 'No Contact'}
                    </span>
                </div>
            )
        },
        {
            header: 'Branch',
            render: (row) => (
                <span className="text-sm text-text-primary">
                    {row.branch_name || '-'}
                </span>
            )
        },
        {
            header: 'Details',
            render: (row) => (
                <div className="flex flex-col max-w-xs">
                    {row.booking_date && (
                        <span className="text-xs text-primary font-medium whitespace-nowrap">
                            Booking: {formatDate(row.booking_date, 'MMM dd, yyyy')}
                        </span>
                    )}
                    {row.remarks && (
                        <span className="text-xs text-text-secondary truncate" title={row.remarks}>
                            {row.remarks}
                        </span>
                    )}
                    {!row.booking_date && !row.remarks && (
                        <span className="text-xs text-text-secondary italic">
                            No details
                        </span>
                    )}
                </div>
            )
        },
        {
            header: 'Time',
            render: (row) => (
                <span className="text-sm text-text-secondary">
                    {formatDate(row.created_at, 'MMM dd, HH:mm')}
                </span>
            )
        },
        {
            header: 'Status',
            render: (row) => (
                <Badge variant={getStatusColor(row.status)}>
                    {row.status}
                </Badge>
            )
        },
        {
            header: 'Update Status',
            render: (row) => (
                <select
                    className="block w-full px-2 py-1 text-xs bg-card border border-border rounded-md text-text-primary focus:border-primary outline-none cursor-pointer"
                    value={row.status}
                    disabled={updatingId === row.id}
                    onChange={(e) => handleUpdateStatus(row.id, e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                >
                    <option value="pending">Pending</option>
                    <option value="ringing">Ringing</option>
                    <option value="coming">Coming</option>
                    <option value="interested">Interested</option>
                    <option value="not_interested">Not Interested</option>
                </select>
            )
        },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex space-x-2">
                    <button
                        onClick={(e) => { e.stopPropagation(); handleEditLead(row); }}
                        className="p-1.5 text-primary hover:bg-primary/10 rounded-lg transition"
                        title="Edit Lead"
                    >
                        <Edit size={16} />
                    </button>
                    {isSuperAdmin && (
                        <button
                            onClick={(e) => { e.stopPropagation(); handleDeleteLead(row.id); }}
                            className="p-1.5 text-danger hover:bg-danger/10 rounded-lg transition"
                            title="Delete Lead"
                        >
                            <Trash2 size={16} />
                        </button>
                    )}
                </div>
            )
        }
    ], [isSuperAdmin, updatingId, getStatusColor]);

    const leadStats = [
        {
            title: "Total Leads",
            value: totalCount,
            icon: <Target className="text-primary" size={20} />
        },
        {
            title: "Filtered",
            value: leads.length,
            icon: <Filter className="text-info" size={20} />
        }
    ];

    return (
        <div className="space-y-6 text-text-primary">

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">
                        Lead Management
                    </h1>
                    <p className="text-sm text-text-secondary">
                        Follow up and track lead conversions
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {leadStats.map((stat, idx) => (
                    <StatsCard
                        key={idx}
                        title={stat.title}
                        value={stat.value}
                        icon={stat.icon}
                        className="bg-card border border-border"
                    />
                ))}
            </div>

            <div className="bg-card border border-border rounded-2xl p-6 shadow-lg">

                <div className="flex flex-col mb-6 p-5 bg-background rounded-xl border border-border">

                    <div className="flex items-center gap-2 mb-6">
                        <Search size={18} className="text-primary" />
                        <h2 className="text-lg font-semibold text-text-primary">
                            Search & Filter
                        </h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">

                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-text-secondary uppercase">
                                Search Contact
                            </label>
                            <Input
                                placeholder="Name or number..."
                                className="!bg-card h-11 border-border text-text-primary focus:border-primary rounded-lg"
                                value={filters.search}
                                onChange={(e) => handleFilterChange('search', e.target.value)}
                            />
                        </div>

                        {isAdmin && (
                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-text-secondary uppercase">
                                    Branch
                                </label>
                                <SearchableSelect
                                    placeholder="Filter by branch..."
                                    options={branches}
                                    value={filters.branch}
                                    onChange={(val) => handleFilterChange('branch', val)}
                                    className="!bg-card border-border"
                                />
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-text-secondary uppercase">
                                Lead Status
                            </label>

                            <select
                                className="block w-full px-3 py-2 bg-card border border-border rounded-lg text-sm text-text-primary focus:border-primary outline-none h-11"
                                value={filters.status}
                                onChange={(e) => handleFilterChange('status', e.target.value)}
                            >
                                <option value="">All Statuses</option>
                                <option value="pending">Pending</option>
                                <option value="ringing">Ringing</option>
                                <option value="coming">Coming</option>
                                <option value="interested">Interested</option>
                                <option value="not_interested">Not Interested</option>
                            </select>
                        </div>

                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                onClick={() => setFilters({ branch: '', status: '', search: '' })}
                                className="flex-1 h-11 rounded-lg border-border text-text-secondary hover:bg-cardHover"
                            >
                                Clear
                            </Button>
                        </div>

                    </div>
                </div>

                <div className="max-h-[600px] overflow-y-auto border border-border rounded-xl">

                    {loading ? (
                        <div className="p-12 text-center text-text-secondary">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                            Loading leads...
                        </div>
                    ) : (
                        <Table columns={columns} data={leads} />
                    )}

                </div>

                {!loading && totalCount > 0 && Math.ceil(totalCount / pageSize) > 1 && (
                    <div className="mt-4 px-4 pb-4">
                        <Pagination
                            currentPage={page}
                            totalPages={Math.ceil(totalCount / pageSize)}
                            onPageChange={handlePageChange}
                        />
                    </div>
                )}

            </div>

            <LeadForm
                isOpen={isFormOpen}
                onClose={() => setIsFormOpen(false)}
                onSubmit={handleFormSubmit}
                initialData={selectedLead}
            />

        </div>
    );
};

export default LeadManagementList;
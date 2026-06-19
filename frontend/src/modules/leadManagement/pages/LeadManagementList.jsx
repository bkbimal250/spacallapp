import React, { useEffect, useState, useMemo, useCallback, memo } from 'react';
import { useLocation } from 'react-router-dom';
import { leadManagementAPI } from '../api';
import Table from '../../../shared/components/Table';
import Badge from '../../../shared/components/Badge';
import Pagination from '../../../shared/components/Pagination';
import { formatDate } from '../../../shared/utils/formatDate';
import { useAuth } from '../../../shared/hooks/useAuth';
import { branchesAPI } from '../../branches/api';
import { Target, Filter, Edit, Trash2 } from 'lucide-react';
import LeadFilter from '../components/LeadFilter';
import StatsCard from '../../dashboard/components/StatsCard';
import LeadForm from '../components/LeadForm'
import { PageSpinner, ContentSkeleton, SubtleLoader, ButtonSpinner } from '../../../shared/components/loaders';

const LeadManagementList = () => {
    const { user } = useAuth();
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const initialBranch = queryParams.get('branch') || '';
    const initialStatus = queryParams.get('status') || '';
    const initialSearch = queryParams.get('search') || '';

    const [leads, setLeads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 100;

    const [filters, setFilters] = useState({
        branch: initialBranch,
        status: initialStatus,
        search: initialSearch
    });

    const [isFormOpen, setIsFormOpen] = useState(false);
    const [selectedLead, setSelectedLead] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [updatingId, setUpdatingId] = useState(null);
    const [branches, setBranches] = useState([]);

    const isSuperAdmin = user?.role === 'super_admin';
    const isAdmin = user?.role === 'admin' || isSuperAdmin;

    useEffect(() => {
        const fetchBranches = async () => {
            if (!isAdmin) return;
            try {
                const response = await branchesAPI.getBranches({ all: true });
                const data = response.data.results || response.data;
                setBranches(data.map(b => ({
                    value: b.id,
                    label: b.spa_name,
                    searchText: [
                        b.spa_name,
                        b.code,
                        b.city,
                        b.area,
                        b.state,
                        b.address,
                        b.phone,
                        b.branch_group_name,
                    ].filter(Boolean).join(' ')
                })));
            } catch (err) {
                console.error("Failed to fetch branches", err);
            }
        };
        fetchBranches();
    }, [isAdmin]);

    const fetchLeads = useCallback(async (currentFilters = {}, currentPage = 1, isBackground = false) => {
        if (!isBackground) setLoading(true);
        else setRefreshing(true);
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
            else setRefreshing(false);
        }
    }, []); // Removed pageSize from dependency array as it's a constant

    useEffect(() => {
        fetchLeads(filters, page);

        const intervalId = setInterval(() => {
            fetchLeads(filters, page, true);
        }, 10000);

        return () => clearInterval(intervalId);
    }, [filters, page, fetchLeads]);

    const handleFilterChange = useCallback((newFilters) => {
        setFilters(newFilters);
        setPage(1);
    }, []);

    const handlePageChange = useCallback((newPage) => {
        setPage(newPage);
    }, []);

    const handleEditLead = useCallback((lead) => {
        setSelectedLead(lead);
        setIsFormOpen(true);
    }, []);

    const handleDeleteLead = useCallback(async (id) => {
        if (window.confirm('Are you sure you want to delete this lead?')) {
            try {
                await leadManagementAPI.deleteLead(id);
                fetchLeads(filters, page);
            } catch (error) {
                console.error("Failed to delete lead", error);
                alert("Failed to delete lead.");
            }
        }
    }, [filters, page, fetchLeads]);

    const handleFormSubmit = useCallback(async (data) => {
        setSubmitting(true);
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
        } finally {
            setSubmitting(false);
        }
    }, [selectedLead, filters, page, fetchLeads]);

    const handleUpdateStatus = useCallback(async (id, newStatus) => {
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
    }, [filters, page, fetchLeads]);

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
    ], [isSuperAdmin, updatingId, getStatusColor, handleUpdateStatus, handleEditLead, handleDeleteLead]);

    const leadStats = useMemo(() => [
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
    ], [totalCount, leads.length]);

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

            <LeadFilter
                filters={filters}
                onFilter={handleFilterChange}
                isAdmin={isAdmin}
                branches={branches}
            />

            <div className="bg-card border border-border rounded-2xl shadow-lg overflow-hidden">

                <SubtleLoader isVisible={refreshing} />
                <div className="max-h-[700px] overflow-y-auto">

                    {loading && leads.length === 0 ? (
                        <PageSpinner message="Loading leads..." />
                    ) : loading && leads.length > 0 ? (
                        <ContentSkeleton rows={10} />
                    ) : (
                        <>
                            {leads.length === 0 ? (
                                <div className="p-12 text-center text-text-secondary">
                                    No leads found.
                                </div>
                            ) : (
                                <Table columns={columns} data={leads} />
                            )}
                        </>
                    )}

                </div>

                {!loading && totalCount > 0 && Math.ceil(totalCount / pageSize) > 1 && (
                    <div className="mt-4 px-4 pb-4">
                        <Pagination
                            currentPage={page}
                            totalPages={Math.ceil(totalCount / pageSize)}
                            onPageChange={handlePageChange}
                            totalCount={totalCount}
                            pageSize={pageSize}
                        />
                    </div>
                )}

            </div>

            <LeadForm
                isOpen={isFormOpen}
                onClose={() => setIsFormOpen(false)}
                onSubmit={handleFormSubmit}
                initialData={selectedLead}
                loading={submitting}
            />

        </div>
    );
};

export default memo(LeadManagementList);

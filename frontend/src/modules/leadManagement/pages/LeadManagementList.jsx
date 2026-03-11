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
import { Plus, Edit, Trash2 } from 'lucide-react';
import LeadForm from '../components/LeadForm';

const LeadManagementList = () => {
    const { user } = useAuth();
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const initialBranch = queryParams.get('branch') || '';

    const [leads, setLeads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 50;

    const [filters, setFilters] = useState({
        branch: initialBranch,
        status: '',
        search: ''
    });

    const [isFormOpen, setIsFormOpen] = useState(false);
    const [selectedLead, setSelectedLead] = useState(null);
    const [updatingId, setUpdatingId] = useState(null);

    const isSuperAdmin = user?.role === 'super_admin';

    const fetchLeads = async (currentFilters = {}, currentPage = 1, isBackground = false) => {
        if (!isBackground) setLoading(true);
        try {
            const apiFilters = { page: currentPage };
            if (currentFilters.branch) {
                if (currentFilters.branch === 'null') {
                    apiFilters.calllog__branch__isnull = 'True';
                } else {
                    apiFilters.calllog__branch = currentFilters.branch;
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

    const getStatusColor = (status) => {
        switch (status) {
            case 'pending': return 'gray';
            case 'ringing': return 'blue';
            case 'coming': return 'purple';
            case 'interested': return 'green';
            case 'not_interested': return 'red';
            default: return 'gray';
        }
    };

    const columns = [
        {
            header: 'Number / Contact',
            render: (row) => (
                <div className="flex flex-col">
                    <span className="font-semibold text-gray-900">{row.phone_number || 'Unknown'}</span>
                    <span className="text-xs text-gray-500">{row.contact_name || 'No Contact'}</span>
                </div>
            )
        },
        { header: 'Branch', accessor: 'branch_name' },

        {
            header: 'Details',
            render: (row) => (
                <div className="flex flex-col max-w-xs">
                    {row.booking_date && <span className="text-xs text-indigo-600 font-medium whitespace-nowrap">Booking: {formatDate(row.booking_date, 'MMM dd, yyyy')}</span>}
                    {row.remarks && <span className="text-xs text-gray-500 truncate" title={row.remarks}>{row.remarks}</span>}
                    {!row.booking_date && !row.remarks && <span className="text-xs text-gray-400 italic">No details</span>}
                </div>
            )
        },
        {
            header: 'Time',
            render: (row) => formatDate(row.created_at, 'MMM dd, HH:mm')
        },
        {
            header: 'Update Status',
            render: (row) => (
                <select
                    className="block w-full px-2 py-1 text-xs border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 cursor-pointer"
                    value={row.status}
                    disabled={updatingId === row.id}
                    onChange={(e) => handleUpdateStatus(row.id, e.target.value)}
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
                        onClick={() => handleEditLead(row)}
                        className="p-1 text-indigo-600 hover:bg-indigo-50 rounded"
                        title="Edit Lead"
                    >
                        <Edit size={16} />
                    </button>
                    {isSuperAdmin && (
                        <button
                            onClick={() => handleDeleteLead(row.id)}
                            className="p-1 text-red-600 hover:bg-red-50 rounded"
                            title="Delete Lead"
                        >
                            <Trash2 size={16} />
                        </button>
                    )}
                </div>
            )
        }
    ];

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-semibold text-gray-900">Lead Management</h1>
            </div>

            <div className="bg-white shadow rounded-lg p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex flex-col">
                        <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">Search Contact/Number</label>
                        <Input
                            placeholder="Type to search..."
                            value={filters.search}
                            onChange={(e) => handleFilterChange('search', e.target.value)}
                        />
                    </div>
                    <div className="flex flex-col">
                        <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">Lead Status</label>
                        <select
                            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
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
                    <div className="flex flex-col justify-end">
                        <Button variant="outline" onClick={() => handleFilterChange('status', '') && handleFilterChange('search', '')} className="border-gray-300 text-gray-700 hover:bg-gray-50 flex-none h-10">Clear Filters</Button>
                    </div>
                </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden flex flex-col">
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-12 text-center text-gray-500">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto mb-4"></div>
                            Loading leads...
                        </div>
                    ) : (
                        <Table
                            columns={columns}
                            data={leads}
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
                isOpen={isFormOpen}
                onClose={() => setIsFormOpen(false)}
                onSubmit={handleFormSubmit}
                initialData={selectedLead}
            />
        </div>
    );
};

export default LeadManagementList;

import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { branchesAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import BranchForm from '../components/BranchForm';
import GroupForm from '../components/GroupForm';
import BranchFilter from '../components/BranchFilter';
import BranchStats from '../components/BranchStats';
import Pagination from '../../../shared/components/Pagination';
import { addItemToList, removeItemFromList, updateItemInList } from '../../../shared/utils/listState';

import {
    AlertTriangle,
    CheckCircle2,
    Edit,
    Eye,
    Layers,
    Trash2,
    Plus,
    MapPin,
    TrendingUp,
    PhoneCall
} from 'lucide-react';

const BranchList = () => {

    const navigate = useNavigate();

    const [branches, setBranches] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isGroupModalOpen, setIsGroupModalOpen] = useState(false);
    const [editingBranch, setEditingBranch] = useState(null);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [stats, setStats] = useState({ total: 0, active: 0, inactive: 0 });
    const [rowAction, setRowAction] = useState({});
    const [saving, setSaving] = useState(false);

    const pageSize = 100;

    const fetchBranches = useCallback(async (currentFilters = {}, currentPage = 1) => {
        setLoading(true);
        try {
            const response = await branchesAPI.getBranches({
                ...currentFilters,
                page: currentPage
            });

            if (response.data.results) {
                setBranches(response.data.results);
                setTotalCount(response.data.count);
            } else {
                setBranches(response.data);
                setTotalCount(response.data.length);
            }
        } catch (error) {
            console.error("Failed to fetch branches", error);
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchStats = useCallback(async () => {
        try {
            const response = await branchesAPI.getBranches({ all: true });
            const allBranches = response.data.results || response.data || [];

            const total = allBranches.length;
            const active = allBranches.filter(b => b.is_active).length;
            const inactive = total - active;

            setStats({ total, active, inactive });

        } catch (error) {
            console.error("Failed to fetch branch stats", error);
        }
    }, []);

    useEffect(() => {
        fetchStats();
    }, [fetchStats]);

    useEffect(() => {
        fetchBranches(filters, page);
    }, [filters, page, fetchBranches]);

    const handleFilter = useCallback((newFilters) => {
        setFilters(newFilters);
        setPage(1);
    }, []);

    const handlePageChange = useCallback((newPage) => {
        setPage(newPage);
    }, []);

    const handleCreate = () => {
        setEditingBranch(null);
        setIsModalOpen(true);
    };

    const setActionLoading = (id, action, value) => {
        setRowAction(prev => ({ ...prev, [`${action}:${id}`]: value }));
    };

    const isActionLoading = (id, action) => Boolean(rowAction[`${action}:${id}`]);

    const branchMatchesFilters = (branch) => {
        if (!branch) return false;
        if (filters.group && branch.branch_group !== filters.group) return false;
        if (filters.status !== undefined && filters.status !== '' && String(Boolean(branch.is_active)) !== String(filters.status)) return false;
        if (filters.city && !String(branch.city || branch.location_city_name || '').toLowerCase().includes(String(filters.city).toLowerCase())) return false;
        if (filters.state && !String(branch.state || branch.location_state_name || '').toLowerCase().includes(String(filters.state).toLowerCase())) return false;
        if (filters.area && !String(branch.area || branch.location_area_name || '').toLowerCase().includes(String(filters.area).toLowerCase())) return false;
        if (filters.search) {
            const haystack = [
                branch.spa_name,
                branch.code,
                branch.city,
                branch.area,
                branch.state,
                branch.address,
                branch.phone,
                branch.branch_group_name,
            ].filter(Boolean).join(' ').toLowerCase();
            if (!haystack.includes(String(filters.search).toLowerCase())) return false;
        }
        return true;
    };

    const adjustStatsForCreate = (branch) => {
        setStats(prev => ({
            total: prev.total + 1,
            active: prev.active + (branch.is_active ? 1 : 0),
            inactive: prev.inactive + (branch.is_active ? 0 : 1),
        }));
    };

    const adjustStatsForDelete = (branch) => {
        if (!branch) return;
        setStats(prev => ({
            total: Math.max(0, prev.total - 1),
            active: Math.max(0, prev.active - (branch?.is_active ? 1 : 0)),
            inactive: Math.max(0, prev.inactive - (branch?.is_active ? 0 : 1)),
        }));
    };

    const adjustStatsForUpdate = (before, after) => {
        if (!before || !after || Boolean(before.is_active) === Boolean(after.is_active)) return;
        setStats(prev => ({
            ...prev,
            active: Math.max(0, prev.active + (after.is_active ? 1 : -1)),
            inactive: Math.max(0, prev.inactive + (after.is_active ? -1 : 1)),
        }));
    };

    const handleEdit = async (branch) => {
        try {
            const response = await branchesAPI.getBranch(branch.id);
            setEditingBranch(response.data);
            setIsModalOpen(true);
        } catch (error) {
            console.error('Failed to load branch details', error);
            window.alert('Could not load branch details for edit.');
        }
    };

    const handleDelete = async (id) => {

        if (window.confirm("Are you sure you want to delete this branch?")) {

            const deletedBranch = branches.find(branch => branch.id === id);
            setActionLoading(id, 'delete', true);
            try {

                await branchesAPI.deleteBranch(id);
                setBranches(prev => removeItemFromList(prev, id));
                setTotalCount(prev => Math.max(0, prev - 1));
                adjustStatsForDelete(deletedBranch);
                setEditingBranch(prev => prev?.id === id ? null : prev);
                if (branches.length === 1 && page > 1) {
                    setPage(prev => Math.max(1, prev - 1));
                }

            } catch (error) {

                console.error("Failed to delete branch", error);
                window.alert("Failed to delete branch.");
            } finally {
                setActionLoading(id, 'delete', false);

            }

        }

    };

    const handleSubmit = async (data) => {
        setSaving(true);
        try {
            if (editingBranch) {
                const response = await branchesAPI.updateBranch(editingBranch.id, data);
                const updatedBranch = response.data;
                setBranches(prev => updateItemInList(prev, updatedBranch));
                setEditingBranch(prev => prev?.id === editingBranch.id ? { ...prev, ...updatedBranch } : prev);
                adjustStatsForUpdate(editingBranch, updatedBranch);
            } else {
                const response = await branchesAPI.createBranch(data);
                if (branchMatchesFilters(response.data)) {
                    setBranches(prev => addItemToList(prev, response.data));
                    setTotalCount(prev => prev + 1);
                } else {
                    window.alert("Created successfully. It may not appear because current filters are active.");
                }
                adjustStatsForCreate(response.data);
            }

            setIsModalOpen(false);
        } catch (error) {
            console.error("Failed to save branch", error);
            window.alert("Failed to save branch.");
        } finally {
            setSaving(false);
        }
    };

    const handleGroupSubmit = async (data) => {
        try {
            await branchesAPI.createGroup(data);
            setIsGroupModalOpen(false);
        } catch (error) {
            console.error("Failed to save branch group", error);
            window.alert("Failed to save branch group.");
        }
    };

    const hasLinkedLocation = (branch) => Boolean(
        branch.location_state &&
        branch.location_city &&
        branch.location_area
    );

    const hasLocationGroup = (branch) => Boolean(branch.location_group);

    const LinkedBadge = ({ ok, label, missingLabel, onClick }) => {
        if (ok) {
            return (
                <span className="inline-flex items-center gap-1.5 rounded-md bg-success/10 px-2 py-1 text-xs font-semibold text-success">
                    <CheckCircle2 size={14} />
                    {label}
                </span>
            );
        }

        return (
            <button
                type="button"
                onClick={onClick}
                className="inline-flex items-center gap-1.5 rounded-md bg-warning/10 px-2 py-1 text-xs font-semibold text-warning hover:bg-warning/20"
                title={missingLabel}
            >
                <AlertTriangle size={14} />
                {missingLabel}
            </button>
        );
    };

    const columns = [

        { header: 'Spa Name', accessor: 'spa_name' },
        { header: 'Branch Code', accessor: 'code' },
        { header: 'City', accessor: 'city' },
        { header: 'Branch Group Name', accessor: 'branch_group_name' },

        {
            header: 'Location',
            render: (row) => (
                <div className="flex items-center text-text-secondary">
                    <MapPin size={14} className="mr-1 text-primary" />
                    {` ${row.area},  ${row.city}, ${row.state}`}
                </div>
            )
        },

        {
            header: 'Linked Location',
            render: (row) => (
                <LinkedBadge
                    ok={hasLinkedLocation(row)}
                    label="Added"
                    missingLabel="Need Location"
                    onClick={() => handleEdit(row)}
                />
            )
        },

        {
            header: 'Location Group',
            render: (row) => (
                <div className="flex flex-col gap-1">
                    <LinkedBadge
                        ok={hasLocationGroup(row)}
                        label="Added"
                        missingLabel="Need Group"
                        onClick={() => handleEdit(row)}
                    />
                    {row.location_group_name && (
                        <span className="inline-flex items-center gap-1 text-xs text-text-secondary">
                            <Layers size={12} />
                            {row.location_group_name}
                        </span>
                    )}
                </div>
            )
        },

        {
            header: 'Operating Hours',
            render: (row) => (
                <span
                    className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold ${
                        row.operating_hours_configured
                            ? 'bg-success/10 text-success'
                            : 'bg-warning/10 text-warning'
                    }`}
                >
                    {row.operating_hours_configured ? 'Configured' : 'Not Configured'}
                </span>
            )
        },

        {
            header: 'Status',
            render: (row) => (
                <span
                    className={`px-2 py-0.5 text-xs font-semibold rounded-md
                    ${row.is_active
                            ? "bg-success/10 text-success"
                            : "bg-danger/10 text-danger"
                        }`}
                >
                    {row.is_active ? 'Active' : 'Inactive'}
                </span>
            )
        },

        {
            header: 'Actions',
            render: (row) => (

                <div className="flex gap-2">

                    {/* View */}
                    <button
                        onClick={() => navigate(`/branches/${row.id}`)}
                        className="p-1 rounded-md text-text-secondary hover:bg-background"
                        title="View Branch"
                    >
                        <Eye size={16} />
                    </button>

                    {/* Call Logs */}
                    <button
                        onClick={() => navigate(`/calllogs/details?branch=${row.id}`)}
                        className="p-1 rounded-md text-primary hover:bg-primary/10"
                        title="View Call Logs"
                    >
                        <PhoneCall size={16} />
                    </button>

                    {/* Analytics */}
                    <button
                        onClick={() => navigate(`/analytics?branch=${row.id}`)}
                        className="p-1 rounded-md text-info hover:bg-info/10"
                        title="View Analytics"
                    >
                        <TrendingUp size={16} />
                    </button>

                    {/* Edit */}
                    <button
                        onClick={() => handleEdit(row)}
                        disabled={isActionLoading(row.id, 'delete')}
                        className="p-1 rounded-md text-warning hover:bg-warning/10"
                        title="Edit"
                    >
                        <Edit size={16} />
                    </button>

                    {/* Delete */}
                    <button
                        onClick={() => handleDelete(row.id)}
                        disabled={isActionLoading(row.id, 'delete')}
                        className="p-1 rounded-md text-danger hover:bg-danger/10 disabled:opacity-50"
                        title="Delete"
                    >
                        <Trash2 size={16} />
                    </button>

                </div>
            )
        }

    ];

    return (
        <div className="space-y-6">
            <div className="flex justify-end gap-3">
                <Button
                    variant="secondary"
                    onClick={() => setIsGroupModalOpen(true)}
                    className="flex items-center gap-2 text-sm"
                >
                    <Plus size={14} />
                    Add Group
                </Button>

                <Button
                    onClick={handleCreate}
                    className="flex items-center gap-2 text-sm"
                >
                    <Plus size={14} />
                    Add Branch
                </Button>
            </div>
            {/* STATS */}
            <BranchStats stats={stats} />




            <div className="bg-card border border-border rounded-2xl p-6">

                <BranchFilter
                    onFilter={handleFilter}
                    externalFilters={filters}
                />

            </div>

            {/* TABLE */}

            <div className="bg-card border border-border rounded-2xl overflow-hidden flex flex-col">

                <div className="overflow-x-auto">

                    {loading ? (

                        <div className="p-12 text-center text-text-secondary">

                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>

                            Loading branches...

                        </div>

                    ) : (

                        <Table
                            columns={columns}
                            data={branches}
                        />

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

            {/* FORM MODAL */}

            <BranchForm
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleSubmit}
                initialData={editingBranch}
                saving={saving}
            />

            {/* GROUP FORM MODAL */}

            <GroupForm
                isOpen={isGroupModalOpen}
                onClose={() => setIsGroupModalOpen(false)}
                onSubmit={handleGroupSubmit}
            />

        </div>
    );
};

export default BranchList;

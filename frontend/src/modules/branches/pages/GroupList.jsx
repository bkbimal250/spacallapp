import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { branchesAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import GroupForm from '../components/GroupForm';
import BranchAssignmentModal from '../components/BranchAssignmentModal';
import ViewGroupModal from '../components/ViewGroupModal';
import BranchGroupStats from '../components/BranchGroupStats';
import BranchGroupListFilter from '../components/BranchGroupListFilter';
import { addItemToList, removeItemFromList, updateItemInList } from '../../../shared/utils/listState';
import {
    Edit,
    Trash2,
    Plus,
    Layers,
    MapPin,
    Users,
    Eye
} from 'lucide-react';

const GroupList = () => {

    const [groups, setGroups] = useState([]);
    const [branches, setBranches] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
    const [isViewModalOpen, setIsViewModalOpen] = useState(false);
    const [editingGroup, setEditingGroup] = useState(null);
    const [viewingGroup, setViewingGroup] = useState(null);
    const [assigningGroup, setAssigningGroup] = useState(null);
    const [filters, setFilters] = useState({});
    const [rowAction, setRowAction] = useState({});
    const [saving, setSaving] = useState(false);

    const fetchGroups = useCallback(async (currentFilters = filters) => {
        setLoading(true);
        try {
            const [groupRes, branchRes] = await Promise.all([
                branchesAPI.getGroups({ ...currentFilters }),
                branchesAPI.getBranches({ all: true })
            ]);
            
            setGroups(groupRes.data.results || groupRes.data || []);
            setBranches(branchRes.data.results || branchRes.data || []);
        } catch (error) {
            console.error("Failed to fetch branch data", error);
        } finally {
            setLoading(false);
        }
    }, []);

    const groupStats = useMemo(() => {
        const totalGroups = groups.length;
        const totalBranches = branches.length;
        const assignedBranches = branches.filter(b => b.branch_group !== null).length;
        const unassignedBranches = totalBranches - assignedBranches;

        return {
            totalGroups,
            assignedBranches,
            unassignedBranches
        };
    }, [groups, branches]);

    useEffect(() => {
        fetchGroups();
    }, [fetchGroups]);

    const handleFilter = useCallback((newFilters) => {
        setFilters(newFilters);
        fetchGroups(newFilters);
    }, [fetchGroups]);

    const handleCreate = () => {
        setEditingGroup(null);
        setIsModalOpen(true);
    };

    const setActionLoading = (id, action, value) => {
        setRowAction(prev => ({ ...prev, [`${action}:${id}`]: value }));
    };

    const isActionLoading = (id, action) => Boolean(rowAction[`${action}:${id}`]);

    const groupMatchesFilters = (group) => {
        if (!group) return false;
        if (filters.status && String(Boolean(group.is_active)) !== String(filters.status)) return false;
        if (filters.search && !String(group.name || '').toLowerCase().includes(String(filters.search).toLowerCase())) return false;
        return true;
    };

    const handleEdit = (group) => {
        setEditingGroup(group);
        setIsModalOpen(true);
    };

    const handleView = (group) => {
        setViewingGroup(group);
        setIsViewModalOpen(true);
    };

    const handleManageBranches = (group) => {
        setAssigningGroup(group);
        setIsAssignModalOpen(true);
    };

    const handleDelete = async (id) => {
        if (window.confirm("Are you sure you want to delete this group? Branches in this group will be unassigned.")) {
            setActionLoading(id, 'delete', true);
            try {
                await branchesAPI.deleteGroup(id);
                setGroups(prev => removeItemFromList(prev, id));
                setBranches(prev => prev.map(branch =>
                    branch.branch_group === id
                        ? { ...branch, branch_group: null, branch_group_name: null }
                        : branch
                ));
                setEditingGroup(prev => prev?.id === id ? null : prev);
                setViewingGroup(prev => prev?.id === id ? null : prev);
                setAssigningGroup(prev => prev?.id === id ? null : prev);
            } catch (error) {
                console.error("Failed to delete group", error);
                window.alert("Failed to delete branch group.");
            } finally {
                setActionLoading(id, 'delete', false);
            }
        }
    };

    const handleSubmit = async (data) => {
        setSaving(true);
        try {
            if (editingGroup) {
                const response = await branchesAPI.updateGroup(editingGroup.id, data);
                const updated = response.data;
                setGroups(prev => updateItemInList(prev, updated));
                setBranches(prev => prev.map(branch =>
                    branch.branch_group === updated.id
                        ? { ...branch, branch_group_name: updated.name }
                        : branch
                ));
                setEditingGroup(prev => prev?.id === updated.id ? { ...prev, ...updated } : prev);
                setViewingGroup(prev => prev?.id === updated.id ? { ...prev, ...updated } : prev);
                setAssigningGroup(prev => prev?.id === updated.id ? { ...prev, ...updated } : prev);
            } else {
                const response = await branchesAPI.createGroup(data);
                const created = { branch_count: 0, ...response.data };
                if (groupMatchesFilters(created)) {
                    setGroups(prev => addItemToList(prev, created));
                } else {
                    window.alert("Created successfully. It may not appear because current filters are active.");
                }
            }
            setIsModalOpen(false);
        } catch (error) {
            console.error("Failed to save branch group", error);
            window.alert("Failed to save branch group.");
        } finally {
            setSaving(false);
        }
    };

    const handleAssignBranches = (selectedIds) => {
        if (!assigningGroup) return;
        const selectedSet = new Set(selectedIds);
        const updatedGroup = {
            ...assigningGroup,
            branch_count: selectedIds.length,
        };
        setGroups(prev => updateItemInList(prev, updatedGroup));
        setBranches(prev => prev.map(branch => {
            if (selectedSet.has(branch.id)) {
                return {
                    ...branch,
                    branch_group: assigningGroup.id,
                    branch_group_name: assigningGroup.name,
                };
            }
            if (branch.branch_group === assigningGroup.id) {
                return {
                    ...branch,
                    branch_group: null,
                    branch_group_name: null,
                };
            }
            return branch;
        }));
        setViewingGroup(prev => prev?.id === assigningGroup.id ? { ...prev, ...updatedGroup } : prev);
        setAssigningGroup(prev => prev?.id === assigningGroup.id ? { ...prev, ...updatedGroup } : prev);
    };

    const columns = [
        {
            header: 'Group Name',
            render: (row) => (
                <div className="flex items-center space-x-2">
                    <Layers size={18} className="text-primary" />
                    <span className="font-medium text-text-primary">{row.name}</span>
                </div>
            )
        },
        {
            header: 'Assigned Branches',
            render: (row) => (
                <div className="flex items-center text-text-secondary">
                    <MapPin size={14} className="mr-1 text-info" />
                    <span>{row.branch_count} Branches</span>
                </div>
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

                    <button
                        onClick={() => handleView(row)}
                        className='p-1 rounded-md text-info hover:bg-info/10 flex items-center gap-1 transition-all'
                        title='View Group Details'
                    >
                        <Eye className='mr-1 text-info' size={16} />
                        <span className="text-xs font-medium">View</span>
                    </button>
                    <button
                        onClick={() => handleManageBranches(row)}
                        className="p-1 rounded-md text-info hover:bg-info/10 flex items-center gap-1"
                        title="Manage Branches"
                    >
                        <Users size={16} />
                        <span className="text-xs font-medium">Manage</span>
                    </button>
                    <button
                        onClick={() => handleEdit(row)}
                        disabled={isActionLoading(row.id, 'delete')}
                        className="p-1 rounded-md text-warning hover:bg-warning/10 disabled:opacity-50"
                        title="Edit"
                    >
                        <Edit size={16} />
                    </button>
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
            <BranchGroupStats stats={groupStats} />

            <BranchGroupListFilter onFilter={handleFilter} />

            <div className="flex justify-end pr-1">
                <Button
                    onClick={handleCreate}
                    className="flex items-center gap-2 text-sm"
                >
                    <Plus size={14} />
                    Add Group
                </Button>
            </div>

            <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-12 text-center text-text-secondary">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                            Loading groups...
                        </div>
                    ) : (
                        <Table
                            columns={columns}
                            data={groups}
                        />
                    )}
                </div>
            </div>

            <GroupForm
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleSubmit}
                initialData={editingGroup}
                saving={saving}
            />

            <BranchAssignmentModal
                isOpen={isAssignModalOpen}
                onClose={() => setIsAssignModalOpen(false)}
                group={assigningGroup}
                onAssign={handleAssignBranches}
            />

            <ViewGroupModal
                isOpen={isViewModalOpen}
                onClose={() => setIsViewModalOpen(false)}
                group={viewingGroup}
                branches={branches}
            />
        </div>
    );
};

export default GroupList;

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { branchesAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import BranchForm from '../components/BranchForm';
import BranchFilter from '../components/BranchFilter';
import BranchStats from '../components/BranchStats';
import Pagination from '../../../shared/components/Pagination';

import {
    Edit,
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
    const [editingBranch, setEditingBranch] = useState(null);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [stats, setStats] = useState({ total: 0, active: 0, inactive: 0 });

    const pageSize = 50;

    const fetchBranches = async (currentFilters = {}, currentPage = 1) => {

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
    };

    const fetchStats = async () => {
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
    };

    useEffect(() => {
        fetchBranches(filters, page);
        fetchStats();
    }, [filters, page]);

    const handleFilter = (newFilters) => {
        setFilters(newFilters);
        setPage(1);
    };

    const handlePageChange = (newPage) => {
        setPage(newPage);
    };

    const handleCreate = () => {
        setEditingBranch(null);
        setIsModalOpen(true);
    };

    const handleEdit = (branch) => {
        setEditingBranch(branch);
        setIsModalOpen(true);
    };

    const handleDelete = async (id) => {

        if (window.confirm("Are you sure you want to delete this branch?")) {

            try {

                await branchesAPI.deleteBranch(id);
                fetchBranches(filters, page);
                fetchStats();

            } catch (error) {

                console.error("Failed to delete branch", error);

            }

        }

    };

    const handleSubmit = async (data) => {

        try {

            if (editingBranch) {
                await branchesAPI.updateBranch(editingBranch.id, data);
            } else {
                await branchesAPI.createBranch(data);
            }

            setIsModalOpen(false);
            fetchBranches(filters, page);
            fetchStats();

        } catch (error) {

            console.error("Failed to save branch", error);

        }

    };

    const columns = [

        { header: 'Spa Name', accessor: 'spa_name' },
        { header: 'Branch Code', accessor: 'code' },
        { header: 'Area', accessor: 'area' },
        { header: 'Postal Code', accessor: 'postal_code' },

        {
            header: 'Location',
            render: (row) => (
                <div className="flex items-center text-text-secondary">
                    <MapPin size={14} className="mr-1 text-primary" />
                    {`${row.city}, ${row.state}`}
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
                        className="p-1 rounded-md text-warning hover:bg-warning/10"
                        title="Edit"
                    >
                        <Edit size={16} />
                    </button>

                    {/* Delete */}
                    <button
                        onClick={() => handleDelete(row.id)}
                        className="p-1 rounded-md text-danger hover:bg-danger/10"
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

            {/* HEADER */}

            <div className="flex justify-between items-center">

                <h1 className="text-2xl font-semibold text-text-primary">
                    Branches
                </h1>

                <Button
                    onClick={handleCreate}
                    className="flex items-center gap-2"
                >
                    <Plus size={16} />
                    Add Branch
                </Button>

            </div>

            {/* STATS */}
            <BranchStats stats={stats} />

            {/* FILTER */}

            <div className="bg-card border border-border rounded-2xl p-6">

                <BranchFilter onFilter={handleFilter} />

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

                {!loading && totalCount > 0 && Math.ceil(totalCount / pageSize) > 1 && (

                    <Pagination
                        currentPage={page}
                        totalPages={Math.ceil(totalCount / pageSize)}
                        onPageChange={handlePageChange}
                    />

                )}

            </div>

            {/* FORM MODAL */}

            <BranchForm
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleSubmit}
                initialData={editingBranch}
            />

        </div>
    );
};

export default BranchList;
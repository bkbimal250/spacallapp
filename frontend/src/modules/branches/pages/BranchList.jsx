import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { branchesAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import BranchForm from '../components/BranchForm';
import BranchFilter from '../components/BranchFilter';
import Pagination from '../../../shared/components/Pagination';
import { Edit, Trash2, Plus, MapPin, TrendingUp } from 'lucide-react';

const BranchList = () => {
    const navigate = useNavigate();
    const [branches, setBranches] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingBranch, setEditingBranch] = useState(null);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 20;

    const fetchBranches = async (currentFilters = {}, currentPage = 1) => {
        setLoading(true);
        try {
            const response = await branchesAPI.getBranches({ ...currentFilters, page: currentPage });
            // The API returns paginated data if configured, otherwise use total count logic
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

    useEffect(() => {
        fetchBranches(filters, page);
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
                <div className="flex items-center text-gray-500">
                    <MapPin size={14} className="mr-1" />
                    {`${row.city}, ${row.state}`}
                </div>
            )
        },
        {
            header: 'Status',
            render: (row) => (
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${row.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {row.is_active ? 'Active' : 'Inactive'}
                </span>
            )
        },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex space-x-2">
                    <button
                        onClick={() => navigate(`/analytics?branch=${row.id}`)}
                        className="text-sky-600 hover:text-sky-800 p-1 hover:bg-sky-50 rounded transition-colors"
                        title="View Analytics"
                    >
                        <TrendingUp size={16} />
                    </button>
                    <button onClick={() => handleEdit(row)} className="text-blue-600 hover:text-blue-800 p-1 hover:bg-blue-50 rounded transition-colors" title="Edit">
                        <Edit size={16} />
                    </button>
                    <button onClick={() => handleDelete(row.id)} className="text-red-600 hover:text-red-800 p-1 hover:bg-red-50 rounded transition-colors" title="Delete">
                        <Trash2 size={16} />
                    </button>
                </div>
            ),
        },
    ];

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-semibold text-gray-900">Branches</h1>
                <Button onClick={handleCreate} className="flex items-center space-x-2">
                    <Plus size={16} />
                    <span>Add Branch</span>
                </Button>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
                <BranchFilter onFilter={handleFilter} />
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden flex flex-col">
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-12 text-center text-gray-500">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500 mx-auto mb-4"></div>
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

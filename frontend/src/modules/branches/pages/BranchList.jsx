import React, { useEffect, useState } from 'react';
import { branchesAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import BranchForm from '../components/BranchForm';
import { Edit, Trash2, Plus, MapPin, Phone } from 'lucide-react';

const BranchList = () => {
    const [branches, setBranches] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingBranch, setEditingBranch] = useState(null);

    const fetchBranches = async () => {
        setLoading(true);
        try {
            const response = await branchesAPI.getBranches();
            setBranches(response.data?.results || response.data || []);
        } catch (error) {
            console.error("Failed to fetch branches", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBranches();
    }, []);

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
                fetchBranches();
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
            fetchBranches();
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
                    <button onClick={() => handleEdit(row)} className="text-blue-600 hover:text-blue-800">
                        <Edit size={16} />
                    </button>
                    <button onClick={() => handleDelete(row.id)} className="text-red-600 hover:text-red-800">
                        <Trash2 size={16} />
                    </button>
                </div>
            ),
        },
    ];

    if (loading) return <div>Loading...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-semibold text-gray-900">Branches</h1>
                <Button onClick={handleCreate} className="flex items-center space-x-2">
                    <Plus size={16} />
                    <span>Add Branch</span>
                </Button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
                <Table
                    columns={columns}
                    data={branches}
                />
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

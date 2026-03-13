import React, { useEffect, useState } from 'react';
import { usersAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import UserForm from '../components/UserForm';
import UserFilter from '../components/UserFilter';
import Pagination from '../../../shared/components/Pagination';
import { Edit, Trash2, Plus } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';

const UserList = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 50;

    const fetchUsers = async (currentFilters = {}, currentPage = 1) => {
        setLoading(true);
        try {
            const response = await usersAPI.getUsers({ ...currentFilters, page: currentPage });

            if (response.data.results) {
                setUsers(response.data.results);
                setTotalCount(response.data.count);
            } else {
                setUsers(response.data);
                setTotalCount(response.data.length);
            }
        } catch (error) {
            console.error("Failed to fetch users", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers(filters, page);
    }, [filters, page]);

    const handleFilter = (newFilters) => {
        setFilters(newFilters);
        setPage(1);
    };

    const handlePageChange = (newPage) => {
        setPage(newPage);
    };

    const handleCreate = () => {
        setEditingUser(null);
        setIsModalOpen(true);
    };

    const handleEdit = (user) => {
        setEditingUser(user);
        setIsModalOpen(true);
    };

    const handleDelete = async (id) => {
        if (window.confirm("Are you sure you want to delete this user?")) {
            try {
                await usersAPI.deleteUser(id);
                fetchUsers(filters, page);
            } catch (error) {
                console.error("Failed to delete user", error);
            }
        }
    };

    const handleSubmit = async (data) => {
        try {
            if (editingUser) {
                await usersAPI.updateUser(editingUser.id, data);
            } else {
                await usersAPI.createUser(data);
            }

            setIsModalOpen(false);
            fetchUsers(filters, page);

        } catch (error) {
            console.error("Failed to save user", error);
            alert("Failed to save user");
        }
    };

    const columns = [
        {
            header: 'Name',
            render: (row) => (
                <span className="text-text-primary font-medium">
                    {row.full_name}
                </span>
            )
        },
        {
            header: 'Email',
            render: (row) => (
                <span className="text-text-secondary">
                    {row.email}
                </span>
            )
        },
        {
            header: 'Role',
            render: (row) => (
                <Badge
                    variant={
                        row.role === 'super_admin'
                            ? 'danger'
                            : row.role === 'admin'
                                ? 'primary'
                                : 'success'
                    }
                >
                    {row.role.replace('_', ' ')}
                </Badge>
            )
        },
        {
            header: 'Branch',
            render: (row) => (
                <span className="text-text-secondary">
                    {row.branch_name || '-'}
                </span>
            )
        },
        {
            header: 'Joined',
            render: (row) => (
                <span className="text-text-secondary">
                    {formatDate(row.created_at)}
                </span>
            )
        },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex gap-2">

                    <button
                        onClick={() => handleEdit(row)}
                        className="text-primary hover:bg-primary/10 p-1 rounded transition"
                        title="Edit"
                    >
                        <Edit size={16} />
                    </button>

                    <button
                        onClick={() => handleDelete(row.id)}
                        className="text-danger hover:bg-danger/10 p-1 rounded transition"
                        title="Delete"
                    >
                        <Trash2 size={16} />
                    </button>

                </div>
            ),
        },
    ];

    return (
        <div className="space-y-6 text-text-primary">

            <div className="flex justify-between items-center">

                <h1 className="text-2xl font-semibold">
                    Users
                </h1>

                <Button
                    onClick={handleCreate}
                    className="flex items-center gap-2 bg-primary text-white hover:bg-primary-hover"
                >
                    <Plus size={16} />
                    Add User
                </Button>

            </div>

            <div className="bg-card border border-border rounded-lg p-6">
                <UserFilter onFilter={handleFilter} />
            </div>

            <div className="bg-card border border-border rounded-lg overflow-hidden flex flex-col">

                <div className="overflow-x-auto">

                    {loading ? (

                        <div className="p-12 text-center text-text-secondary">

                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>

                            Loading users...

                        </div>

                    ) : (

                        <Table
                            columns={columns}
                            data={users}
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

            <UserForm
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleSubmit}
                initialData={editingUser}
            />

        </div>
    );
};

export default UserList;
import React, { useEffect, useState } from 'react';
import { usersAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import UserForm from '../components/UserForm';
import { Edit, Trash2, Plus } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';

const UserList = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const response = await usersAPI.getUsers();
            setUsers(response.data);
        } catch (error) {
            console.error("Failed to fetch users", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

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
                fetchUsers();
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
            fetchUsers();
        } catch (error) {
            console.error("Failed to save user", error);
            alert("Failed to save user");
        }
    };

    const columns = [
        { header: 'Name', accessor: (row) => `${row.first_name} ${row.last_name}` },
        { header: 'Email', accessor: 'email' },
        { header: 'Role', accessor: (row) => <Badge variant="blue">{row.role}</Badge> },
        { header: 'Joined', accessor: (row) => formatDate(row.created_at) },
        {
            header: 'Actions',
            accessor: (row) => (
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
                <h1 className="text-2xl font-semibold text-gray-900">Users</h1>
                <Button onClick={handleCreate} className="flex items-center space-x-2">
                    <Plus size={16} />
                    <span>Add User</span>
                </Button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
                <Table
                    columns={columns}
                    data={users}
                />
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

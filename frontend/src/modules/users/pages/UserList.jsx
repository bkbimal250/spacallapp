import React, { useEffect, useState } from 'react';
import { usersAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import UserForm from '../components/UserForm';
import UserFilter from '../components/UserFilter';
import Pagination from '../../../shared/components/Pagination';
import { Edit, Trash2, Plus, Copy, Check, Eye, EyeOff } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';
import { useAuth } from '../../../shared/hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { PageSpinner, ContentSkeleton } from '../../../shared/components/loaders';

const EmailCell = ({ row, isSuperAdmin }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = (e) => {
        e.stopPropagation();
        let textToCopy = row.email;

        if (isSuperAdmin) {
            const password = row.password_plain || row.password;
            if (password) {
                textToCopy = `email : ${row.email}\npassword: ${password}`;
            }
        }

        navigator.clipboard.writeText(textToCopy);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="flex items-center gap-2 group">
            <span className="text-text-secondary whitespace-nowrap">
                {row.email}
            </span>
            <button
                onClick={handleCopy}
                className={`p-1 rounded transition-all duration-200 ${copied
                    ? 'text-success bg-success/10'
                    : 'text-text-muted hover:text-primary hover:bg-primary/10 opacity-0 group-hover:opacity-100 flex-shrink-0'
                    }`}
                title={isSuperAdmin ? "Copy Credentials" : "Copy Email"}
            >
                {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
        </div>
    );
};

const PasswordCell = ({ row }) => {
    const [show, setShow] = useState(false);
    const [copied, setCopied] = useState(false);
    const password = row.password_plain || row.password || '';

    const handleCopy = (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(password);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (!password) return <span className="text-text-muted italic text-xs">Not set</span>;

    return (
        <div className="flex items-center gap-2 group">
            <span className="text-text-secondary font-mono tracking-wider min-w-[80px]">
                {show ? password : '••••••••'}
            </span>
            <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={(e) => { e.stopPropagation(); setShow(!show); }}
                    className="p-1 rounded text-text-muted hover:text-primary hover:bg-primary/10"
                    title={show ? "Hide Password" : "Show Password"}
                >
                    {show ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
                <button
                    onClick={handleCopy}
                    className={`p-1 rounded transition-all duration-200 ${copied ? 'text-success bg-success/10' : 'text-text-muted hover:text-primary hover:bg-primary/10'}`}
                    title="Copy Password"
                >
                    {copied ? <Check size={14} /> : <Copy size={14} />}
                </button>
            </div>
        </div>
    );
};

const UserList = () => {
    const { user: currentUser } = useAuth();
    const navigate = useNavigate();
    const isSuperAdmin = currentUser?.role === 'super_admin';
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 100;

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
        setSubmitting(true);
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
        } finally {
            setSubmitting(false);
        }
    };

    const handleViewDetails = (userId) => {
        navigate(`/users/login-history?user=${userId}`);
    };

    const columns = React.useMemo(() => {
        const cols = [
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
                render: (row) => <EmailCell row={row} isSuperAdmin={isSuperAdmin} />
            }
        ];

        if (isSuperAdmin) {
            cols.push({
                header: 'Password',
                render: (row) => <PasswordCell row={row} />
            });
        }

        cols.push(
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
                            onClick={() => handleViewDetails(row.id)}
                            className="bg-bg-tertiary text-text-secondary hover:bg-bg-quaternary px-2 py-1 rounded-md text-xs font-medium transition flex items-center gap-1 border border-border"
                            title="View Details"
                        >
                            <Eye size={14} />
                            Logs
                        </button>
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
            }
        );

        return cols;
    }, [isSuperAdmin, handleEdit, handleDelete]);

    return (
        <div className="space-y-6 text-text-primary">

            <div className="flex justify-between items-center">

                <h1 className="text-2xl font-semibold">
                    Users
                </h1>

                <div className="flex gap-2">
                    <Button
                        onClick={() => navigate('/users/login-history')}
                        className="flex items-center gap-2 bg-secondary text-white hover:bg-secondary/90"
                    >
                        <Eye size={16} />
                        Login History
                    </Button>
                    <Button
                        onClick={handleCreate}
                        className="flex items-center gap-2 bg-primary text-white hover:bg-primary-hover"
                    >
                        <Plus size={16} />
                        Add User
                    </Button>
                </div>

            </div>

            <div className="bg-card border border-border rounded-lg p-6">
                <UserFilter onFilter={handleFilter} />
            </div>

            <div className="bg-card border border-border rounded-lg overflow-hidden flex flex-col">

                <div className="overflow-x-auto min-h-[400px]">

                    {loading && users.length === 0 ? (
                        <PageSpinner message="Loading users..." />
                    ) : loading && users.length > 0 ? (
                        <ContentSkeleton rows={10} />
                    ) : (
                        <>
                            {users.length === 0 ? (
                                <div className="p-12 text-center text-text-secondary">
                                    No users found.
                                </div>
                            ) : (
                                <Table
                                    columns={columns}
                                    data={users}
                                />
                            )}
                        </>
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

            <UserForm
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleSubmit}
                initialData={editingUser}
                loading={submitting}
            />

        </div>
    );
};

export default UserList;
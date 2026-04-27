import React, { useEffect, useState } from 'react';
import { contactApi } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import ContactForm from '../components/ContactForm';
import ContactFilter from '../components/ContactFilter';
import Pagination from '../../../shared/components/Pagination';
import {
    Edit,
    Trash2,
    Plus,
    User,
    Phone,
    ExternalLink
} from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';
import { useNavigate } from 'react-router-dom';

const ContactList = () => {

    const navigate = useNavigate();

    const [contacts, setContacts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingContact, setEditingContact] = useState(null);

    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);

    const pageSize = 100;

    const fetchContacts = async (currentFilters = {}, currentPage = 1) => {

        setLoading(true);

        try {

            const response = await contactApi.getContacts({
                ...currentFilters,
                page: currentPage
            });

            if (response.data.results) {

                setContacts(response.data.results);
                setTotalCount(response.data.count);

            } else {

                setContacts(response.data);
                setTotalCount(response.data.length);

            }

        } catch (error) {

            console.error("Failed to fetch contacts", error);

        } finally {

            setLoading(false);

        }

    };

    useEffect(() => {

        fetchContacts(filters, page);

    }, [filters, page]);

    const handleFilter = (newFilters) => {

        setFilters(newFilters);
        setPage(1);

    };

    const handlePageChange = (newPage) => {

        setPage(newPage);

    };

    const handleCreate = () => {

        setEditingContact(null);
        setIsModalOpen(true);

    };

    const handleEdit = (contact) => {

        setEditingContact(contact);
        setIsModalOpen(true);

    };

    const handleViewCalls = (phoneNumber) => {

        navigate(`/calllogs/details?search=${encodeURIComponent(phoneNumber)}&quick_date=all`);

    };

    const handleDelete = async (id) => {

        if (!window.confirm("Delete this contact?")) return;

        try {

            await contactApi.deleteContact(id);
            fetchContacts(filters, page);

        } catch (error) {

            console.error("Failed to delete contact", error);

        }

    };

    const handleSubmit = async (data) => {

        try {

            if (editingContact) {

                await contactApi.updateContact(editingContact.id, data);

            } else {

                await contactApi.createContact(data);

            }

            setIsModalOpen(false);
            fetchContacts(filters, page);

        } catch (error) {

            console.error("Failed to save contact", error);

        }

    };

    const columns = [

        {
            header: 'Name',
            render: (row) => (
                <div className="flex items-center space-x-2">
                    <User size={16} className="text-primary" />
                    <span className="font-semibold text-text-primary">
                        {row.name}
                    </span>
                </div>
            )
        },

        {
            header: 'Phone',
            render: (row) => (
                <div className="flex items-center text-sm text-text-secondary">
                    <Phone size={14} className="mr-1.5 opacity-70" />
                    {row.phone_number}
                </div>
            )
        },

        {
            header: 'Call Activity',
            render: (row) => (
                <div className="flex items-center">

                    <span
                        className={`text-xs px-2 py-1 rounded-md font-semibold ${row.total_calls > 0
                                ? "bg-success/10 text-success"
                                : "bg-border text-text-secondary"
                            }`}
                    >
                        {row.total_calls || 0} Calls
                    </span>

                    {row.total_calls > 0 && (
                        <button
                            onClick={() =>
                                handleViewCalls(row.phone_number)
                            }
                            className="ml-2 text-primary hover:text-primary/80"
                            title="View call logs"
                        >
                            <ExternalLink size={14} />
                        </button>
                    )}

                </div>
            )
        },

        {
            header: 'Email',
            accessor: 'email',
            render: (row) =>
                row.email || (
                    <span className="text-text-secondary opacity-60">
                        —
                    </span>
                )
        },

        {
            header: 'City',
            accessor: 'city',
            render: (row) =>
                row.city || (
                    <span className="text-text-secondary opacity-60">
                        —
                    </span>
                )
        },

        {
            header: 'Country',
            accessor: 'country',
            render: (row) =>
                row.country || (
                    <span className="text-text-secondary opacity-60">
                        —
                    </span>
                )
        },

        {
            header: 'Created',
            render: (row) =>
                formatDate(row.created_at, 'MMM dd, yyyy HH:mm')
        },

        {
            header: 'Actions',
            render: (row) => (
                <div className="flex space-x-2">

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
            )
        }

    ];

    return (

        <div className="space-y-6">

            <div className="flex justify-between items-center">

                <h1 className="text-2xl font-bold text-text-primary">
                    Contacts
                </h1>

                <Button
                    onClick={handleCreate}
                    className="flex items-center space-x-2"
                >
                    <Plus size={16} />
                    <span>Add Contact</span>
                </Button>

            </div>

            <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
                <ContactFilter onFilter={handleFilter} />
            </div>

            <div className="bg-card border border-border rounded-xl overflow-hidden flex flex-col shadow-sm">

                <div className="overflow-x-auto">

                    {loading ? (

                        <div className="p-12 text-center text-text-secondary">

                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>

                            Loading contacts...

                        </div>

                    ) : (

                        <Table
                            columns={columns}
                            data={contacts}
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

            <ContactForm
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleSubmit}
                initialData={editingContact}
            />

        </div>

    );

};

export default ContactList;
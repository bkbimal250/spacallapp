import React, { useEffect, useState } from 'react';
import { contactApi } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import ContactForm from '../components/ContactForm';
import ContactFilter from '../components/ContactFilter';
import Pagination from '../../../shared/components/Pagination';
import { Edit, Trash2, Plus, User, Phone, MessageSquare, ExternalLink } from 'lucide-react';
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
    const pageSize = 50;

    const fetchContacts = async (currentFilters = {}, currentPage = 1) => {
        setLoading(true);
        try {
            const response = await contactApi.getContacts({ ...currentFilters, page: currentPage });
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
        navigate(`/calllogs/details?search=${encodeURIComponent(phoneNumber)}`);
    };

    const handleDelete = async (id) => {
        if (window.confirm("Are you sure you want to delete this contact?")) {
            try {
                await contactApi.deleteContact(id);
                fetchContacts(filters, page);
            } catch (error) {
                console.error("Failed to delete contact", error);
            }
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
                <div className="flex items-center">
                    <User size={16} className="mr-2 text-sky-500" />
                    <span className="font-medium text-gray-900">{row.name}</span>
                </div>
            )
        },
        { 
            header: 'Phone Number', 
            render: (row) => (
                <div className="flex items-center text-sm">
                    <Phone size={14} className="mr-1.5 text-gray-400" />
                    {row.phone_number}
                </div>
            )
        },
        {
            header: 'Call Activity',
            render: (row) => (
                <div className="flex items-center">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${row.total_calls > 0 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                        {row.total_calls || 0} Calls
                    </span>
                    {row.total_calls > 0 && (
                        <button 
                            onClick={() => handleViewCalls(row.phone_number)}
                            className="ml-2 text-sky-600 hover:text-sky-800 transition-colors"
                            title="View all calls for this contact"
                        >
                            <ExternalLink size={14} />
                        </button>
                    )}
                </div>
            )
        },
        { header: 'Email', accessor: 'email', render: (row) => row.email || <span className="text-gray-400">—</span> },
        { header: 'City', accessor: 'city', render: (row) => row.city || <span className="text-gray-400">—</span> },
        { header: 'Country', accessor: 'country', render: (row) => row.country || <span className="text-gray-400">—</span> },
        { header: 'Created At', render: (row) => formatDate(row.created_at, 'MMM dd, yyyy HH:mm') },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex space-x-2">
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
                <h1 className="text-2xl font-semibold text-gray-900">Contacts</h1>
                <Button onClick={handleCreate} className="flex items-center space-x-2">
                    <Plus size={16} />
                    <span>Add Contact</span>
                </Button>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
                <ContactFilter onFilter={handleFilter} />
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden flex flex-col">
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-12 text-center text-gray-500">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500 mx-auto mb-4"></div>
                            Loading contacts...
                        </div>
                    ) : (
                        <Table
                            columns={columns}
                            data={contacts}
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

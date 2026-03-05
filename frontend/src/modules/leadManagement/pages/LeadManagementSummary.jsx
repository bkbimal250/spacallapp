import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { leadManagementAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import Pagination from '../../../shared/components/Pagination';
import { ROUTES } from '../../../routes/routeConfig';
import { List } from 'lucide-react';

const LeadManagementSummary = () => {
    const navigate = useNavigate();
    const [summaries, setSummaries] = useState([]);
    const [loading, setLoading] = useState(true);

    // Pagination
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 50;

    // Filter states
    const [search, setSearch] = useState('');
    const [city, setCity] = useState('');
    const [status, setStatus] = useState('');
    const [activeFilters, setActiveFilters] = useState({});

    const fetchSummary = async () => {
        setLoading(true);
        try {
            const params = { page, ...activeFilters };
            const response = await leadManagementAPI.getBranchSummary(params);

            if (response.data.results) {
                setSummaries(response.data.results);
                setTotalCount(response.data.count);
            } else {
                setSummaries(response.data);
                setTotalCount(response.data.length);
            }
        } catch (error) {
            console.error("Failed to fetch lead management summary", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSummary();
    }, [activeFilters, page]);

    const handleFilter = () => {
        const newFilters = {};
        if (search.trim()) newFilters.branch_search = search.trim();
        if (city.trim()) newFilters.city = city.trim();
        if (status) newFilters.status = status;

        setActiveFilters(newFilters);
        setPage(1);
    };

    const handleClear = () => {
        setSearch('');
        setCity('');
        setStatus('');
        setActiveFilters({});
        setPage(1);
    };

    const handlePageChange = (newPage) => {
        setPage(newPage);
    };

    const handleDetails = (branchId) => {
        navigate(`${ROUTES.LEAD_MANAGEMENT_LIST}?branch=${branchId}`);
    };

    const columns = [
        { header: 'Branch Name', accessor: 'branch_name', render: (row) => <span className="font-semibold text-gray-900">{row.branch_name}</span> },
        {
            header: 'Area / City', render: (row) => (
                <div className="flex flex-col">
                    <span className="text-sm font-medium text-gray-800">{row.area}</span>
                    <span className="text-xs text-gray-500">{row.city}</span>
                </div>
            )
        },
        { header: 'Total Leads', accessor: 'total_leads', render: (row) => <span className="font-bold text-indigo-700">{row.total_leads}</span> },
        { header: 'Pending', accessor: 'total_pending', render: (row) => <span className="text-gray-600 font-medium">{row.total_pending}</span> },
        { header: 'Ringing', accessor: 'total_ringing', render: (row) => <span className="text-blue-600 font-medium">{row.total_ringing}</span> },
        { header: 'Coming', accessor: 'total_coming', render: (row) => <span className="text-purple-600 font-medium">{row.total_coming}</span> },
        { header: 'Interested', accessor: 'total_interested', render: (row) => <span className="text-green-600 font-medium">{row.total_interested}</span> },
        { header: 'Not Interested', accessor: 'total_not_interested', render: (row) => <span className="text-red-500 font-medium">{row.total_not_interested}</span> },
        {
            header: 'Actions',
            render: (row) => (
                <Button variant="outline" size="sm" onClick={() => handleDetails(row.branch_id)} className="flex items-center space-x-1 border-gray-200">
                    <List size={14} />
                    <span>View Details</span>
                </Button>
            )
        }
    ];

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-semibold text-gray-900">Lead Management Summary</h1>

            <div className="bg-white shadow rounded-lg p-6">
                <div className="flex flex-col mb-4 space-y-4 border-b border-gray-100 pb-4">
                    <h2 className="text-lg font-medium text-gray-800">Branch Search</h2>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                        <div className="flex flex-col">
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">Search Name/Code</label>
                            <Input
                                placeholder="Search branches..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') handleFilter(); }}
                            />
                        </div>
                        <div className="flex flex-col">
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">City</label>
                            <Input
                                placeholder="Filter by city..."
                                value={city}
                                onChange={(e) => setCity(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') handleFilter(); }}
                            />
                        </div>
                        <div className="flex flex-col">
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">Branch Status</label>
                            <select
                                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                value={status}
                                onChange={(e) => setStatus(e.target.value)}
                            >
                                <option value="">All Statuses</option>
                                <option value="active">Active</option>
                                <option value="inactive">Inactive</option>
                            </select>
                        </div>
                        <div className="flex justify-end space-x-2">
                            <Button variant="outline" onClick={handleClear} className="w-1/2 justify-center border-gray-300 text-gray-700 hover:bg-gray-50">Clear</Button>
                            <Button onClick={handleFilter} className="w-1/2 justify-center bg-indigo-600 hover:bg-indigo-700 text-white border-transparent">Filter</Button>
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto pt-4 flex flex-col">
                    <div className="overflow-x-auto">
                        {loading ? (
                            <div className="p-12 text-center text-gray-500">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto mb-4"></div>
                                Loading summary...
                            </div>
                        ) : (
                            <Table
                                columns={columns}
                                data={summaries}
                            />
                        )}
                    </div>

                    {!loading && totalCount > 0 && Math.ceil(totalCount / pageSize) > 1 && (
                        <div className="mt-4">
                            <Pagination
                                currentPage={page}
                                totalPages={Math.ceil(totalCount / pageSize)}
                                onPageChange={handlePageChange}
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default LeadManagementSummary;

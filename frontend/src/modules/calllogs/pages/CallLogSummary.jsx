import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { callLogsAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import Pagination from '../../../shared/components/Pagination';
import { ROUTES } from '../../../routes/routeConfig';
import { BarChart3, List } from 'lucide-react';

const CallLogSummary = () => {
    const navigate = useNavigate();
    const [summaries, setSummaries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterPeriod, setFilterPeriod] = useState('today');

    // Pagination
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 50;

    // Filter states corresponding to wireframe
    const [search, setSearch] = useState('');
    const [city, setCity] = useState('');
    const [status, setStatus] = useState('');

    // Applied filters
    const [activeFilters, setActiveFilters] = useState({});

    const getDatesForPeriod = (period) => {
        const now = new Date();
        let startDate = '';
        let endDate = '';

        if (period === 'today') {
            const todayStr = now.toISOString().split('T')[0];
            startDate = todayStr;
            endDate = todayStr;
        } else if (period === 'yesterday') {
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);
            const ydayStr = yesterday.toISOString().split('T')[0];
            startDate = ydayStr;
            endDate = ydayStr;
        } else if (period === 'this_week') {
            const firstDay = new Date(now.setDate(now.getDate() - now.getDay()));
            startDate = firstDay.toISOString().split('T')[0];
        } else if (period === 'last_7_days') {
            const last7 = new Date(now);
            last7.setDate(last7.getDate() - 7);
            startDate = last7.toISOString().split('T')[0];
        }

        return { startDate, endDate };
    };

    const fetchSummary = async () => {
        setLoading(true);
        try {
            const dates = getDatesForPeriod(filterPeriod);
            const params = { page, ...activeFilters };
            if (dates.startDate) params.start_date = dates.startDate;
            if (dates.endDate) params.end_date = dates.endDate;

            const response = await callLogsAPI.getBranchSummary(params);

            // Handle DRF built-in pagination response gracefully
            if (response.data.results) {
                setSummaries(response.data.results);
                setTotalCount(response.data.count);
            } else {
                setSummaries(response.data);
                setTotalCount(response.data.length);
            }
        } catch (error) {
            console.error("Failed to fetch branch summary", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSummary();
    }, [filterPeriod, activeFilters, page]);

    const handleFilter = () => {
        const newFilters = {};
        if (search.trim()) newFilters.branch_search = search.trim();
        if (city.trim()) newFilters.city = city.trim();
        if (status) newFilters.status = status;

        setActiveFilters(newFilters);
        setPage(1); // Reset page to 1 when filtering
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
        navigate(`${ROUTES.CALLLOG_DETAILS}?branch=${branchId}`);
    };

    const handleAnalytics = (branchId) => {
        navigate(`${ROUTES.ANALYTICS}?branch=${branchId}`);
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
        { header: 'Total Calls', accessor: 'total_calls', render: (row) => <span className="font-bold text-gray-700">{row.total_calls}</span> },
        { header: 'Total Outgoing', accessor: 'total_outgoing', render: (row) => <span className="text-blue-600 font-medium">{row.total_outgoing}</span> },
        { header: 'Total Incoming', accessor: 'total_incoming', render: (row) => <span className="text-green-600 font-medium">{row.total_incoming}</span> },
        { header: 'Total Missed', accessor: 'total_missed', render: (row) => <span className="text-red-600 font-medium">{row.total_missed}</span> },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex space-x-2">
                    <Button variant="outline" size="sm" onClick={() => handleDetails(row.branch_id)} className="flex items-center space-x-1 border-gray-200">
                        <List size={14} />
                        <span>Details</span>
                    </Button>
                    <Button variant="white" size="sm" onClick={() => handleAnalytics(row.branch_id)} className="flex items-center space-x-1 border-gray-200 text-indigo-600">
                        <BarChart3 size={14} />
                        <span>Analytics</span>
                    </Button>
                </div>
            )
        }
    ];

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-semibold text-gray-900">Branch Call Logs Summary</h1>

            <div className="bg-white shadow rounded-lg p-6">
                <div className="flex flex-col mb-4 space-y-4">
                    <div className="flex flex-col sm:flex-row items-center justify-between border-b border-gray-100 pb-4">
                        <h2 className="text-lg font-medium text-gray-800">Branch Data Filter</h2>
                        <div className="mt-4 sm:mt-0">
                            <select
                                value={filterPeriod}
                                onChange={(e) => {
                                    setFilterPeriod(e.target.value);
                                    setPage(1);
                                }}
                                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm xl:min-w-[200px] focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm cursor-pointer hover:border-indigo-400"
                            >
                                <option value="today">Today data only</option>
                                <option value="yesterday">Yesterday</option>
                                <option value="last_7_days">Last 7 Days</option>
                                <option value="this_week">This Week</option>
                                <option value="all">All Time</option>
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                        <div className="flex flex-col">
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">Search name/code</label>
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
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">Status</label>
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

                <div className="overflow-x-auto border-t border-gray-100 pt-4 flex flex-col">
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

export default CallLogSummary;

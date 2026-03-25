import React, { useEffect, useState, useMemo, useCallback, memo } from 'react';
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

    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);

    const pageSize = 100;

    const [search, setSearch] = useState('');
    const [city, setCity] = useState('');
    const [status, setStatus] = useState('');

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

    const fetchSummary = useCallback(async () => {

        setLoading(true);

        try {

            const dates = getDatesForPeriod(filterPeriod);

            const params = { page, ...activeFilters };

            if (dates.startDate) params.start_date = dates.startDate;
            if (dates.endDate) params.end_date = dates.endDate;

            const response = await callLogsAPI.getBranchSummary(params);

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

    }, [filterPeriod, page, activeFilters]);

    useEffect(() => {
        fetchSummary();
    }, [fetchSummary]);

    const handleSearchChange = useCallback((e) => setSearch(e.target.value), []);
    const handleCityChange = useCallback((e) => setCity(e.target.value), []);
    const handleStatusSelectChange = useCallback((e) => setStatus(e.target.value), []);
    const handlePeriodChange = useCallback((e) => {
        setFilterPeriod(e.target.value);
        setPage(1);
    }, []);

    const handleFilter = useCallback(() => {

        const newFilters = {};

        if (search.trim()) newFilters.branch_search = search.trim();
        if (city.trim()) newFilters.city = city.trim();
        if (status) newFilters.status = status;

        setActiveFilters(newFilters);
        setPage(1);

    }, [search, city, status]);

    const handleClear = useCallback(() => {

        setSearch('');
        setCity('');
        setStatus('');
        setActiveFilters({});
        setPage(1);

    }, []);

    const handlePageChange = useCallback((newPage) => {
        setPage(newPage);
    }, []);

    const handleDetails = useCallback((branchId) => {
        navigate(`${ROUTES.CALLLOG_DETAILS}?branch=${branchId}`);
    }, [navigate]);

    const handleAnalytics = useCallback((branchId) => {
        navigate(`${ROUTES.ANALYTICS}?branch=${branchId}`);
    }, [navigate]);

    const columns = useMemo(() => [

        {
            header: 'Branch Name',
            render: (row) => (
                <span className="font-semibold text-text-primary">
                    {row.branch_name}
                </span>
            )
        },

        {
            header: 'Area / City',
            render: (row) => (
                <div className="flex flex-col">
                    <span className="text-sm font-medium text-text-primary">
                        {row.area}
                    </span>
                    <span className="text-xs text-text-secondary">
                        {row.city}
                    </span>
                </div>
            )
        },

        {
            header: 'Total Calls',
            render: (row) => (
                <span className="font-bold text-text-primary">
                    {row.total_calls}
                </span>
            )
        },

        {
            header: 'Total Outgoing',
            render: (row) => (
                <span className="text-info font-medium">
                    {row.total_outgoing}
                </span>
            )
        },

        {
            header: 'Total Incoming',
            render: (row) => (
                <span className="text-success font-medium">
                    {row.total_incoming}
                </span>
            )
        },

        {
            header: 'Total Missed',
            render: (row) => (
                <span className="text-danger font-medium">
                    {row.total_missed}
                </span>
            )
        },

        {
            header: 'Actions',
            render: (row) => (

                <div className="flex space-x-2">

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDetails(row.branch_id)}
                        className="flex items-center space-x-1 border-border"
                    >

                        <List size={14} />

                        <span>Details</span>

                    </Button>

                    <Button
                        variant="white"
                        size="sm"
                        onClick={() => handleAnalytics(row.branch_id)}
                        className="flex items-center space-x-1 border-border text-primary"
                    >

                        <BarChart3 size={14} />

                        <span>Analytics</span>

                    </Button>

                </div>

            )
        }

    ], [handleDetails, handleAnalytics]);

    return (

        <div className="space-y-6 text-text-primary">

            <h1 className="text-2xl font-semibold">
                Branch Call Logs Summary
            </h1>

            <div className="bg-card border border-border rounded-2xl p-6">

                <div className="flex flex-col mb-4 space-y-4">

                    <div className="flex flex-col sm:flex-row items-center justify-between border-b border-border pb-4">

                        <h2 className="text-lg font-medium">
                            Branch Data Filter
                        </h2>

                        <div className="mt-4 sm:mt-0">

                            <select
                                value={filterPeriod}
                                onChange={handlePeriodChange}
                                className="block w-full px-3 py-2 bg-background border border-border rounded-md text-text-primary focus:ring-primary focus:border-primary sm:text-sm cursor-pointer"
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

                            <label className="text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
                                Search name/code
                            </label>

                            <Input
                                placeholder="Search branches..."
                                value={search}
                                onChange={handleSearchChange}
                                onKeyDown={(e) => { if (e.key === 'Enter') handleFilter(); }}
                            />

                        </div>

                        <div className="flex flex-col">

                            <label className="text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
                                City
                            </label>

                            <Input
                                placeholder="Filter by city..."
                                value={city}
                                onChange={handleCityChange}
                                onKeyDown={(e) => { if (e.key === 'Enter') handleFilter(); }}
                            />

                        </div>

                        <div className="flex flex-col">

                            <label className="text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
                                Status
                            </label>

                            <select
                                className="block w-full px-3 py-2 bg-background border border-border rounded-md text-text-primary focus:ring-primary focus:border-primary sm:text-sm"
                                value={status}
                                onChange={handleStatusSelectChange}
                            >

                                <option value="">All Statuses</option>
                                <option value="active">Active</option>
                                <option value="inactive">Inactive</option>

                            </select>

                        </div>

                        <div className="flex justify-end space-x-2">

                            <Button
                                variant="secondary"
                                onClick={handleClear}
                                className="w-1/2 justify-center"
                            >
                                Clear
                            </Button>

                            <Button
                                onClick={handleFilter}
                                className="w-1/2 justify-center"
                            >
                                Filter
                            </Button>

                        </div>

                    </div>

                </div>

                <div className="overflow-x-auto border-t border-border pt-4 flex flex-col">

                    <div className="overflow-x-auto">

                        {loading ? (

                            <div className="p-12 text-center text-text-secondary">

                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>

                                Loading summary...

                            </div>

                        ) : (

                            <Table
                                columns={columns}
                                data={summaries}
                            />

                        )}

                    </div>

                    {!loading && totalCount > 0 && (

                        <div className="mt-4">

                            <Pagination
                                currentPage={page}
                                totalPages={Math.ceil(totalCount / pageSize)}
                                onPageChange={handlePageChange}
                                totalCount={totalCount}
                                pageSize={pageSize}
                            />

                        </div>

                    )}

                </div>

            </div>

        </div>

    );

};

export default memo(CallLogSummary);
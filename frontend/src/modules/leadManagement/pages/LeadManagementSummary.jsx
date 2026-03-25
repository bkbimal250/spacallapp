import React, { useEffect, useState, useMemo, useCallback, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { leadManagementAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import Pagination from '../../../shared/components/Pagination';
import { ROUTES } from '../../../routes/routeConfig';
import { List, Search, Target, Clock, CheckCircle2, XCircle } from 'lucide-react';
import StatsCard from '../../dashboard/components/StatsCard';

const LeadManagementSummary = () => {
    const navigate = useNavigate();
    const [summaries, setSummaries] = useState([]);
    const [loading, setLoading] = useState(true);

    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 100;

    const [search, setSearch] = useState('');
    const [city, setCity] = useState('');
    const [status, setStatus] = useState('');
    const [activeFilters, setActiveFilters] = useState({});

    const [totals, setTotals] = useState({
        leads: 0,
        pending: 0,
        interested: 0,
        not_interested: 0
    });

    const fetchSummary = useCallback(async () => {
        setLoading(true);
        try {
            const params = { page, ...activeFilters };
            const response = await leadManagementAPI.getBranchSummary(params);

            let data = [];

            if (response.data.results) {
                data = response.data.results;
                setTotalCount(response.data.count);
            } else {
                data = response.data;
                setTotalCount(response.data.length);
            }

            setSummaries(data);

            const t = data.reduce((acc, curr) => ({
                leads: acc.leads + curr.total_leads,
                pending: acc.pending + curr.total_pending,
                interested: acc.interested + curr.total_interested,
                not_interested: acc.not_interested + curr.total_not_interested
            }), { leads: 0, pending: 0, interested: 0, not_interested: 0 });

            setTotals(t);

        } catch (error) {
            console.error("Failed to fetch lead management summary", error);
        } finally {
            setLoading(false);
        }
    }, [page, activeFilters]);

    useEffect(() => {
        fetchSummary();
    }, [fetchSummary]);

    const handleSearchChange = useCallback((e) => setSearch(e.target.value), []);
    const handleCityChange = useCallback((e) => setCity(e.target.value), []);
    const handleStatusSelectChange = useCallback((e) => setStatus(e.target.value), []);

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

    const handleDetails = useCallback((branchId, statusVal = '') => {
        let url = `${ROUTES.LEAD_MANAGEMENT_LIST}?branch=${branchId}`;
        if (statusVal) url += `&status=${statusVal}`;
        navigate(url);
    }, [navigate]);

    const columns = useMemo(() => [
        {
            header: 'Branch Name',
            render: (row) => (
                <button
                    onClick={() => handleDetails(row.branch_id)}
                    className="font-semibold text-text-primary hover:text-primary transition"
                >
                    {row.branch_name}
                </button>
            )
        },
        {
            header: 'Area / City',
            render: (row) => (
                <div className="flex flex-col">
                    <span className="text-sm text-text-primary">{row.area}</span>
                    <span className="text-xs text-text-secondary">{row.city}</span>
                </div>
            )
        },
        {
            header: 'Total Leads',
            render: (row) => (
                <button
                    onClick={() => handleDetails(row.branch_id)}
                    className="px-3 py-1 text-sm bg-primary/20 text-primary rounded-lg hover:bg-primary/30"
                >
                    {row.total_leads}
                </button>
            )
        },
        {
            header: 'Pending',
            render: (row) => (
                <button
                    onClick={() => handleDetails(row.branch_id, 'pending')}
                    className="px-2 py-1 text-warning hover:bg-warning/10 rounded"
                >
                    {row.total_pending}
                </button>
            )
        },
        {
            header: 'Ringing',
            render: (row) => (
                <button
                    onClick={() => handleDetails(row.branch_id, 'ringing')}
                    className="px-2 py-1 text-info hover:bg-info/10 rounded"
                >
                    {row.total_ringing}
                </button>
            )
        },
        {
            header: 'Coming',
            render: (row) => (
                <button
                    onClick={() => handleDetails(row.branch_id, 'coming')}
                    className="px-2 py-1 text-accent-purple hover:bg-accent-purple/10 rounded"
                >
                    {row.total_coming}
                </button>
            )
        },
        {
            header: 'Interested',
            render: (row) => (
                <button
                    onClick={() => handleDetails(row.branch_id, 'interested')}
                    className="px-2 py-1 text-success hover:bg-success/10 rounded"
                >
                    {row.total_interested}
                </button>
            )
        },
        {
            header: 'Not Interested',
            render: (row) => (
                <button
                    onClick={() => handleDetails(row.branch_id, 'not_interested')}
                    className="px-2 py-1 text-danger hover:bg-danger/10 rounded"
                >
                    {row.total_not_interested}
                </button>
            )
        },
        {
            header: 'Actions',
            render: (row) => (
                <button
                    onClick={() => handleDetails(row.branch_id)}
                    className="flex items-center gap-2 text-text-secondary hover:text-primary transition"
                >
                    <List size={14} />
                    View
                </button>
            )
        }
    ], [handleDetails]);

    return (
        <div className="space-y-6 text-text-primary">

            <div>
                <h1 className="text-2xl font-bold text-text-primary">
                    Lead Performance Summary
                </h1>
                <p className="text-sm text-text-secondary">
                    Branch-wise lead conversion analytics
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard
                    title="Total Leads"
                    value={totals.leads}
                    icon={<Target className="text-primary" size={20} />}
                    className="bg-card border border-border"
                />
                <StatsCard
                    title="Pending"
                    value={totals.pending}
                    icon={<Clock className="text-warning" size={20} />}
                    className="bg-card border border-border"
                />
                <StatsCard
                    title="Interested"
                    value={totals.interested}
                    icon={<CheckCircle2 className="text-success" size={20} />}
                    className="bg-card border border-border"
                />
                <StatsCard
                    title="Not Interested"
                    value={totals.not_interested}
                    icon={<XCircle className="text-danger" size={20} />}
                    className="bg-card border border-border"
                />
            </div>

            <div className="bg-card border border-border rounded-xl p-6">

                <div className="flex flex-col mb-6 p-4 bg-background border border-border rounded-lg">

                    <div className="flex items-center gap-2 mb-4">
                        <Search size={18} className="text-primary" />
                        <h2 className="text-lg font-semibold">Filter Branches</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">

                        <Input
                            placeholder="Branch name..."
                            className="bg-card border-border text-text-primary"
                            value={search}
                            onChange={handleSearchChange}
                            onKeyDown={(e) => { if (e.key === 'Enter') handleFilter(); }}
                        />

                        <Input
                            placeholder="City..."
                            className="bg-card border-border text-text-primary"
                            value={city}
                            onChange={handleCityChange}
                            onKeyDown={(e) => { if (e.key === 'Enter') handleFilter(); }}
                        />

                        <select
                            className="px-3 py-2 bg-card border border-border rounded text-text-primary"
                            value={status}
                            onChange={handleStatusSelectChange}
                        >
                            <option value="">All Statuses</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                        </select>

                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                onClick={handleClear}
                                className="border-border text-text-secondary"
                            >
                                Clear
                            </Button>

                            <Button
                                onClick={handleFilter}
                                className="bg-primary hover:bg-primary-hover text-white"
                            >
                                Filter
                            </Button>
                        </div>

                    </div>
                </div>

                <div className="max-h-[600px] overflow-y-auto border border-border rounded-lg">

                    {loading ? (
                        <div className="p-10 text-center text-text-secondary">
                            <div className="animate-spin h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                            Loading summary...
                        </div>
                    ) : (
                        <Table columns={columns} data={summaries} />
                    )}

                </div>

                {!loading && totalCount > 0 && Math.ceil(totalCount / pageSize) > 1 && (
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
    );
};

export default memo(LeadManagementSummary);
import React, { useEffect, useState, useMemo, useCallback, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { callLogsAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Pagination from '../../../shared/components/Pagination';
import CallLogsSummaryFilter from '../components/CallLogsSummaryFilter';
import { ROUTES } from '../../../routes/routeConfig';
import { BarChart3, List } from 'lucide-react';

const CallLogSummary = () => {
    const navigate = useNavigate();

    const [summaries, setSummaries] = useState([]);
    const [loading, setLoading] = useState(true);
    
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 100;

    // We initialize with quick_date: 'today' as the default view
    const [activeFilters, setActiveFilters] = useState({ quick_date: 'today' });
    const [sortConfig, setSortConfig] = useState({ key: 'branch_name', direction: 'asc' });

    const fetchSummary = useCallback(async () => {
        setLoading(true);
        try {
            const ordering = sortConfig.direction === 'desc' ? `-${sortConfig.key}` : sortConfig.key;
            const params = { 
                page, 
                ...activeFilters,
                ordering
            };

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
    }, [page, activeFilters, sortConfig]);

    useEffect(() => {
        fetchSummary();
    }, [fetchSummary]);

    const handleFilter = useCallback((newFilters) => {
        setActiveFilters(newFilters);
        setPage(1);
    }, []);

    const handlePageChange = useCallback((newPage) => {
        setPage(newPage);
    }, []);

    const handleSort = useCallback((key) => {
        setSortConfig(prev => {
            const isMetric = key.startsWith('total_');
            const isSameKey = prev.key === key;
            
            if (isSameKey) {
                return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
            }
            
            // Default to DESC for metrics (more is usually more interesting), ASC for others
            return { key, direction: isMetric ? 'desc' : 'asc' };
        });
        setPage(1);
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
            sortKey: 'branch_name',
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
            sortKey: 'total_calls',
            render: (row) => (
                <span className="font-bold text-text-primary">
                    {row.total_calls}
                </span>
            )
        },
        {
            header: 'Total Outgoing',
            sortKey: 'outgoing_calls',
            render: (row) => (
                <span className="text-info font-medium">
                    {row.total_outgoing}
                </span>
            )
        },
        {
            header: 'Total Incoming',
            sortKey: 'incoming_calls',
            render: (row) => (
                <span className="text-success font-medium">
                    {row.total_incoming}
                </span>
            )
        },
        {
            header: 'Total Missed',
            sortKey: 'missed_calls',
            render: (row) => (
                <span className="text-danger font-medium">
                    {row.total_missed}
                </span>
            )
        },
        {
            header: 'Followed Up',
            sortKey: 'followed',
            render: (row) => (
                <span className="text-success font-medium">
                    {row.total_followed || 0}
                </span>
            )
        },
        {
            header: 'Missed SLA',
            sortKey: 'missed_sla',
            render: (row) => (
                <span className="text-red-600 font-bold">
                    {row.total_missed_sla || 0}
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
                        className="flex items-center space-x-1 border-border-light hover:bg-cardHover h-9"
                    >
                        <List size={14} />
                        <span>Details</span>
                    </Button>
                    <Button
                        variant="white"
                        size="sm"
                        onClick={() => handleAnalytics(row.branch_id)}
                        className="flex items-center space-x-1 border border-border-light text-primary hover:bg-primary/5 h-9"
                    >
                        <BarChart3 size={14} />
                        <span>Analytics</span>
                    </Button>
                </div>
            )
        }
    ], [handleDetails, handleAnalytics]);

    return (
        <div className="space-y-6 text-text-primary animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">
                        Branch Call Logs Summary
                    </h1>
                    <p className="text-sm text-text-secondary mt-1">
                        View and filter call performance across all spa locations.
                    </p>
                </div>
            </div>

            {/* Premium Filter Component */}
            <CallLogsSummaryFilter 
                onFilter={handleFilter} 
                initialFilters={activeFilters}
            />

            <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
                <div className="p-1">
                    {loading ? (
                        <div className="p-20 text-center text-text-secondary">
                            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto mb-4"></div>
                            <p className="font-medium">Loading summary data...</p>
                        </div>
                    ) : summaries.length > 0 ? (
                        <>
                            <Table
                                columns={columns}
                                data={summaries}
                                onSort={handleSort}
                                sortConfig={sortConfig}
                            />
                            {totalCount > pageSize && (
                                <div className="p-4 border-t border-border bg-background/30">
                                    <Pagination
                                        currentPage={page}
                                        totalPages={Math.ceil(totalCount / pageSize)}
                                        onPageChange={handlePageChange}
                                        totalCount={totalCount}
                                        pageSize={pageSize}
                                    />
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="p-20 text-center text-text-secondary bg-background/20">
                            <BarChart3 size={48} className="mx-auto mb-4 opacity-20" />
                            <p className="text-lg font-medium">No results found</p>
                            <p className="text-sm">Try adjusting your filters to see more data.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default memo(CallLogSummary);
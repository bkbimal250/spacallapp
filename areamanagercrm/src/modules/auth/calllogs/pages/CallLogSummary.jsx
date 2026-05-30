import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { callLogsAPI } from '../api';

const PAGE_SIZE = 100;

const defaultFilters = {
    quick_date: 'today',
    branch_search: '',
    city: '',
    status: '',
};

const cleanFilters = (filters) => Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== null && value !== '')
);

const SummaryFilter = ({ filters, onChange, onApply, onClear }) => {
    const setField = (key, value) => onChange({ ...filters, [key]: value });

    return (
        <form
            className="rounded-2xl border border-border bg-card p-4 md:p-5 shadow-sm space-y-4 md:space-y-5"
            onSubmit={(event) => {
                event.preventDefault();
                onApply();
            }}
        >
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr] lg:items-center">
                {/* Period Quick Select */}
                <div className="flex flex-wrap items-center gap-2">
                    <div className="mr-2 text-xs lg:text-sm font-semibold uppercase tracking-wider text-textSecondary">Period</div>
                    <div className="grid grid-cols-3 gap-1.5 w-full xs:w-auto xs:flex xs:flex-wrap">
                        {[
                            ['today', 'Today'],
                            ['yesterday', 'Yesterday'],
                            ['all', 'All Time'],
                        ].map(([value, label]) => (
                            <button
                                key={value}
                                type="button"
                                onClick={() => {
                                    const nextFilters = { ...filters, quick_date: value };
                                    onChange(nextFilters);
                                    onApply(nextFilters);
                                }}
                                className={`rounded-xl px-3 py-2.5 xs:py-2 text-xs font-bold text-center transition-all duration-200 active:scale-[0.97] shadow-sm ${
                                    filters.quick_date === value
                                        ? 'bg-primary text-white shadow-md'
                                        : 'bg-background text-textSecondary border border-border/60 hover:text-textPrimary'
                                }`}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Branch Search Input */}
                <div className="flex min-w-0 items-center rounded-xl bg-background border border-border/80 focus-within:border-primary transition-all">
                    <span className="pl-3.5 pr-2.5 text-xs font-semibold uppercase tracking-wider text-textSecondary">Search</span>
                    <input
                        value={filters.branch_search}
                        onChange={(event) => setField('branch_search', event.target.value)}
                        placeholder="Branch name or code..."
                        className="h-11 min-w-0 flex-1 rounded-r-xl bg-transparent px-3 text-sm text-textPrimary outline-none"
                    />
                </div>
            </div>

            <div className="border-t border-border/80 pt-4 md:pt-5">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">
                    <label className="block">
                        <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-textSecondary">City</span>
                        <input
                            value={filters.city}
                            onChange={(event) => setField('city', event.target.value)}
                            placeholder="All Cities"
                            className="h-11 w-full rounded-xl border border-border/80 bg-background px-3.5 text-sm text-textPrimary outline-none focus:border-primary transition-all"
                        />
                    </label>

                    <label className="block">
                        <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-textSecondary">Status</span>
                        <select
                            value={filters.status}
                            onChange={(event) => setField('status', event.target.value)}
                            className="h-11 w-full rounded-xl border border-border/80 bg-background px-3 text-sm text-textPrimary outline-none focus:border-primary transition-all"
                        >
                            <option value="">All Statuses</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                        </select>
                    </label>

                    {/* Desktop spacer */}
                    <div className="hidden md:block" />

                    {/* Filter Action Buttons */}
                    <div className="flex items-end gap-2 w-full">
                        <button
                            type="button"
                            onClick={onClear}
                            className="h-11 flex-1 rounded-xl border border-border/80 px-4 text-sm font-semibold text-textSecondary transition hover:border-danger hover:text-danger hover:bg-danger/5 active:scale-[0.98]"
                        >
                            Clear
                        </button>
                        <button
                            type="submit"
                            className="h-11 flex-[1.4] rounded-xl bg-primary px-4 text-sm font-semibold text-white transition hover:bg-primary/90 active:scale-[0.98]"
                        >
                            Apply Filter
                        </button>
                    </div>
                </div>
            </div>
        </form>
    );
};

const CallLogSummary = () => {
    const navigate = useNavigate();
    const [draftFilters, setDraftFilters] = useState(defaultFilters);
    const [activeFilters, setActiveFilters] = useState(defaultFilters);
    const [summaries, setSummaries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [sortConfig, setSortConfig] = useState({ key: 'branch_name', direction: 'asc' });

    const fetchSummary = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const ordering = sortConfig.direction === 'desc' ? `-${sortConfig.key}` : sortConfig.key;
            const response = await callLogsAPI.getBranchSummary(cleanFilters({
                ...activeFilters,
                page,
                page_size: PAGE_SIZE,
                ordering,
            }));
            const data = response.data || {};
            setSummaries(data.results || data || []);
            setTotalCount(data.count ?? (Array.isArray(data) ? data.length : 0));
        } catch (err) {
            setError('Unable to load branch summary right now.');
            setSummaries([]);
            setTotalCount(0);
        } finally {
            setLoading(false);
        }
    }, [activeFilters, page, sortConfig]);

    useEffect(() => {
        fetchSummary();
    }, [fetchSummary]);

    const sortBy = (key) => {
        setSortConfig((current) => ({
            key,
            direction: current.key === key && current.direction === 'asc' ? 'desc' : 'asc',
        }));
        setPage(1);
    };

    const openDetails = (row) => {
        const params = new URLSearchParams();
        params.set('branch', row.branch_id);
        params.set('quick_date', activeFilters.quick_date || 'today');
        navigate(`/calllogs?${params.toString()}`);
    };

    const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

    const columns = [
        ['branch_name', 'Branch Name'],
        [null, 'Area / City'],
        ['total_calls', 'Total Calls'],
        ['outgoing_calls', 'Total Outgoing'],
        ['incoming_calls', 'Total Incoming'],
        ['missed_calls', 'Total Missed'],
        ['followed', 'Followed Up'],
        ['missed_sla', 'Missed SLA'],
        [null, 'Actions'],
    ];

    return (
        <div className="space-y-4 lg:space-y-6 text-textPrimary px-1 sm:px-0">
            <div>
                <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-textPrimary">Branch Call Logs Summary</h1>
                <p className="mt-1 text-xs lg:text-sm text-textSecondary">
                    View and filter call performance across all assigned spa locations.
                </p>
            </div>

            <SummaryFilter
                filters={draftFilters}
                onChange={setDraftFilters}
                onApply={(nextFilters = draftFilters) => {
                    setDraftFilters(nextFilters);
                    setActiveFilters(nextFilters);
                    setPage(1);
                }}
                onClear={() => {
                    setDraftFilters(defaultFilters);
                    setActiveFilters(defaultFilters);
                    setPage(1);
                }}
            />

            {error && (
                <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-xs lg:text-sm text-danger">
                    {error}
                </div>
            )}

            <div className="space-y-4">
                {/* 1. DESKTOP/TABLET TABLE VIEW (Hidden on Mobile) */}
                <div className="hidden md:block overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
                    <div className="overflow-x-auto scrollbar-thin">
                        <table className="min-w-full divide-y divide-border">
                            <thead className="bg-cardHover sticky top-0 z-10">
                                <tr>
                                    {columns.map(([sortKey, label]) => (
                                        <th
                                            key={label}
                                            className={`px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wide text-textSecondary ${sortKey ? 'cursor-pointer hover:text-primary select-none' : ''}`}
                                            onClick={() => sortKey && sortBy(sortKey)}
                                        >
                                            <span className="inline-flex items-center gap-1">
                                                {label}
                                                {sortKey && sortConfig.key === sortKey && (
                                                    <span className="text-primary font-bold">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                                                )}
                                            </span>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border bg-background">
                                {loading ? (
                                    <tr>
                                        <td colSpan="9" className="px-4 py-16 text-center text-sm text-textSecondary">
                                            Loading summary data...
                                        </td>
                                    </tr>
                                ) : summaries.length === 0 ? (
                                    <tr>
                                        <td colSpan="9" className="px-4 py-16 text-center text-sm text-textSecondary">
                                            No assigned SPA summary found for these filters.
                                        </td>
                                    </tr>
                                ) : (
                                    summaries.map((row) => (
                                        <tr key={row.branch_id} className="transition hover:bg-cardHover">
                                            <td className="px-4 py-3.5 text-sm font-bold uppercase text-textPrimary">
                                                {row.branch_name || 'Unknown Branch'}
                                            </td>
                                            <td className="px-4 py-3.5">
                                                <p className="text-sm font-semibold uppercase text-textPrimary">{row.area || 'N/A'}</p>
                                                <p className="text-xs uppercase text-textSecondary">{row.city || 'N/A'}</p>
                                            </td>
                                            <td className="px-4 py-3.5 text-sm font-bold text-textPrimary">{row.total_calls || 0}</td>
                                            <td className="px-4 py-3.5 text-sm font-semibold text-info">{row.total_outgoing || 0}</td>
                                            <td className="px-4 py-3.5 text-sm font-semibold text-success">{row.total_incoming || 0}</td>
                                            <td className="px-4 py-3.5 text-sm font-semibold text-danger">{row.total_missed || 0}</td>
                                            <td className="px-4 py-3.5 text-sm font-semibold text-success">{row.total_followed || 0}</td>
                                            <td className="px-4 py-3.5 text-sm font-semibold text-danger">{row.total_missed_sla || 0}</td>
                                            <td className="px-4 py-3.5">
                                                <button
                                                    type="button"
                                                    onClick={() => openDetails(row)}
                                                    className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-textPrimary transition hover:border-primary hover:text-primary active:scale-[0.98]"
                                                >
                                                    Details
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* 2. MOBILE CARD VIEW (Visible only on Mobile) */}
                <div className="block md:hidden space-y-3">
                    {loading ? (
                        Array.from({ length: 4 }).map((_, index) => (
                            <div key={index} className="rounded-2xl border border-border bg-card p-4 space-y-3 animate-pulse">
                                <div className="h-4 bg-border rounded-md w-3/4" />
                                <div className="h-3 bg-border rounded-md w-1/2" />
                                <div className="grid grid-cols-3 gap-2 pt-2">
                                    <div className="h-10 bg-border rounded-lg" />
                                    <div className="h-10 bg-border rounded-lg" />
                                    <div className="h-10 bg-border rounded-lg" />
                                </div>
                            </div>
                        ))
                    ) : summaries.length === 0 ? (
                        <div className="rounded-2xl border border-border bg-card p-10 text-center text-sm text-textSecondary italic">
                            No assigned SPA summary found for these filters.
                        </div>
                    ) : (
                        summaries.map((row) => (
                            <div
                                key={row.branch_id}
                                onClick={() => openDetails(row)}
                                className="group rounded-2xl border border-border bg-card p-4 shadow-sm transition-all duration-200 hover:border-primary/40 active:scale-[0.98] cursor-pointer relative"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="min-w-0 flex-1 pr-4">
                                        <h3 className="font-bold text-sm text-textPrimary uppercase tracking-tight truncate">
                                            {row.branch_name || 'Unknown Branch'}
                                        </h3>
                                        <p className="text-[10px] text-textSecondary uppercase font-medium mt-0.5">
                                            {row.area || 'N/A'} · {row.city || 'N/A'}
                                        </p>
                                    </div>
                                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary font-bold text-xs select-none">
                                        →
                                    </span>
                                </div>

                                <div className="mt-3.5 grid grid-cols-3 gap-2 border-t border-border/60 pt-3">
                                    <div className="text-center rounded-xl bg-background border border-border/30 p-2">
                                        <span className="block text-[9px] font-semibold text-textSecondary uppercase tracking-wide">Total</span>
                                        <span className="text-xs font-bold text-textPrimary">{row.total_calls || 0}</span>
                                    </div>
                                    <div className="text-center rounded-xl bg-info/10 p-2">
                                        <span className="block text-[9px] font-semibold text-info uppercase tracking-wide">Out</span>
                                        <span className="text-xs font-bold text-info">{row.total_outgoing || 0}</span>
                                    </div>
                                    <div className="text-center rounded-xl bg-success/10 p-2">
                                        <span className="block text-[9px] font-semibold text-success uppercase tracking-wide">In</span>
                                        <span className="text-xs font-bold text-success">{row.total_incoming || 0}</span>
                                    </div>
                                </div>

                                <div className="mt-2 grid grid-cols-3 gap-2">
                                    <div className="text-center rounded-xl bg-danger/10 p-2">
                                        <span className="block text-[9px] font-semibold text-danger uppercase tracking-wide">Missed</span>
                                        <span className="text-xs font-bold text-danger">{row.total_missed || 0}</span>
                                    </div>
                                    <div className="text-center rounded-xl bg-success-bg p-2">
                                        <span className="block text-[9px] font-semibold text-success uppercase tracking-wide">Followed</span>
                                        <span className="text-xs font-bold text-success">{row.total_followed || 0}</span>
                                    </div>
                                    <div className="text-center rounded-xl bg-danger-bg p-2">
                                        <span className="block text-[9px] font-semibold text-danger uppercase tracking-wide">SLA Miss</span>
                                        <span className="text-xs font-bold text-danger">{row.total_missed_sla || 0}</span>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Responsive Pagination Footer */}
                {!loading && totalCount > PAGE_SIZE && (
                    <div className="flex flex-col sm:flex-row gap-3 items-center justify-between border border-border rounded-2xl bg-card px-4 py-3 shadow-soft">
                        <p className="text-xs lg:text-sm text-textSecondary font-medium">
                            Showing page {page} of {totalPages} · {totalCount} records
                        </p>
                        <div className="flex gap-2 w-full sm:w-auto">
                            <button
                                type="button"
                                disabled={page <= 1}
                                onClick={() => setPage((current) => Math.max(1, current - 1))}
                                className="h-10 flex-1 sm:flex-initial rounded-xl border border-border px-4 text-xs lg:text-sm font-semibold text-textSecondary transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-40 active:scale-[0.98]"
                            >
                                Previous
                            </button>
                            <button
                                type="button"
                                disabled={page >= totalPages}
                                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                                className="h-10 flex-1 sm:flex-initial rounded-xl border border-border px-4 text-xs lg:text-sm font-semibold text-textSecondary transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-40 active:scale-[0.98]"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CallLogSummary;

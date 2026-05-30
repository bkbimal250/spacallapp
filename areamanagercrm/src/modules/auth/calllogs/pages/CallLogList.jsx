import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { callLogsAPI } from '../api';
import { branchesAPI } from '../../branches/api';
import { useAuth } from '../../../shared/hooks/useAuth';

const PAGE_SIZE = 25;

const formatDate = (value) => {
    if (!value) return 'N/A';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
};

const maskPhoneNumber = (value) => {
    if (!value) return 'N/A';
    const text = String(value);
    const digits = text.replace(/\D/g, '');
    if (digits.length <= 4) return digits;

    const masked = `${'*'.repeat(digits.length - 4)}${digits.slice(-4)}`;
    return text.trim().startsWith('+') ? `+${masked}` : masked;
};

const sanitizeFiltersForRole = (filters, user) => {
    const clean = { ...filters };

    if (user?.role === 'area_manager') {
        delete clean.branch_group;
    }

    return Object.fromEntries(
        Object.entries(clean).filter(([, value]) => value !== undefined && value !== null && value !== '')
    );
};

const filtersFromSearch = (search, user) => {
    const params = new URLSearchParams(search);
    return sanitizeFiltersForRole({
        search: params.get('search') || '',
        quick_date: params.get('quick_date') || 'today',
        start_date: params.get('start_date') || '',
        end_date: params.get('end_date') || '',
        call_type: params.get('call_type') || '',
        branch: params.get('branch') || '',
        branch_group: params.get('branch_group') || '',
        is_unique: params.get('is_unique') === 'true' ? 'true' : '',
    }, user);
};

const branchLabel = (branch) => branch.code ? `${branch.spa_name} (${branch.code})` : branch.spa_name;

const StatCard = ({ label, value }) => (
    <div className="rounded-2xl border border-border bg-card p-3 lg:p-4 shadow-sm transition-all duration-200 hover:border-primary/40 active:scale-[0.98] select-none">
        <p className="text-[10px] lg:text-xs font-semibold uppercase tracking-wider text-textSecondary">{label}</p>
        <p className="mt-1 lg:mt-2 text-xl lg:text-2xl font-bold tracking-tight text-textPrimary">{value ?? 0}</p>
    </div>
);

const CallLogList = ({ compactHeader = false }) => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [filters, setFilters] = useState(() => filtersFromSearch(location.search, user));
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);
    const [branches, setBranches] = useState([]);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [statsLoading, setStatsLoading] = useState(true);
    const [error, setError] = useState('');
    const [branchPanelOpen, setBranchPanelOpen] = useState(false);

    const isAreaManager = user?.role === 'area_manager';
    const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));
    const selectedBranchIds = useMemo(
        () => String(filters.branch || '').split(',').map((item) => item.trim()).filter(Boolean),
        [filters.branch],
    );
    const selectedBranches = useMemo(
        () => branches.filter((branch) => selectedBranchIds.includes(String(branch.id))),
        [branches, filters.branch],
    );
    const selectedBranchCount = selectedBranchIds.length;

    useEffect(() => {
        setFilters(filtersFromSearch(location.search, user));
        setPage(1);
    }, [location.search, user]);

    useEffect(() => {
        const fetchBranches = async () => {
            try {
                const response = await branchesAPI.getBranches({ all: true });
                const branchData = response.data.results || response.data || [];
                setBranches(branchData);
            } catch (err) {
                setBranches([]);
            }
        };
        fetchBranches();
    }, []);

    const selectedBranchLabel = selectedBranches.length === 1
        ? branchLabel(selectedBranches[0])
        : '';

    const setSelectedBranchIds = (ids) => {
        handleInputChange('branch', ids.join(','));
    };

    const toggleBranch = (branchId) => {
        const value = String(branchId);
        const nextIds = selectedBranchIds.includes(value)
            ? selectedBranchIds.filter((id) => id !== value)
            : [...selectedBranchIds, value];
        setSelectedBranchIds(nextIds);
    };

    const updateUrlFilters = useCallback((nextFilters) => {
        const clean = sanitizeFiltersForRole(nextFilters, user);
        const params = new URLSearchParams();
        Object.entries(clean).forEach(([key, value]) => {
            if (value !== false) {
                params.set(key, String(value));
            }
        });
        navigate(params.toString() ? `?${params.toString()}` : location.pathname, { replace: true });
    }, [location.pathname, navigate, user]);

    const fetchLogs = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const requestFilters = sanitizeFiltersForRole(filters, user);
            const response = await callLogsAPI.getCallLogs({
                ...requestFilters,
                page,
                page_size: PAGE_SIZE,
                ordering: '-call_time',
            });
            const data = response.data || {};
            setLogs(data.results || data || []);
            setTotalCount(data.count ?? (Array.isArray(data) ? data.length : 0));
        } catch (err) {
            setError('Unable to load call logs right now.');
            setLogs([]);
            setTotalCount(0);
        } finally {
            setLoading(false);
        }
    }, [filters, page, user]);

    const fetchStats = useCallback(async () => {
        setStatsLoading(true);
        try {
            const response = await callLogsAPI.getCallLogStats(sanitizeFiltersForRole(filters, user));
            setStats(response.data);
        } catch (err) {
            setStats(null);
        } finally {
            setStatsLoading(false);
        }
    }, [filters, user]);

    useEffect(() => {
        fetchLogs();
        fetchStats();
    }, [fetchLogs, fetchStats]);

    const handleInputChange = (key, value) => {
        setFilters((current) => ({ ...current, [key]: value }));
    };

    const applyFilters = () => {
        setPage(1);
        updateUrlFilters(filters);
    };

    const clearFilters = () => {
        setPage(1);
        updateUrlFilters({ quick_date: 'today', branch: filters.branch || '' });
    };


    return (
        <div className="space-y-4 lg:space-y-6 text-textPrimary px-1 sm:px-0">
            {!compactHeader && (
                <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <p className="text-xs lg:text-sm font-semibold uppercase tracking-wider text-primary">Area Manager</p>
                        <h1 className="mt-0.5 text-xl lg:text-2xl font-bold tracking-tight text-textPrimary">
                            {selectedBranchLabel ? `${selectedBranchLabel} Call Logs` : 'Call Logs'}
                        </h1>
                        <p className="mt-1 text-xs lg:text-sm text-textSecondary">Showing calls from selected assigned SPA access.</p>
                    </div>
                </div>
            )}

            <form
                className="rounded-2xl border border-border bg-card p-4 md:p-5 shadow-sm space-y-4"
                onSubmit={(event) => {
                    event.preventDefault();
                    applyFilters();
                }}
            >
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_auto] sm:items-end relative">
                    <div className="relative">
                        <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-textSecondary">Check SPA / Branch</span>
                        <button
                            type="button"
                            onClick={() => setBranchPanelOpen((open) => !open)}
                            className="flex h-11 w-full items-center justify-between rounded-xl border border-border bg-background px-3.5 py-2 text-left text-sm text-textPrimary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
                        >
                            <span className="truncate pr-4">
                                {selectedBranchCount === 0
                                    ? 'All assigned SPAs'
                                    : selectedBranchCount === 1
                                        ? selectedBranchLabel
                                        : `${selectedBranchCount} SPAs selected`}
                            </span>
                            <span className="text-textSecondary text-[10px] select-none">{branchPanelOpen ? '▲' : '▼'}</span>
                        </button>

                        {branchPanelOpen && (
                            <>
                                {/* Mobile Bottom Drawer Background Backdrop */}
                                <div 
                                    className="fixed inset-0 z-30 bg-slate-900/60 backdrop-blur-xs md:hidden"
                                    onClick={() => setBranchPanelOpen(false)}
                                />
                                
                                {/* Branch Selector Drawer Panel */}
                                <div className="fixed inset-x-4 bottom-4 z-40 max-h-[80vh] rounded-2xl border border-border bg-card shadow-large flex flex-col md:absolute md:inset-x-0 md:bottom-auto md:top-full md:z-20 md:mt-2 md:max-h-80 md:rounded-xl md:shadow-medium overflow-hidden">
                                    <div className="flex flex-col gap-2 border-b border-border p-3.5 sm:flex-row sm:items-center sm:justify-between bg-cardHover/60">
                                        <p className="text-xs font-bold uppercase tracking-wider text-textSecondary">
                                            {selectedBranchCount || 'All'} selected
                                        </p>
                                        <div className="flex gap-2">
                                            <button
                                                type="button"
                                                onClick={() => setSelectedBranchIds(branches.map((branch) => String(branch.id)))}
                                                className="rounded-lg border border-border px-2.5 py-1 text-xs font-semibold text-textSecondary bg-background hover:border-primary hover:text-primary active:scale-95"
                                            >
                                                Select all
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setSelectedBranchIds([])}
                                                className="rounded-lg border border-border px-2.5 py-1 text-xs font-semibold text-textSecondary bg-background hover:border-danger hover:text-danger active:scale-95"
                                            >
                                                Clear
                                            </button>
                                        </div>
                                    </div>
                                    <div className="max-h-[60vh] md:max-h-64 overflow-y-auto p-2 scrollbar-thin bg-background/50">
                                        {branches.map((branch) => {
                                            const checked = selectedBranchIds.includes(String(branch.id));
                                            return (
                                                <label
                                                    key={branch.id}
                                                    className={`flex items-start gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-150 cursor-pointer ${
                                                        checked ? 'bg-primarySoft/70 text-textPrimary' : 'hover:bg-cardHover'
                                                    }`}
                                                >
                                                    <input
                                                        type="checkbox"
                                                        checked={checked}
                                                        onChange={() => toggleBranch(branch.id)}
                                                        className="mt-0.5 h-4.5 w-4.5 rounded border-border text-primary focus:ring-primary cursor-pointer"
                                                    />
                                                    <span className="min-w-0 flex-1">
                                                        <span className="block font-semibold text-textPrimary truncate">{branch.spa_name}</span>
                                                        <span className="text-[10px] font-medium text-textSecondary uppercase">{branch.code || branch.city || 'Assigned SPA'}</span>
                                                    </span>
                                                </label>
                                            );
                                        })}
                                    </div>
                                    {/* Mobile bottom sheet close button */}
                                    <div className="p-3 bg-card border-t border-border/80 md:hidden">
                                        <button
                                            type="button"
                                            onClick={() => setBranchPanelOpen(false)}
                                            className="w-full h-10 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary/95 active:scale-[0.98]"
                                        >
                                            Confirm Selection
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    <button
                        type="submit"
                        onClick={() => setBranchPanelOpen(false)}
                        className="h-11 rounded-xl border border-primary bg-primarySoft px-5 text-sm font-semibold text-primary transition hover:bg-primary hover:text-white active:scale-[0.98]"
                    >
                        Check
                    </button>
                </div>

                <div className="rounded-xl border border-primary/20 bg-primarySoft/40 px-3.5 py-2 text-xs lg:text-sm text-textSecondary">
                    <span className="font-semibold text-textPrimary">Current scope:</span>{' '}
                    {selectedBranchCount === 0
                        ? `${branches.length || 0} assigned SPAs`
                        : selectedBranchCount === 1
                            ? selectedBranchLabel
                            : `${selectedBranchCount} selected SPAs`}
                </div>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-5 pt-1">
                    <label className="block sm:col-span-2">
                        <span className="mb-1 block text-xs font-semibold uppercase tracking-wider text-textSecondary">Search Contact</span>
                        <input
                            value={filters.search || ''}
                            onChange={(event) => handleInputChange('search', event.target.value)}
                            placeholder="Phone number or contact name"
                            className="h-11 w-full rounded-xl border border-border bg-background px-3.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
                        />
                    </label>

                    <label className="block">
                        <span className="mb-1 block text-xs font-semibold uppercase tracking-wider text-textSecondary">Date range</span>
                        <select
                            value={filters.quick_date || 'today'}
                            onChange={(event) => handleInputChange('quick_date', event.target.value)}
                            className="h-11 w-full rounded-xl border border-border bg-background px-3 text-sm outline-none transition focus:border-primary"
                        >
                            <option value="today">Today</option>
                            <option value="yesterday">Yesterday</option>
                            <option value="all">All Time</option>
                        </select>
                    </label>

                    <label className="block">
                        <span className="mb-1 block text-xs font-semibold uppercase tracking-wider text-textSecondary">Call Type</span>
                        <select
                            value={filters.call_type || ''}
                            onChange={(event) => handleInputChange('call_type', event.target.value)}
                            className="h-11 w-full rounded-xl border border-border bg-background px-3 text-sm outline-none transition focus:border-primary"
                        >
                            <option value="">All Types</option>
                            <option value="incoming">Incoming</option>
                            <option value="outgoing">Outgoing</option>
                            <option value="missed">Missed</option>
                            <option value="rejected">Rejected</option>
                        </select>
                    </label>

                    <label className="flex items-center gap-2.5 rounded-xl border border-border bg-background px-3.5 h-11 mt-6 cursor-pointer select-none">
                        <input
                            type="checkbox"
                            checked={filters.is_unique === 'true'}
                            onChange={(event) => handleInputChange('is_unique', event.target.checked ? 'true' : '')}
                            className="h-4.5 w-4.5 rounded border-border text-primary focus:ring-primary cursor-pointer"
                        />
                        <span className="text-sm font-semibold text-textSecondary">Unique records</span>
                    </label>
                </div>

                <div className="mt-4 flex flex-wrap gap-2 pt-1 border-t border-border/40">
                    <button
                        type="button"
                        onClick={() => navigate('/')}
                        className="h-10 flex-1 sm:flex-initial rounded-xl border border-border px-4 text-xs lg:text-sm font-semibold text-textSecondary transition hover:border-primary hover:text-primary hover:bg-primary/5 active:scale-[0.98]"
                    >
                        Back to Summary
                    </button>
                    <button
                        type="submit"
                        onClick={() => setBranchPanelOpen(false)}
                        className="h-10 flex-[1.4] sm:flex-initial rounded-xl bg-primary px-5 text-xs lg:text-sm font-semibold text-white transition hover:bg-primary/90 active:scale-[0.98]"
                    >
                        Apply Filter
                    </button>
                    <button
                        type="button"
                        onClick={clearFilters}
                        className="h-10 flex-1 sm:flex-initial rounded-xl border border-border px-4 text-xs lg:text-sm font-semibold text-textSecondary transition hover:border-primary hover:text-primary hover:bg-primary/5 active:scale-[0.98]"
                    >
                        Clear
                    </button>
                </div>
            </form>

            {/* KPI Cards Grid */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                {statsLoading ? (
                    Array.from({ length: 6 }).map((_, index) => (
                        <div key={index} className="h-18 lg:h-24 animate-pulse rounded-2xl border border-border bg-card" />
                    ))
                ) : (
                    <>
                        <StatCard label="Total" value={stats?.total} />
                        <StatCard label="Incoming" value={stats?.incoming} />
                        <StatCard label="Outgoing" value={stats?.outgoing} />
                        <StatCard label="Missed" value={stats?.missed} />
                        <StatCard label="Rejected" value={stats?.rejected} />
                        <StatCard label="Unique" value={stats?.unique_count} />
                    </>
                )}
            </div>

            {/* Call Logs View */}
            <div className="space-y-4">
                {/* 1. DESKTOP CALL LOGS TABLE */}
                <div className="hidden md:block overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
                    <div className="overflow-x-auto scrollbar-thin">
                        <table className="min-w-full divide-y divide-border">
                            <thead className="bg-cardHover sticky top-0 z-10">
                                <tr>
                                    {['Type', 'Phone Number', 'Branch', 'Device', 'Duration', 'Call Time', 'Follow-up'].map((header) => (
                                        <th key={header} className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wide text-textSecondary select-none">
                                            {header}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border bg-background">
                                {loading ? (
                                    <tr>
                                        <td colSpan="7" className="px-4 py-16 text-center text-sm text-textSecondary">
                                            Loading call logs...
                                        </td>
                                    </tr>
                                ) : logs.length === 0 ? (
                                    <tr>
                                        <td colSpan="7" className="px-4 py-16 text-center text-sm text-textSecondary">
                                            No call logs found for your assigned branch access.
                                        </td>
                                    </tr>
                                ) : (
                                    logs.map((log) => (
                                        <tr key={log.id} className="transition hover:bg-cardHover">
                                            <td className="px-4 py-3.5 text-sm capitalize text-textPrimary font-semibold">{log.call_type || 'N/A'}</td>
                                            <td className="px-4 py-3.5">
                                                <p className="text-sm font-bold text-textPrimary tracking-wide">{maskPhoneNumber(log.phone_number)}</p>
                                                {log.contact_name && <p className="text-xs text-textSecondary mt-0.5">{log.contact_name}</p>}
                                            </td>
                                            <td className="px-4 py-3.5 text-sm text-textSecondary uppercase font-medium">{log.branch_name || 'Assigned branch'}</td>
                                            <td className="px-4 py-3.5">
                                                <p className="text-sm text-textPrimary font-semibold">{log.phone_name || 'Device'}</p>
                                                <p className="text-xs font-mono text-textSecondary mt-0.5">{log.device_uid || 'N/A'}</p>
                                            </td>
                                            <td className="px-4 py-3.5 text-sm text-textSecondary font-semibold">{log.duration ?? 0}s</td>
                                            <td className="px-4 py-3.5 text-sm text-textSecondary">{formatDate(log.call_time)}</td>
                                            <td className="px-4 py-3.5 text-sm">
                                                {log.call_type === 'missed' ? (
                                                    <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-bold ${
                                                        log.is_followed_up ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
                                                    }`}>
                                                        {log.is_followed_up ? (log.followup_status || 'Followed') : 'Pending'}
                                                    </span>
                                                ) : (
                                                    <span className="text-textSecondary">-</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* 2. MOBILE CALL LOGS FEED VIEW */}
                <div className="block md:hidden space-y-3">
                    {loading ? (
                        Array.from({ length: 4 }).map((_, index) => (
                            <div key={index} className="rounded-2xl border border-border bg-card p-4 space-y-3 animate-pulse">
                                <div className="flex items-center justify-between">
                                    <div className="h-5 bg-border rounded-full w-20" />
                                    <div className="h-3 bg-border rounded-md w-24" />
                                </div>
                                <div className="h-10 bg-border rounded-xl w-full" />
                                <div className="grid grid-cols-2 gap-2 pt-1">
                                    <div className="h-8 bg-border rounded-lg" />
                                    <div className="h-8 bg-border rounded-lg" />
                                </div>
                            </div>
                        ))
                    ) : logs.length === 0 ? (
                        <div className="rounded-2xl border border-border bg-card p-10 text-center text-sm text-textSecondary italic">
                            No call logs found for your assigned branch access.
                        </div>
                    ) : (
                        logs.map((log) => (
                            <div
                                key={log.id}
                                className="rounded-2xl border border-border bg-card p-4 shadow-sm space-y-3 hover:border-primary/30 transition duration-150 active:scale-[0.99]"
                            >
                                {/* Top Row: Call Type Badge & Time */}
                                <div className="flex items-center justify-between">
                                    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold select-none ${
                                        log.call_type === 'incoming' ? 'bg-success/10 text-success border border-success/20' :
                                        log.call_type === 'outgoing' ? 'bg-info/10 text-info border border-info/20' :
                                        log.call_type === 'missed' ? 'bg-danger/10 text-danger border border-danger/20' :
                                        'bg-warning/10 text-warning border border-warning/20'
                                    }`}>
                                        <span className="h-1.5 w-1.5 rounded-full bg-current" />
                                        <span className="capitalize">{log.call_type || 'Call'}</span>
                                    </span>
                                    <span className="text-[10px] text-textSecondary font-medium">
                                        {formatDate(log.call_time)}
                                    </span>
                                </div>

                                {/* Middle Row: Contact & Duration */}
                                <div className="flex justify-between items-center bg-background/50 rounded-xl p-3 border border-border/40">
                                    <div className="min-w-0 flex-1">
                                        <p className="text-sm font-bold text-textPrimary tracking-wide">
                                            {maskPhoneNumber(log.phone_number)}
                                        </p>
                                        {log.contact_name && (
                                            <p className="text-xs text-textSecondary font-semibold mt-0.5 truncate">
                                                {log.contact_name}
                                            </p>
                                        )}
                                    </div>
                                    <div className="text-right pl-3 select-none">
                                        <p className="text-xs font-bold text-textPrimary">{log.duration ?? 0}s</p>
                                        <p className="text-[9px] text-textSecondary uppercase font-bold tracking-wide">Duration</p>
                                    </div>
                                </div>

                                {/* Bottom Row: Metadata Grid */}
                                <div className="grid grid-cols-2 gap-x-4 gap-y-2 pt-1 text-[11px] leading-relaxed">
                                    <div>
                                        <span className="text-[9px] text-textSecondary block uppercase font-bold tracking-wide">Branch</span>
                                        <span className="font-semibold text-textPrimary truncate block uppercase">{log.branch_name || 'Assigned branch'}</span>
                                    </div>
                                    <div>
                                        <span className="text-[9px] text-textSecondary block uppercase font-bold tracking-wide">Device</span>
                                        <span className="font-semibold text-textPrimary truncate block">{log.phone_name || 'Device'}</span>
                                    </div>
                                    <div className="col-span-2 border-t border-border/50 pt-2 flex items-center justify-between">
                                        <div className="min-w-0 pr-4">
                                            <span className="text-[9px] text-textSecondary block uppercase font-bold tracking-wide">Device ID</span>
                                            <span className="font-mono text-[10px] text-textSecondary truncate max-w-[150px] block">{log.device_uid || 'N/A'}</span>
                                        </div>
                                        <div>
                                            {log.call_type === 'missed' && (
                                                <span className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-[10px] font-extrabold uppercase select-none ${
                                                    log.is_followed_up ? 'bg-success/15 text-success border border-success/20' : 'bg-warning/15 text-warning border border-warning/20'
                                                }`}>
                                                    {log.is_followed_up ? (log.followup_status || 'Followed') : 'Pending'}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Responsive Pagination Footer */}
                <div className="flex flex-col gap-3 border-t border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between bg-card rounded-2xl shadow-soft">
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
            </div>
        </div>
    );
};

export default CallLogList;

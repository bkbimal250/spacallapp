import React, { useState, useCallback, useEffect, memo } from 'react';
import { 
    Search, 
    Calendar,
    Filter,
    X,
    MapPin,
    Activity
} from 'lucide-react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';

/**
 * CallLogsSummaryFilter Component
 * Provides advanced filtering for the Call Log Summary page with a premium UI.
 */
const CallLogsSummaryFilter = ({ 
    onFilter, 
    initialFilters = {} 
}) => {
    // Search states
    const [search, setSearch] = useState(initialFilters.branch_search || '');
    const [city, setCity] = useState(initialFilters.city || '');
    const [status, setStatus] = useState(initialFilters.status || '');

    // Date Mode states: 'preset', 'single', 'range'
    const [dateMode, setDateMode] = useState(() => {
        if (initialFilters.start_date && initialFilters.end_date) {
            return initialFilters.start_date === initialFilters.end_date ? 'single' : 'range';
        }
        return 'preset';
    });

    // Sub-date states
    const [quickDate, setQuickDate] = useState(initialFilters.quick_date || 'today');
    const [singleDate, setSingleDate] = useState(
        initialFilters.start_date === initialFilters.end_date ? initialFilters.start_date : ''
    );
    const [dateRange, setDateRange] = useState({ 
        startDate: initialFilters.start_date || '', 
        endDate: initialFilters.end_date || '' 
    });

    // Sync with initialFilters if they change
    useEffect(() => {
        setSearch(initialFilters.branch_search || '');
        setCity(initialFilters.city || '');
        setStatus(initialFilters.status || '');
        
        if (initialFilters.start_date && initialFilters.end_date) {
            if (initialFilters.start_date === initialFilters.end_date) {
                setDateMode('single');
                setSingleDate(initialFilters.start_date);
                setDateRange({ startDate: initialFilters.start_date, endDate: initialFilters.end_date });
            } else {
                setDateMode('range');
                setSingleDate('');
                setDateRange({ startDate: initialFilters.start_date, endDate: initialFilters.end_date });
            }
            setQuickDate('');
        } else {
            setDateMode('preset');
            setQuickDate(initialFilters.quick_date || 'today');
            setSingleDate('');
            setDateRange({ startDate: '', endDate: '' });
        }
    }, [initialFilters]);

    const handleApplyFilters = useCallback(() => {
        const filters = {
            branch_search: search.trim() || undefined,
            city: city.trim() || undefined,
            status: status || undefined,
        };

        if (dateMode === 'single') {
            if (singleDate) {
                filters.start_date = singleDate;
                filters.end_date = singleDate;
                filters.quick_date = undefined;
            }
        } else if (dateMode === 'range') {
            if (dateRange.startDate) filters.start_date = dateRange.startDate;
            if (dateRange.endDate) filters.end_date = dateRange.endDate;
            filters.quick_date = undefined;
        } else {
            filters.quick_date = quickDate;
            filters.start_date = undefined;
            filters.end_date = undefined;
        }

        // Clean undefined values
        const cleanFilters = Object.fromEntries(
            Object.entries(filters).filter(([_, v]) => v !== undefined)
        );
        
        onFilter(cleanFilters);
    }, [search, city, status, dateMode, quickDate, singleDate, dateRange, onFilter]);

    const handleClear = useCallback(() => {
        setSearch('');
        setCity('');
        setStatus('');
        setQuickDate('today');
        setSingleDate('');
        setDateRange({ startDate: '', endDate: '' });
        setDateMode('preset');
        onFilter({ quick_date: 'today' });
    }, [onFilter]);

    const handleQuickDateChange = (preset) => {
        setQuickDate(preset);
        setDateMode('preset');
        // Auto-apply for presets
        onFilter({
            branch_search: search.trim() || undefined,
            city: city.trim() || undefined,
            status: status || undefined,
            quick_date: preset
        });
    };

    const handleSingleDateChange = (date) => {
        setSingleDate(date);
        if (date) {
            // Auto-apply for single date selection
            onFilter({
                branch_search: search.trim() || undefined,
                city: city.trim() || undefined,
                status: status || undefined,
                start_date: date,
                end_date: date
            });
        }
    };

    const datePresets = [
        { id: 'today', label: 'Today' },
        { id: 'yesterday', label: 'Yesterday' }
    ];

    return (
        <div className="bg-card rounded-xl border border-border shadow-sm transition-all duration-300 mb-6">
            <div className="p-5 space-y-6">
                {/* ── TOP SECTION: DATE MODES & BRANCH SEARCH ── */}
                <div className="flex flex-col lg:flex-row gap-6 items-start lg:items-center justify-between">
                    <div className="flex flex-wrap items-center gap-2">
                        <div className="flex items-center gap-2 mr-2 text-text-secondary">
                            <Calendar size={18} className="text-primary" />
                            <span className="text-sm font-semibold uppercase tracking-wider">Period</span>
                        </div>
                        <div className="flex items-center p-1 bg-background rounded-lg border border-border">
                            {datePresets.map(preset => (
                                <button
                                    key={preset.id}
                                    onClick={() => handleQuickDateChange(preset.id)}
                                    className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all duration-200 ${
                                        dateMode === 'preset' && quickDate === preset.id
                                            ? 'bg-primary text-white shadow-md'
                                            : 'text-text-secondary hover:bg-cardHover hover:text-text-primary'
                                    }`}
                                >
                                    {preset.label}
                                </button>
                            ))}
                            <button
                                onClick={() => setDateMode('single')}
                                className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all duration-200 ${
                                    dateMode === 'single'
                                        ? 'bg-primary text-white shadow-md'
                                        : 'text-text-secondary hover:bg-cardHover hover:text-text-primary'
                                }`}
                            >
                                Quick Date
                            </button>
                            <button
                                onClick={() => setDateMode('range')}
                                className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all duration-200 ${
                                    dateMode === 'range'
                                        ? 'bg-primary text-white shadow-md'
                                        : 'text-text-secondary hover:bg-cardHover hover:text-text-primary'
                                }`}
                            >
                                Custom (Range)
                            </button>
                        </div>
                    </div>

                    <div className="w-full lg:w-96 relative">
                        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
                        <Input
                            placeholder="Search branch name or code..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleApplyFilters()}
                            className="pl-10 h-10 bg-background border-border-light hover:border-primary focus:border-primary transition-colors"
                        />
                    </div>
                </div>

                {/* ── MIDDLE SECTION: CONDITIONAL DATE INPUTS ── */}
                {dateMode !== 'preset' && (
                    <div className="p-4 bg-background/50 rounded-lg border border-border-light animate-in fade-in slide-in-from-top-2 duration-300">
                        <div className="flex flex-wrap items-center gap-4">
                            {dateMode === 'single' ? (
                                <div className="space-y-1">
                                    <label className="text-[10px] uppercase font-bold text-text-secondary ml-1 tracking-wider">Select Date</label>
                                    <input
                                        type="date"
                                        className="block px-3 py-2 bg-card border border-border rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                        value={singleDate}
                                        onChange={(e) => handleSingleDateChange(e.target.value)}
                                    />
                                </div>
                            ) : (
                                <>
                                    <div className="space-y-1">
                                        <label className="text-[10px] uppercase font-bold text-text-secondary ml-1 tracking-wider">Start Date</label>
                                        <input
                                            type="date"
                                            className="block px-3 py-2 bg-card border border-border rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                            value={dateRange.startDate}
                                            onChange={(e) => setDateRange(prev => ({ ...prev, startDate: e.target.value }))}
                                        />
                                    </div>
                                    <span className="mt-5 text-text-secondary">—</span>
                                    <div className="space-y-1">
                                        <label className="text-[10px] uppercase font-bold text-text-secondary ml-1 tracking-wider">End Date</label>
                                        <input
                                            type="date"
                                            className="block px-3 py-2 bg-card border border-border rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                            value={dateRange.endDate}
                                            onChange={(e) => setDateRange(prev => ({ ...prev, endDate: e.target.value }))}
                                        />
                                    </div>
                                </>
                            )}
                            <Button 
                                variant="outline" 
                                size="sm" 
                                className="mt-5 text-xs border-border-light hover:bg-card"
                                onClick={() => setDateMode('preset')}
                            >
                                <X size={14} className="mr-1" /> Close
                            </Button>
                        </div>
                    </div>
                )}

                {/* ── BOTTOM SECTION: ADVANCED FILTERS (CITY, STATUS) ── */}
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 pt-2 border-t border-border-light/50">
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2 mb-1">
                            <MapPin size={15} className="text-primary/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary tracking-widest">City</span>
                        </div>
                        <Input
                            placeholder="All Cities"
                            value={city}
                            onChange={(e) => setCity(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleApplyFilters()}
                            className="bg-background border-border-light hover:border-primary focus:border-primary transition-colors"
                        />
                    </div>

                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2 mb-1">
                            <Activity size={15} className="text-primary/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary tracking-widest">Status</span>
                        </div>
                        <select
                            className="block w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none appearance-none cursor-pointer"
                            value={status}
                            onChange={(e) => setStatus(e.target.value)}
                        >
                            <option value="">All Statuses</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                        </select>
                    </div>

                    <div className="lg:col-span-2 flex items-end gap-3 justify-end">
                        <div className="flex gap-2 h-[42px]">
                            <Button
                                variant="outline"
                                onClick={handleClear}
                                className="border-border hover:bg-cardHover text-text-secondary flex items-center gap-2 px-4 shadow-sm"
                                title="Clear All"
                            >
                                <X size={16} /> <span className="font-semibold text-xs">Clear</span>
                            </Button>

                            <Button
                                onClick={handleApplyFilters}
                                className="bg-primary hover:bg-primary-dark text-white px-8 font-bold shadow-lg shadow-primary/20 flex items-center gap-2"
                            >
                                <Filter size={16} /> Apply Filter
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default memo(CallLogsSummaryFilter);

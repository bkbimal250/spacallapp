import React, { useState, useEffect, useCallback, memo } from 'react';
import { 
    Search, 
    Calendar,
    Filter,
    X,
    Smartphone,
    MapPin,
    Activity,
    CheckCircle2,
    Clock
} from 'lucide-react';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

/**
 * DeviceFilter Component
 * Standardized premium filtering for Device Management.
 */
const DeviceFilter = ({ onFilter, initialFilters = {} }) => {
    // Basic states
    const [search, setSearch] = useState(initialFilters.search || '');
    const [selectedBranch, setSelectedBranch] = useState(initialFilters.branch || '');
    const [selectedCity, setSelectedCity] = useState(initialFilters.city || '');
    const [registrationStatus, setRegistrationStatus] = useState(initialFilters.is_registered || '');
    const [androidIdStatus, setAndroidIdStatus] = useState(initialFilters.has_android_id || '');
    const [complianceStatus, setComplianceStatus] = useState(initialFilters.compliance_status || '');
    const [activeStatus, setActiveStatus] = useState(initialFilters.is_active || '');
    const [blockedStatus, setBlockedStatus] = useState(initialFilters.is_blocked || '');

    // Data lists
    const [branches, setBranches] = useState([]);
    const [cities, setCities] = useState([]);

    // Date states
    const [dateMode, setDateMode] = useState('preset');
    const [quickDate, setQuickDate] = useState(initialFilters.quick_date || '');
    const [singleDate, setSingleDate] = useState('');
    const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });

    // Fetch branches and metadata
    useEffect(() => {
        const fetchMetadata = async () => {
            try {
                const response = await branchesAPI.getBranches({ all: true });
                const branchData = response.data.results || response.data;
                
                setBranches(branchData.map(b => ({
                    value: b.id,
                    label: `${b.spa_name} ${b.code ? `(${b.code})` : ''}`,
                    title: b.spa_name,
                    searchText: [
                        b.spa_name,
                        b.code,
                        b.city,
                        b.area,
                        b.state,
                        b.address,
                        b.phone,
                        b.branch_group_name,
                    ].filter(Boolean).join(' ')
                })));

                const uniqueCities = [...new Set(branchData.map(b => b.city).filter(Boolean))];
                setCities(uniqueCities.map(c => ({ value: c, label: c })));
            } catch (err) {
                console.error("Failed to fetch filter metadata", err);
            }
        };
        fetchMetadata();
    }, []);

    const handleApplyFilters = useCallback(() => {
        const filters = {
            search: search.trim() || undefined,
            branch: selectedBranch || undefined,
            city: selectedCity.trim() || undefined,
            is_registered: registrationStatus || undefined,
            has_android_id: androidIdStatus || undefined,
            compliance_status: complianceStatus || undefined,
            is_active: activeStatus || undefined,
            is_blocked: blockedStatus || undefined,
        };

        if (dateMode === 'single' && singleDate) {
            filters.start_date = singleDate;
            filters.end_date = singleDate;
        } else if (dateMode === 'range') {
            if (dateRange.startDate) filters.start_date = dateRange.startDate;
            if (dateRange.endDate) filters.end_date = dateRange.endDate;
        } else if (quickDate) {
            filters.quick_date = quickDate;
        }

        // Clean undefined
        const cleanFilters = Object.fromEntries(
            Object.entries(filters).filter(([_, v]) => v !== undefined)
        );
        onFilter(cleanFilters);
    }, [search, selectedBranch, selectedCity, registrationStatus, androidIdStatus, complianceStatus, activeStatus, blockedStatus, dateMode, quickDate, singleDate, dateRange, onFilter]);

    const handleClear = () => {
        setSearch('');
        setSelectedBranch('');
        setSelectedCity('');
        setRegistrationStatus('');
        setAndroidIdStatus('');
        setComplianceStatus('');
        setActiveStatus('');
        setBlockedStatus('');
        setQuickDate('');
        setSingleDate('');
        setDateRange({ startDate: '', endDate: '' });
        setDateMode('preset');
        onFilter({});
    };

    return (
        <div className="bg-card rounded-xl border border-border shadow-sm mb-6 relative z-10 overflow-visible">
            <div className="p-5 space-y-6 overflow-visible">
                {/* ── TOP: SEARCH & DATE PRESETS ── */}
                <div className="flex flex-col lg:flex-row gap-6 items-start lg:items-center justify-between">
                    <div className="flex flex-wrap items-center gap-2">
                        <div className="flex items-center gap-2 mr-2 text-text-secondary">
                            <Calendar size={18} className="text-primary" />
                            <span className="text-xs font-bold uppercase tracking-wider">Date Created</span>
                        </div>
                        <div className="flex items-center p-1 bg-background rounded-lg border border-border">
                            {[
                                { id: '', label: 'All Time' },
                                { id: 'today', label: 'Today' },
                                { id: 'yesterday', label: 'Yesterday' }
                            ].map(preset => (
                                <button
                                    key={preset.id}
                                    onClick={() => {
                                        setQuickDate(preset.id);
                                        setDateMode('preset');
                                    }}
                                    className={`px-3 py-1.5 rounded-md text-[11px] font-bold transition-all ${
                                        dateMode === 'preset' && quickDate === preset.id
                                            ? 'bg-primary text-white shadow-sm'
                                            : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                                    }`}
                                >
                                    {preset.label}
                                </button>
                            ))}
                            <button
                                onClick={() => setDateMode('range')}
                                className={`px-3 py-1.5 rounded-md text-[11px] font-bold transition-all ${
                                    dateMode === 'range'
                                        ? 'bg-primary text-white shadow-sm'
                                        : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                                }`}
                            >
                                Custom
                            </button>
                        </div>
                    </div>

                    <div className="w-full lg:w-97 relative">
                        <Input
                            placeholder="Search device, branch, city, area, spa code..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleApplyFilters()}
                            className="h-11 bg-background border-border-light"
                        />
                    </div>
                </div>

                {/* ── MIDDLE: CUSTOM DATE PICKER ── */}
                {dateMode === 'range' && (
                    <div className="p-4 bg-background/50 rounded-lg border border-primary/20 animate-in fade-in slide-in-from-top-2 duration-300">
                        <div className="flex flex-wrap items-center gap-4">
                            <div className="space-y-1">
                                <label className="text-[10px] uppercase font-bold text-text-secondary ml-1">Start Date</label>
                                <input
                                    type="date"
                                    className="block px-3 py-2 bg-card border border-border rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                    value={dateRange.startDate}
                                    onChange={(e) => setDateRange(p => ({ ...p, startDate: e.target.value }))}
                                />
                            </div>
                            <span className="mt-5 text-text-muted">—</span>
                            <div className="space-y-1">
                                <label className="text-[10px] uppercase font-bold text-text-secondary ml-1">End Date</label>
                                <input
                                    type="date"
                                    className="block px-3 py-2 bg-card border border-border rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                    value={dateRange.endDate}
                                    onChange={(e) => setDateRange(p => ({ ...p, endDate: e.target.value }))}
                                />
                            </div>
                            <Button 
                                variant="outline" 
                                size="sm" 
                                className="mt-5 text-xs text-text-muted hover:text-danger"
                                onClick={() => { setDateMode('preset'); setQuickDate(''); }}
                            >
                                <X size={14} className="mr-1" /> Reset
                            </Button>
                        </div>
                    </div>
                )}

                {/* ── BOTTOM: ADVANCED GRIDS ── */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 pt-4 border-t border-border/50">
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <MapPin size={14} className="text-primary/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary">Branch</span>
                        </div>
                        <SearchableSelect
                            placeholder="All Branches"
                            options={branches}
                            value={selectedBranch}
                            onChange={setSelectedBranch}
                            className="bg-background"
                        />
                    </div>

                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <Activity size={14} className="text-warning/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary">Compliance</span>
                        </div>
                        <select
                            className="w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm transition-all focus:ring-2 focus:ring-primary/20 outline-none"
                            value={complianceStatus}
                            onChange={(e) => setComplianceStatus(e.target.value)}
                        >
                            <option value="">All</option>
                            <option value="OK">OK</option>
                            <option value="MISSING_ANDROID_ID">Missing Android ID</option>
                            <option value="MISSING_FCM_TOKEN">Missing FCM Token</option>
                            <option value="OUTDATED_APP">Outdated App</option>
                            <option value="HEARTBEAT_MISSING">Heartbeat Missing</option>
                            <option value="DEVICE_TIME_WRONG">Device Time Wrong</option>
                            <option value="SUSPECTED_UNINSTALLED">Suspected Uninstalled</option>
                            <option value="AUTH_BROKEN">Auth Broken</option>
                        </select>
                    </div>

                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <Smartphone size={14} className="text-primary/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary">Android ID</span>
                        </div>
                        <select
                            className="w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm transition-all focus:ring-2 focus:ring-primary/20 outline-none"
                            value={androidIdStatus}
                            onChange={(e) => setAndroidIdStatus(e.target.value)}
                        >
                            <option value="">All Devices</option>
                            <option value="true">Android ID Present</option>
                            <option value="false">Android ID Missing</option>
                        </select>
                    </div>

                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <CheckCircle2 size={14} className="text-secondary/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary">Registration</span>
                        </div>
                        <select
                            className="w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm transition-all focus:ring-2 focus:ring-primary/20 outline-none"
                            value={registrationStatus}
                            onChange={(e) => setRegistrationStatus(e.target.value)}
                        >
                            <option value="">All Statuses</option>
                            <option value="true">Claimed / Registered</option>
                            <option value="false">Pending Registration</option>
                        </select>
                    </div>

                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <Activity size={14} className="text-success/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary">Inward Active Status</span>
                        </div>
                        <select
                            className="w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm transition-all focus:ring-2 focus:ring-primary/20 outline-none"
                            value={activeStatus}
                            onChange={(e) => setActiveStatus(e.target.value)}
                        >
                            <option value="">All</option>
                            <option value="true">Active Only</option>
                            <option value="false">Inactive Only</option>
                        </select>
                    </div>

                    <div className="flex items-end gap-2">
                         <div className="flex-1 space-y-1.5">
                            <div className="flex items-center gap-2">
                                <Clock size={14} className="text-danger/70" />
                                <span className="text-[10px] uppercase font-bold text-text-secondary">Blocked Status</span>
                            </div>
                            <select
                                className="w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm transition-all focus:ring-2 focus:ring-primary/20 outline-none"
                                value={blockedStatus}
                                onChange={(e) => setBlockedStatus(e.target.value)}
                            >
                                <option value="">All</option>
                                <option value="true">Blocked Only</option>
                                <option value="false">Unblocked Only</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div className="flex justify-between items-center pt-2">
                   <div className="flex gap-2">
                        <Button
                            variant="secondary"
                            onClick={handleClear}
                            className="h-10 px-6 font-bold text-xs"
                        >
                            Clear All
                        </Button>
                        <Button
                            onClick={handleApplyFilters}
                            className="h-10 px-8 bg-primary text-white font-bold text-xs shadow-lg shadow-primary/20"
                        >
                            <Filter size={14} className="mr-2" /> Apply Filters
                        </Button>
                   </div>
                </div>
            </div>
        </div>
    );
};

export default memo(DeviceFilter);

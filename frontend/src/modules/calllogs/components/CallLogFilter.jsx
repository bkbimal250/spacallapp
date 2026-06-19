import React, { useEffect, useState, memo, useCallback } from 'react';
import { useSelector } from 'react-redux';
import {
    Search,
    Building2,
    Smartphone,
    PhoneCall,
    Calendar,
    ChevronDown,
    Filter,
    X
} from 'lucide-react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';
import { devicesAPI } from '../../devices/api';

const CallLogFilter = ({
    onFilter,
    initialBranch = '',
    initialDevice = '',
    initialSearch = '',
    initialCallType = '',
    initialSlaStatus = '',
    initialBranchGroup = '',
    initialUnique = false,
    initialQuickDate = 'today',
    initialStartDate = '',
    initialEndDate = ''
}) => {
    const { user } = useSelector(state => state.auth);

    const [search, setSearch] = useState(initialSearch);

    // Date states
    const [dateMode, setDateMode] = useState(() => {
        if (initialStartDate && initialEndDate) {
            return initialStartDate === initialEndDate ? 'single' : 'range';
        }
        return 'preset';
    });
    const [quickDate, setQuickDate] = useState(initialQuickDate || 'today');
    const [singleDate, setSingleDate] = useState(initialStartDate === initialEndDate ? initialStartDate : '');
    const [dateRange, setDateRange] = useState({
        startDate: initialStartDate,
        endDate: initialEndDate
    });

    const [branches, setBranches] = useState([]);
    const [selectedBranch, setSelectedBranch] = useState(initialBranch);
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(initialDevice);
    const [selectedCallType, setSelectedCallType] = useState(initialCallType);
    const [selectedSlaStatus, setSelectedSlaStatus] = useState(initialSlaStatus);
    const [branchGroups, setBranchGroups] = useState([]);
    const [selectedBranchGroup, setSelectedBranchGroup] = useState(initialBranchGroup);
    const [isUnique, setIsUnique] = useState(initialUnique);
    const [loadingDevices, setLoadingDevices] = useState(false);

    const isRestrictedManager = user?.role === 'spa_manager' || user?.role === 'regional_manager';

    useEffect(() => {
        setSearch(initialSearch);
        setSelectedBranch(initialBranch);
        setSelectedDevice(initialDevice);
        setSelectedCallType(initialCallType);
        setSelectedSlaStatus(initialSlaStatus);
        setSelectedBranchGroup(initialBranchGroup);
        setIsUnique(initialUnique);

        if (initialStartDate && initialEndDate) {
            if (initialStartDate === initialEndDate) {
                setDateMode('single');
                setSingleDate(initialStartDate);
                setDateRange({ startDate: initialStartDate, endDate: initialEndDate });
            } else {
                setDateMode('range');
                setDateRange({ startDate: initialStartDate, endDate: initialEndDate });
            }
            setQuickDate('');
        } else {
            setDateMode('preset');
            setQuickDate(initialQuickDate || 'today');
            setSingleDate('');
            setDateRange({ startDate: '', endDate: '' });
        }
    }, [initialSearch, initialBranch, initialDevice, initialCallType, initialSlaStatus, initialBranchGroup, initialUnique, initialQuickDate, initialStartDate, initialEndDate]);

    useEffect(() => {
        const fetchBranches = async () => {
            if (isRestrictedManager) return;
            try {
                // Fetch branches filtered by group if one is selected
                const params = { all: true };
                if (selectedBranchGroup) {
                    params.branch_group = selectedBranchGroup;
                }

                const response = await branchesAPI.getBranches(params);
                const branchData = response.data.results || response.data;
                setBranches(
                    branchData.map(b => ({
                        value: b.id,
                        label: b.code ? `${b.spa_name} (${b.code})` : b.spa_name,
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
                    }))
                );
            } catch (error) {
                console.error("Failed to fetch branches for filter", error);
            }
        };
        fetchBranches();
    }, [isRestrictedManager, selectedBranchGroup]);

    useEffect(() => {
        const fetchGroups = async () => {
            if (isRestrictedManager) return;
            try {
                const response = await branchesAPI.getGroups({ all: true });
                const groupData = response.data.results || response.data;
                setBranchGroups(
                    groupData.map(g => ({
                        value: g.id,
                        label: g.name,
                        title: g.name
                    }))
                );
            } catch (error) {
                console.error("Failed to fetch branch groups", error);
            }
        };
        fetchGroups();
    }, [isRestrictedManager]);

    useEffect(() => {
        const fetchDevices = async () => {
            const branchId = isRestrictedManager ? user?.branch : selectedBranch;
            if (!branchId) {
                setDevices([]);
                setSelectedDevice('');
                return;
            }
            setLoadingDevices(true);
            try {
                const response = await devicesAPI.getDevices({ branch: branchId, all: true });
                const deviceData = response.data.results || response.data;
                setDevices(
                    deviceData.map(d => ({
                        value: d.device_id,
                        label: d.phone_name ? `${d.phone_name} (${d.device_id})` : `${d.device_id} (${d.sim_1_number || 'No SIM'})`,
                        title: d.phone_name || d.device_id
                    }))
                );
            } catch (error) {
                console.error("Failed to fetch devices for branch", error);
            } finally {
                setLoadingDevices(false);
            }
        };
        fetchDevices();
    }, [selectedBranch, isRestrictedManager, user?.branch]);

    const getActiveFilters = useCallback((overrides = {}) => {
        // Base values with safe fallbacks
        const baseSearch = overrides.search !== undefined ? overrides.search : (search || '');
        const baseBranch = overrides.branch !== undefined ? overrides.branch : (selectedBranch && !isRestrictedManager ? selectedBranch : undefined);
        const baseDevice = overrides.device !== undefined ? overrides.device : (selectedDevice || '');
        const baseBranchGroup = overrides.branch_group !== undefined ? overrides.branch_group : (selectedBranchGroup || '');
        const baseIsUnique = overrides.is_unique !== undefined ? overrides.is_unique : !!isUnique;

        // Date values
        const baseQuickDate = overrides.quick_date !== undefined ? overrides.quick_date : (dateMode === 'preset' ? quickDate : undefined);
        const baseStartDate = overrides.start_date !== undefined ? overrides.start_date : (dateMode !== 'preset' ? (dateMode === 'single' ? singleDate : dateRange.startDate) : undefined);
        const baseEndDate = overrides.end_date !== undefined ? overrides.end_date : (dateMode !== 'preset' ? (dateMode === 'single' ? singleDate : dateRange.endDate) : undefined);

        // Call Type & SLA logic
        let baseCallType = overrides.call_type !== undefined ? overrides.call_type : (selectedCallType || '');
        let baseSlaStatus = overrides.sla_status !== undefined ? overrides.sla_status : (selectedSlaStatus || '');

        // Smart cleanup: If call_type is not missed, clear sla_status
        if (baseCallType && baseCallType !== 'missed') {
            baseSlaStatus = undefined;
        }
        // If SLA status is selected but type isn't missed, force missed type
        if (baseSlaStatus && baseCallType !== 'missed') {
            baseCallType = 'missed';
        }

        const filters = {
            search: baseSearch,
            quick_date: baseQuickDate,
            start_date: baseStartDate,
            end_date: baseEndDate,
            branch: baseBranch,
            device: baseDevice,
            branch_group: baseBranchGroup,
            call_type: baseCallType,
            sla_status: baseSlaStatus,
            is_unique: baseIsUnique
        };

        // Deep filter to remove null/undefined/empty strings
        return Object.fromEntries(
            Object.entries(filters).filter(([_, v]) => v !== undefined && v !== null && v !== '')
        );
    }, [search, quickDate, singleDate, dateRange, dateMode, selectedBranch, selectedDevice, selectedBranchGroup, selectedCallType, selectedSlaStatus, isUnique, isRestrictedManager]);

    const handleFilter = useCallback((additionalFilters = {}) => {
        const filters = getActiveFilters(additionalFilters);
        onFilter(filters);
    }, [onFilter, getActiveFilters]);

    const handleQuickDateChange = (preset) => {
        setQuickDate(preset);
        setDateMode('preset');
        onFilter(getActiveFilters({ quick_date: preset, start_date: '', end_date: '' }));
    };

    const handleSingleDateChange = (date) => {
        setSingleDate(date);
        if (date) {
            onFilter(getActiveFilters({ start_date: date, end_date: date, quick_date: '' }));
        }
    };

    const handleClear = useCallback(() => {
        setSearch('');
        setQuickDate('all');
        setSingleDate('');
        setDateRange({ startDate: '', endDate: '' });
        setDateMode('preset');
        setSelectedBranch(initialBranch || '');
        setSelectedDevice('');
        setSelectedCallType('');
        setSelectedSlaStatus('');
        setSelectedBranchGroup('');
        setIsUnique(false);

        onFilter({
            quick_date: 'all',
            branch: initialBranch || '',
            branch_group: '',
            search: '',
            call_type: '',
            sla_status: '',
            is_unique: false
        });
    }, [onFilter, initialBranch]);

    const datePresets = [
        { id: 'today', label: 'Today' },
        { id: 'yesterday', label: 'Yesterday' },
        { id: 'all', label: 'All Time' },
    ];

    return (
        <div className="bg-card rounded-xl border border-border shadow-sm transition-all duration-300">
            <div className="p-5 space-y-6">
                {/* ── TOP SECTION: QUICK DATE & SEARCH ── */}
                <div className="flex flex-col lg:flex-row gap-6 items-start lg:items-center justify-between">
                    <div className="flex flex-wrap items-center gap-2">
                        <div className="flex items-center gap-2 mr-2 text-text-secondary">
                            <Calendar size={18} className="text-primary" />
                            <span className="text-sm font-semibold uppercase tracking-wider">Date</span>
                        </div>
                        <div className="flex items-center p-1 bg-background rounded-lg border border-border">
                            {datePresets.map(preset => (
                                <button
                                    key={preset.id}
                                    onClick={() => handleQuickDateChange(preset.id)}
                                    className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all duration-200 ${dateMode === 'preset' && quickDate === preset.id
                                        ? 'bg-primary text-white shadow-md'
                                        : 'text-text-secondary hover:bg-cardHover hover:text-text-primary'
                                        }`}
                                >
                                    {preset.label}
                                </button>
                            ))}
                            <button
                                onClick={() => setDateMode('single')}
                                className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all duration-200 ${dateMode === 'single'
                                    ? 'bg-primary text-white shadow-md'
                                    : 'text-text-secondary hover:bg-cardHover hover:text-text-primary'
                                    }`}
                            >
                                Quick Date
                            </button>
                            <button
                                onClick={() => setDateMode('range')}
                                className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all duration-200 ${dateMode === 'range'
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
                            placeholder="Search Number / Name..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="pl-10 h-10 bg-background border-border-light hover:border-primary focus:border-primary transition-colors"
                        />
                    </div>
                </div>

                {/* ── MIDDLE SECTION: CUSTOM DATE / RANGE (HIDDEN UNLESS ACTIVE) ── */}
                {dateMode !== 'preset' && (
                    <div className="p-4 bg-background/50 rounded-lg border border-border-light animate-in fade-in slide-in-from-top-2 duration-300">
                        <div className="flex flex-wrap items-center gap-4">
                            {dateMode === 'single' ? (
                                <div className="space-y-1">
                                    <label className="text-[10px] uppercase font-bold text-text-secondary ml-1">Select Date</label>
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
                                        <label className="text-[10px] uppercase font-bold text-text-secondary ml-1">Start Date</label>
                                        <input
                                            type="date"
                                            className="block px-3 py-2 bg-card border border-border rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                            value={dateRange.startDate}
                                            onChange={(e) => setDateRange(prev => ({ ...prev, startDate: e.target.value }))}
                                        />
                                    </div>
                                    <span className="mt-5 text-text-secondary">—</span>
                                    <div className="space-y-1">
                                        <label className="text-[10px] uppercase font-bold text-text-secondary ml-1">End Date</label>
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

                {/* ── BOTTOM SECTION: ADVANCED FILTERS ── */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 pt-6 border-t border-border-light/30">
                    {!isRestrictedManager && (
                        <>
                            <div className="space-y-2">
                                <div className="flex items-center gap-2 px-1">
                                    <Building2 size={14} className="text-primary/60" />
                                    <span className="text-[11px] uppercase font-bold text-text-secondary/80 tracking-wider">Group</span>
                                </div>
                                <SearchableSelect
                                    placeholder="Filter by Group"
                                    options={branchGroups}
                                    value={selectedBranchGroup}
                                    onChange={(val) => {
                                        setSelectedBranchGroup(val);
                                        setSelectedBranch('');
                                        setSelectedDevice('');
                                        onFilter(getActiveFilters({ branch_group: val, branch: '', device: '' }));
                                    }}
                                    className="w-full"
                                />
                            </div>

                            <div className="space-y-2">
                                <div className="flex items-center gap-2 px-1">
                                    <Building2 size={14} className="text-primary/60" />
                                    <span className="text-[11px] uppercase font-bold text-text-secondary/80 tracking-wider">Branch</span>
                                </div>
                                <SearchableSelect
                                    placeholder="Filter by Branch"
                                    options={branches}
                                    value={selectedBranch}
                                    onChange={(val) => {
                                        setSelectedBranch(val);
                                        setSelectedDevice('');
                                        onFilter(getActiveFilters({ branch: val, device: '' }));
                                    }}
                                    className="w-full"
                                />
                            </div>
                        </>
                    )}

                    <div className="space-y-2">
                        <div className="flex items-center gap-2 px-1">
                            <Smartphone size={14} className="text-primary/60" />
                            <span className="text-[11px] uppercase font-bold text-text-secondary/80 tracking-wider">Device</span>
                        </div>
                        <SearchableSelect
                            placeholder={loadingDevices ? "Loading..." : "All Devices"}
                            options={devices}
                            value={selectedDevice}
                            onChange={(val) => {
                                setSelectedDevice(val);
                                onFilter(getActiveFilters({ device: val }));
                            }}
                            disabled={!selectedBranch && !isRestrictedManager}
                            className="w-full"
                        />
                    </div>

                    <div className="space-y-2">
                        <div className="flex items-center gap-2 px-1">
                            <PhoneCall size={14} className="text-primary/60" />
                            <span className="text-[11px] uppercase font-bold text-text-secondary/80 tracking-wider">Call Type</span>
                        </div>
                        <div className="relative group">
                            <select
                                className="block w-full h-[42px] px-4 bg-background border border-border rounded-xl text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none appearance-none cursor-pointer hover:border-primary/50 shadow-sm"
                                value={selectedCallType}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    setSelectedCallType(val);
                                    if (val !== 'missed') {
                                        setSelectedSlaStatus('');
                                    }
                                    onFilter(getActiveFilters({ call_type: val, sla_status: val !== 'missed' ? '' : undefined }));
                                }}
                            >
                                <option value="">All Types</option>
                                <option value="incoming">Incoming</option>
                                <option value="outgoing">Outgoing</option>
                                <option value="missed">Missed</option>
                                <option value="rejected">Rejected</option>
                            </select>
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-text-muted group-hover:text-primary transition-colors">
                                <ChevronDown size={16} />
                            </div>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <div className="flex items-center gap-2 px-1">
                            <Filter size={14} className="text-primary/60" />
                            <span className="text-[11px] uppercase font-bold text-text-secondary/80 tracking-wider">Follow-up SLA</span>
                        </div>
                        <div className="relative group">
                            <select
                                className="block w-full h-[42px] px-4 bg-background border border-border rounded-xl text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none appearance-none cursor-pointer hover:border-primary/50 shadow-sm"
                                value={selectedSlaStatus}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    setSelectedSlaStatus(val);
                                    let typeOverride = undefined;
                                    if (val) {
                                        setSelectedCallType('missed');
                                        typeOverride = 'missed';
                                    }
                                    onFilter(getActiveFilters({ sla_status: val, call_type: typeOverride }));
                                }}
                            >
                                <option value="">All Status</option>
                                <option value="GOOD">Good (&lt; 10m)</option>
                                <option value="OK">OK (&lt; 30m)</option>
                                <option value="LATE">Late (&gt; 30m)</option>
                                <option value="MISSED">Missed SLA</option>
                                <option value="CUSTOMER_RECALL">Customer Recall</option>
                            </select>
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-text-muted group-hover:text-primary transition-colors">
                                <ChevronDown size={16} />
                            </div>
                        </div>
                    </div>

                    {/* UNIQUE TOGGLE CELL */}
                    <div className="flex items-end h-full pt-[22px]">
                        <div 
                            className={`flex items-center justify-between w-full h-[42px] px-4 rounded-xl border transition-all cursor-pointer select-none shadow-sm
                                ${isUnique ? 'bg-primary/5 border-primary shadow-primary/5' : 'bg-background border-border hover:border-primary/30'}`}
                            onClick={() => {
                                const newVal = !isUnique;
                                setIsUnique(newVal);
                                onFilter(getActiveFilters({ is_unique: newVal }));
                            }}
                        >
                            <span className={`text-xs font-bold transition-colors ${isUnique ? 'text-primary' : 'text-text-secondary'}`}>
                                Unique Records
                            </span>
                            <div className="relative">
                                <input
                                    type="checkbox"
                                    className="sr-only"
                                    checked={isUnique}
                                    readOnly
                                />
                                <div className={`w-9 h-5 rounded-full transition-all duration-300 ${isUnique ? 'bg-primary' : 'bg-slate-200'}`}></div>
                                <div className={`absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-300 shadow-sm ${isUnique ? 'translate-x-4' : 'translate-x-0'}`}></div>
                            </div>
                        </div>
                    </div>

                    {/* ACTION BUTTONS CELL */}
                    <div className="flex items-end gap-3 h-full pt-[22px] sm:col-span-1 md:col-span-1 lg:col-span-2">
                        <div className="flex gap-2 w-full h-[42px]">
                            <Button
                                variant="outline"
                                onClick={handleClear}
                                className="flex-1 border-border hover:bg-slate-50 text-text-secondary hover:text-danger hover:border-danger/30 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 group"
                                title="Clear All Filters"
                            >
                                <X size={16} className="group-hover:rotate-90 transition-transform duration-300" /> 
                                <span className="font-bold text-xs uppercase tracking-tight">Clear</span>
                            </Button>

                            <Button
                                onClick={() => handleFilter()}
                                className="flex-[1.5] bg-primary hover:bg-primary-dark text-white rounded-xl font-bold shadow-lg shadow-primary/10 hover:shadow-primary/20 transition-all duration-200 flex items-center justify-center gap-2"
                            >
                                <Filter size={16} /> 
                                <span className="uppercase text-xs tracking-tight">Apply Filter</span>
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );



};

export default memo(CallLogFilter);

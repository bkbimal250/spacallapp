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
    initialFollowupStatus = '',
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
    const [selectedFollowupStatus, setSelectedFollowupStatus] = useState(initialFollowupStatus);
    const [isUnique, setIsUnique] = useState(initialUnique);
    const [loadingDevices, setLoadingDevices] = useState(false);

    const isRestrictedManager = user?.role === 'spa_manager' || user?.role === 'regional_manager';

    useEffect(() => {
        setSearch(initialSearch);
        setSelectedBranch(initialBranch);
        setSelectedDevice(initialDevice);
        setSelectedCallType(initialCallType);
        setSelectedFollowupStatus(initialFollowupStatus);
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
    }, [initialSearch, initialBranch, initialDevice, initialCallType, initialFollowupStatus, initialUnique, initialQuickDate, initialStartDate, initialEndDate]);

    useEffect(() => {
        const fetchBranches = async () => {
            if (isRestrictedManager) return;
            try {
                const response = await branchesAPI.getBranches({ all: true });
                const branchData = response.data.results || response.data;
                setBranches(
                    branchData.map(b => ({
                        value: b.id,
                        label: b.code ? `${b.spa_name} (${b.code})` : b.spa_name,
                        title: b.spa_name
                    }))
                );
            } catch (error) {
                console.error("Failed to fetch branches for filter", error);
            }
        };
        fetchBranches();
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

    const handleFilter = useCallback((additionalFilters = {}) => {
        const filters = { ...additionalFilters };
        if (search) filters.search = search;
        
        if (dateMode === 'single') {
            if (singleDate) {
                filters.start_date = singleDate;
                filters.end_date = singleDate;
            }
        } else if (dateMode === 'range') {
            if (dateRange.startDate) filters.start_date = dateRange.startDate;
            if (dateRange.endDate) filters.end_date = dateRange.endDate;
        } else if (quickDate) {
            filters.quick_date = quickDate;
        }

        if (selectedBranch && !isRestrictedManager) filters.branch = selectedBranch;
        if (selectedDevice) filters.device = selectedDevice;
        if (selectedCallType) filters.call_type = selectedCallType;
        if (selectedFollowupStatus) filters.followup_status = selectedFollowupStatus;
        if (isUnique) filters.is_unique = true;

        onFilter(filters);
    }, [search, quickDate, singleDate, dateRange, dateMode, selectedBranch, selectedDevice, selectedCallType, isRestrictedManager, isUnique, onFilter]);

    const getActiveFilters = useCallback((overrides = {}) => {
        const filters = {
            search: overrides.search !== undefined ? overrides.search : search,
            quick_date: overrides.quick_date !== undefined ? overrides.quick_date : (dateMode === 'preset' ? quickDate : undefined),
            start_date: overrides.start_date !== undefined ? overrides.start_date : (dateMode !== 'preset' ? (dateMode === 'single' ? singleDate : dateRange.startDate) : undefined),
            end_date: overrides.end_date !== undefined ? overrides.end_date : (dateMode !== 'preset' ? (dateMode === 'single' ? singleDate : dateRange.endDate) : undefined),
            branch: overrides.branch !== undefined ? overrides.branch : (selectedBranch && !isRestrictedManager ? selectedBranch : undefined),
            device: overrides.device !== undefined ? overrides.device : selectedDevice,
            call_type: overrides.call_type !== undefined ? overrides.call_type : selectedCallType,
            followup_status: overrides.followup_status !== undefined ? overrides.followup_status : selectedFollowupStatus,
            is_unique: overrides.is_unique !== undefined ? overrides.is_unique : isUnique
        };
        return Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== undefined && v !== ''));
    }, [search, quickDate, singleDate, dateRange, dateMode, selectedBranch, selectedDevice, selectedCallType, selectedFollowupStatus, isUnique, isRestrictedManager]);

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
        setSelectedFollowupStatus('');
        setIsUnique(false);
        onFilter({ quick_date: 'all', branch: initialBranch || '' });
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 pt-2 border-t border-border-light/50">
                    {!isRestrictedManager && (
                        <div className="space-y-1.5">
                            <div className="flex items-center gap-2 mb-1">
                                <Building2 size={15} className="text-primary/70" />
                                <span className="text-[10px] uppercase font-bold text-text-secondary tracking-widest">Branch</span>
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
                    )}

                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2 mb-1">
                            <Smartphone size={15} className="text-primary/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary tracking-widest">Device</span>
                        </div>
                        <SearchableSelect
                            placeholder={loadingDevices ? "Loading..." : "All Devices"}
                            options={devices}
                            value={selectedDevice}
                            onChange={(val) => {
                                setSelectedDevice(val);
                                const filters = {
                                    search,
                                    branch: (selectedBranch && !isRestrictedManager) ? selectedBranch : undefined,
                                    quick_date: quickDate,
                                    device: val,
                                    call_type: selectedCallType,
                                    followup_status: selectedFollowupStatus,
                                    is_unique: isUnique
                                };
                                onFilter(Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '')));
                            }}
                            disabled={!selectedBranch && !isRestrictedManager}
                        />
                    </div>

                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2 mb-1">
                            <PhoneCall size={15} className="text-primary/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary tracking-widest">Call Type</span>
                        </div>
                        <select
                            className="block w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none appearance-none cursor-pointer"
                            value={selectedCallType}
                            onChange={(e) => {
                                const val = e.target.value;
                                setSelectedCallType(val);
                                const filters = {
                                    search,
                                    branch: (selectedBranch && !isRestrictedManager) ? selectedBranch : undefined,
                                    quick_date: quickDate,
                                    call_type: val,
                                    followup_status: selectedFollowupStatus,
                                    is_unique: isUnique
                                };
                                onFilter(Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '')));
                            }}
                        >
                            <option value="">All Types</option>
                            <option value="incoming">Incoming</option>
                            <option value="outgoing">Outgoing</option>
                            <option value="missed">Missed</option>
                            <option value="rejected">Rejected</option>
                        </select>
                    </div>

                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2 mb-1">
                            <Filter size={15} className="text-primary/70" />
                            <span className="text-[10px] uppercase font-bold text-text-secondary tracking-widest">Follow-up SLA</span>
                        </div>
                        <select
                            className="block w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none appearance-none cursor-pointer"
                            value={selectedFollowupStatus}
                            onChange={(e) => {
                                const val = e.target.value;
                                setSelectedFollowupStatus(val);
                                const filters = {
                                    search,
                                    branch: (selectedBranch && !isRestrictedManager) ? selectedBranch : undefined,
                                    quick_date: quickDate,
                                    call_type: selectedCallType,
                                    followup_status: val,
                                    is_unique: isUnique
                                };
                                onFilter(Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '')));
                            }}
                        >
                            <option value="">All Status</option>
                            <option value="GOOD">Good (&lt; 10m)</option>
                            <option value="OK">OK (&lt; 30m)</option>
                            <option value="LATE">Late (&gt; 30m)</option>
                            <option value="MISSED">Missed SLA</option>
                        </select>
                    </div>

                    <div className="flex items-end gap-3">
                        <div className="flex-1 flex items-center h-[42px] px-4 bg-background border border-border rounded-lg group cursor-pointer hover:border-primary transition-all overflow-hidden">
                            <label className="flex items-center cursor-pointer w-full">
                                <div className="relative">
                                    <input
                                        type="checkbox"
                                        className="sr-only"
                                        checked={isUnique}
                                        onChange={(e) => {
                                            const val = e.target.checked;
                                            setIsUnique(val);
                                            const filters = {
                                                search,
                                                branch: (selectedBranch && !isRestrictedManager) ? selectedBranch : undefined,
                                                quick_date: quickDate,
                                                call_type: selectedCallType,
                                                followup_status: selectedFollowupStatus,
                                                is_unique: val
                                            };
                                            onFilter(Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '')));
                                        }}
                                    />
                                    <div className={`w-9 h-5 rounded-full transition-colors ${isUnique ? 'bg-primary' : 'bg-slate-300'}`}></div>
                                    <div className={`absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${isUnique ? 'translate-x-4' : 'translate-x-0'} shadow-sm`}></div>
                                </div>
                                <span className="ml-3 text-xs font-bold text-text-secondary group-hover:text-primary transition-colors whitespace-nowrap">
                                    Unique Record
                                </span>
                            </label>
                        </div>
                        
                        <div className="flex gap-2 h-[42px]">
                            <Button
                                variant="outline"
                                onClick={handleClear}
                                className="border-border hover:bg-cardHover text-text-secondary flex items-center gap-2 px-4"
                                title="Clear All"
                            >
                                <X size={16} /> <span className="font-semibold text-xs">Clear</span>
                            </Button>

                            <Button
                                onClick={() => handleFilter()}
                                className="bg-primary hover:bg-primary-dark text-white px-6 font-bold shadow-lg shadow-primary/20 flex items-center gap-2"
                            >
                                <Filter size={16} /> Apply
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default memo(CallLogFilter);
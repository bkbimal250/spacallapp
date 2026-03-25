import React, { useEffect, useState, memo, useCallback } from 'react';
import { useSelector } from 'react-redux';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';
import { devicesAPI } from '../../devices/api';

const CallLogFilter = ({ onFilter, initialBranch = '', initialDevice = '', initialSearch = '', initialUnique = false }) => {

    const { user } = useSelector(state => state.auth);

    const [search, setSearch] = useState(initialSearch);
    const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });
    const [branches, setBranches] = useState([]);
    const [selectedBranch, setSelectedBranch] = useState(initialBranch);
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState('');
    const [selectedCallType, setSelectedCallType] = useState('');
    const [isUnique, setIsUnique] = useState(initialUnique);
    const [loadingDevices, setLoadingDevices] = useState(false);

    useEffect(() => {
        setSearch(initialSearch);
        setSelectedBranch(initialBranch);
        setSelectedDevice(initialDevice);
        setIsUnique(initialUnique);
    }, [initialSearch, initialBranch, initialDevice, initialUnique]);

    const isRestrictedManager =
        user?.role === 'branch_manager' ||
        user?.role === 'regional_manager';

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
                        title: b.spa_name // 👈 for tooltip
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

    const handleSearchChange = useCallback((e) => {
        setSearch(e.target.value);
    }, []);

    const handleBranchChange = useCallback((val) => {
        setSelectedBranch(val);
        setSelectedDevice('');
    }, []);

    const handleCallTypeChange = useCallback((e) => {
        setSelectedCallType(e.target.value);
    }, []);

    const handleStartDateChange = useCallback((e) => {
        setDateRange(prev => ({
            ...prev,
            startDate: e.target.value
        }));
    }, []);

    const handleEndDateChange = useCallback((e) => {
        setDateRange(prev => ({
            ...prev,
            endDate: e.target.value
        }));
    }, []);

    const handleFilter = useCallback(() => {
        const filters = {};

        if (search) filters.search = search;
        if (dateRange.startDate) filters.start_date = dateRange.startDate;
        if (dateRange.endDate) filters.end_date = dateRange.endDate;
        if (selectedBranch && !isRestrictedManager) filters.branch = selectedBranch;
        if (selectedDevice) filters.device = selectedDevice;
        if (selectedCallType) filters.call_type = selectedCallType;
        if (isUnique) filters.is_unique = true;

        onFilter(filters);
    }, [search, dateRange, selectedBranch, selectedDevice, selectedCallType, isRestrictedManager, onFilter]);

    const handleClear = useCallback(() => {
        setSearch('');
        setDateRange({ startDate: '', endDate: '' });
        setSelectedBranch('');
        setSelectedDevice('');
        setSelectedCallType('');
        setIsUnique(false);
        onFilter({});
    }, [onFilter]);

    return (
        <div className="space-y-6 text-text-primary">

            {/* 🔥 FILTER GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 items-end">

                {/* 🔥 SEARCH */}
                <div className="space-y-1 lg:col-span-2">
                    <Input
                        label="Search Number / Name"
                        placeholder="Search By Number / Name"
                        value={search}
                        onChange={handleSearchChange}
                        className="bg-card border-border w-full"
                    />
                </div>

                {/* 🔥 BRANCH (WIDER) */}
                {!isRestrictedManager && (
                    <div className="space-y-1 lg:col-span-2">
                        <SearchableSelect
                            label="Branch"
                            placeholder="All Branches"
                            options={branches}
                            value={selectedBranch}
                            onChange={handleBranchChange}
                            className="bg-card border-border w-full"
                        />
                    </div>
                )}

                {/* 🔥 DEVICE */}
                <div className="space-y-1 lg:col-span-1">
                    <SearchableSelect
                        label="Device"
                        placeholder={loadingDevices ? "Loading..." : "All Devices"}
                        options={devices}
                        value={selectedDevice}
                        onChange={setSelectedDevice}
                        disabled={!selectedBranch && !isRestrictedManager}
                        className="bg-card border-border w-full"
                    />
                </div>

                {/* 🔥 CALL TYPE */}
                <div className="space-y-1 lg:col-span-1">
                    <label className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                        Call Type
                    </label>

                    <select
                        className="block w-full px-3 py-2 bg-card border border-border rounded-md text-text-primary focus:border-primary"
                        value={selectedCallType}
                        onChange={handleCallTypeChange}
                    >
                        <option value="">All Types</option>
                        <option value="incoming">Incoming</option>
                        <option value="outgoing">Outgoing</option>
                        <option value="missed">Missed</option>
                        <option value="rejected">Rejected</option>
                    </select>
                </div>

                {/* 🔥 DATE RANGE */}

                <div className="space-y-1 lg:col-span-2">
                    <label className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                        Date Range
                    </label>

                    <div className="flex flex-wrap lg:flex-nowrap items-center gap-2">

                        {/* Start Date */}
                        <input
                            type="date"
                            className="flex-1 min-w-[140px] px-3 py-2 bg-card border border-border rounded-md text-text-primary focus:border-primary"
                            value={dateRange.startDate}
                            onChange={handleStartDateChange}
                        />

                        <span className="text-text-secondary">—</span>

                        {/* End Date */}
                        <input
                            type="date"
                            className="flex-1 min-w-[140px] px-3 py-2 bg-card border border-border rounded-md text-text-primary focus:border-primary"
                            value={dateRange.endDate}
                            onChange={handleEndDateChange}
                        />

                    </div>
                </div>

                {/* 🔥 UNIQUE FILTER & ACTION BUTTONS */}
                <div className="flex items-center justify-between lg:col-span-2 gap-4">

                    <label className="flex items-center cursor-pointer group">
                        <div className="relative">
                            <input
                                type="checkbox"
                                className="sr-only"
                                checked={isUnique}
                                onChange={(e) => setIsUnique(e.target.checked)}
                            />
                            <div className={`w-10 h-6 rounded-full transition-colors ${isUnique ? 'bg-primary' : 'bg-border'}`}></div>
                            <div className={`absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform ${isUnique ? 'translate-x-4' : 'translate-x-0'}`}></div>
                        </div>
                        <span className="ml-3 text-sm font-medium text-text-secondary group-hover:text-primary transition-colors">
                            Unique Record
                        </span>
                    </label>

                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            onClick={handleClear}
                            className="border-border text-text-secondary hover:bg-cardHover px-4 whitespace-nowrap"
                        >
                            Clear
                        </Button>

                        <Button
                            onClick={handleFilter}
                            className="bg-primary text-white hover:bg-primary-hover px-5 whitespace-nowrap"
                        >
                            Apply
                        </Button>
                    </div>

                </div>

            </div>

        </div>
    );
};

export default memo(CallLogFilter);
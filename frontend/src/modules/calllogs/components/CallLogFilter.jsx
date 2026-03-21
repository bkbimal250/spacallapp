import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';
import { devicesAPI } from '../../devices/api';

const CallLogFilter = ({ onFilter, initialBranch = '', initialDevice = '', initialSearch = '' }) => {

    const { user } = useSelector(state => state.auth);

    const [search, setSearch] = useState(initialSearch);
    const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });
    const [branches, setBranches] = useState([]);
    const [selectedBranch, setSelectedBranch] = useState(initialBranch);
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState('');
    const [selectedCallType, setSelectedCallType] = useState('');
    const [loadingDevices, setLoadingDevices] = useState(false);

    useEffect(() => {
        setSearch(initialSearch);
        setSelectedBranch(initialBranch);
        setSelectedDevice(initialDevice);
    }, [initialSearch, initialBranch, initialDevice]);

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
                        label: b.spa_name,
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
                        label: `${d.device_id} (${d.sim_1_number || 'No SIM'})`,
                        title: d.device_id
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

    const handleFilter = () => {
        const filters = {};

        if (search) filters.search = search;
        if (dateRange.startDate) filters.start_date = dateRange.startDate;
        if (dateRange.endDate) filters.end_date = dateRange.endDate;
        if (selectedBranch && !isRestrictedManager) filters.branch = selectedBranch;
        if (selectedDevice) filters.device = selectedDevice;
        if (selectedCallType) filters.call_type = selectedCallType;

        onFilter(filters);
    };

    const handleClear = () => {
        setSearch('');
        setDateRange({ startDate: '', endDate: '' });
        setSelectedBranch('');
        setSelectedDevice('');
        setSelectedCallType('');
        onFilter({});
    };

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
                        onChange={(e) => setSearch(e.target.value)}
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
                            onChange={(val) => {
                                setSelectedBranch(val);
                                setSelectedDevice(''); // Reset device when branch changes
                            }}
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
                        onChange={(e) => setSelectedCallType(e.target.value)}
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

                    <div className="flex items-center gap-2">
                        <input
                            type="date"
                            className="w-full px-3 py-2 bg-card border border-border rounded-md text-text-primary focus:border-primary"
                            value={dateRange.startDate}
                            onChange={(e) =>
                                setDateRange(prev => ({
                                    ...prev,
                                    startDate: e.target.value
                                }))
                            }
                        />

                        <span className="text-text-secondary">—</span>

                        <input
                            type="date"
                            className="w-full px-3 py-2 bg-card border border-border rounded-md text-text-primary focus:border-primary"
                            value={dateRange.endDate}
                            onChange={(e) =>
                                setDateRange(prev => ({
                                    ...prev,
                                    endDate: e.target.value
                                }))
                            }
                        />
                    </div>
                </div>

            </div>

            {/* 🔥 ACTION BUTTONS */}
            <div className="flex flex-wrap justify-start gap-3 pt-4 border-t border-border/50">

                <Button
                    variant="outline"
                    onClick={handleClear}
                    className="border-border text-text-secondary hover:bg-cardHover px-6"
                >
                    Clear Filters
                </Button>

                <Button
                    onClick={handleFilter}
                    className="bg-primary text-white hover:bg-primary-hover px-8"
                >
                    Apply Filters
                </Button>

            </div>

        </div>
    );
};

export default CallLogFilter;
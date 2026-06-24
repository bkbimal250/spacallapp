import React, { memo, useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, Filter, MapPin, Search, X } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

const statusOptions = [
    { value: '', label: 'All devices' },
    { value: 'online', label: 'Online' },
    { value: 'offline', label: 'Offline' },
    { value: 'app_uninstall_suspected', label: 'Possible app uninstall' },
    { value: 'registered', label: 'Registered' },
    { value: 'pending', label: 'Pending registration' },
    { value: 'blocked', label: 'Blocked' },
];

const eventOptions = [
    { value: '', label: 'All events' },
    { value: 'offline', label: 'Offline' },
    { value: 'sync_failure', label: 'Sync failure' },
    { value: 'battery_low', label: 'Battery low' },
    { value: 'storage_full', label: 'Storage full' },
    { value: 'network_weak', label: 'Weak network' },
    { value: 'sim_change', label: 'SIM change' },
    { value: 'permission_denied', label: 'Permission denied' },
    { value: 'app_crash', label: 'App crash' },
];

const resolvedOptions = [
    { value: '', label: 'All alerts' },
    { value: 'false', label: 'Active' },
    { value: 'true', label: 'Resolved' },
];

const MonitoringFilters = ({ filters, onChange, onApply, onClear }) => {
    const [branches, setBranches] = useState([]);

    useEffect(() => {
        let mounted = true;

        const fetchBranches = async () => {
            try {
                const response = await branchesAPI.getBranches({ all: true });
                const branchData = response.data.results || response.data || [];
                if (!mounted) return;

                setBranches(branchData.map(branch => ({
                    value: branch.id,
                    label: `${branch.spa_name}${branch.code ? ` (${branch.code})` : ''}`,
                    title: branch.spa_name,
                    searchText: [
                        branch.spa_name,
                        branch.code,
                        branch.city,
                        branch.area,
                        branch.state,
                        branch.address,
                        branch.phone,
                        branch.branch_group_name,
                    ].filter(Boolean).join(' ')
                })));
            } catch (error) {
                console.error('Failed to fetch monitoring filter branches', error);
            }
        };

        fetchBranches();
        return () => {
            mounted = false;
        };
    }, []);

    const updateFilter = (key, value) => {
        onChange({ ...filters, [key]: value });
    };

    const hasFilters = Object.values(filters).some(Boolean);

    return (
        <div className="bg-card border border-border rounded-2xl p-5 space-y-5">
            <div className="grid grid-cols-1 xl:grid-cols-[1.3fr_1fr_1fr_1fr_1fr] gap-4">
                <div className="space-y-1.5">
                    <div className="flex items-center gap-2 text-[10px] uppercase font-bold text-text-secondary">
                        <Search size={14} className="text-primary/70" />
                        Search Device
                    </div>
                    <Input
                        value={filters.search || ''}
                        onChange={(event) => updateFilter('search', event.target.value)}
                        onKeyDown={(event) => event.key === 'Enter' && onApply()}
                        placeholder="Search device, branch, city, area, issue..."
                        className="h-[42px] bg-background"
                    />
                </div>

                <div className="space-y-1.5">
                    <div className="flex items-center gap-2 text-[10px] uppercase font-bold text-text-secondary">
                        <MapPin size={14} className="text-primary/70" />
                        Branch
                    </div>
                    <SearchableSelect
                        value={filters.branch || ''}
                        onChange={(value) => updateFilter('branch', value)}
                        options={branches}
                        placeholder="All branches"
                        className="bg-background"
                    />
                </div>

                <div className="space-y-1.5">
                    <div className="flex items-center gap-2 text-[10px] uppercase font-bold text-text-secondary">
                        <Activity size={14} className="text-success/70" />
                        Device Status
                    </div>
                    <select
                        value={filters.deviceStatus || ''}
                        onChange={(event) => updateFilter('deviceStatus', event.target.value)}
                        className="w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm text-text-primary outline-none focus:ring-2 focus:ring-primary/20"
                    >
                        {statusOptions.map(option => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                    </select>
                </div>

                <div className="space-y-1.5">
                    <div className="flex items-center gap-2 text-[10px] uppercase font-bold text-text-secondary">
                        <AlertTriangle size={14} className="text-warning/70" />
                        Event Type
                    </div>
                    <select
                        value={filters.event_type || ''}
                        onChange={(event) => updateFilter('event_type', event.target.value)}
                        className="w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm text-text-primary outline-none focus:ring-2 focus:ring-primary/20"
                    >
                        {eventOptions.map(option => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                    </select>
                </div>

                <div className="space-y-1.5">
                    <div className="flex items-center gap-2 text-[10px] uppercase font-bold text-text-secondary">
                        <CheckCircle2 size={14} className="text-secondary/70" />
                        Alert Status
                    </div>
                    <select
                        value={filters.resolved || ''}
                        onChange={(event) => updateFilter('resolved', event.target.value)}
                        className="w-full h-[42px] px-3 bg-background border border-border rounded-lg text-sm text-text-primary outline-none focus:ring-2 focus:ring-primary/20"
                    >
                        {resolvedOptions.map(option => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/60 pt-4">
                <p className="text-xs text-text-secondary">
                    Filters apply to both live devices and system alerts where the backend supports the same field.
                </p>
                <div className="flex items-center gap-2">
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={onClear}
                        disabled={!hasFilters}
                    >
                        <X size={14} className="mr-1" />
                        Clear
                    </Button>
                    <Button size="sm" onClick={onApply}>
                        <Filter size={14} className="mr-1" />
                        Apply
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default memo(MonitoringFilters);

import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

const CallLogFilter = ({ onFilter, initialBranch = '', initialSearch = '' }) => {
    const { user } = useSelector(state => state.auth);
    const [search, setSearch] = useState(initialSearch);
    const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });
    const [branches, setBranches] = useState([]);
    const [selectedBranch, setSelectedBranch] = useState(initialBranch);
    const [selectedCallType, setSelectedCallType] = useState('');

    useEffect(() => {
        setSearch(initialSearch);
        setSelectedBranch(initialBranch);
    }, [initialSearch, initialBranch]);

    const isRestrictedManager = user?.role === 'branch_manager' || user?.role === 'regional_manager';

    useEffect(() => {
        const fetchBranches = async () => {
            // No need to fetch all branches for restricted managers
            if (isRestrictedManager) return;

            try {
                const response = await branchesAPI.getBranches();
                const branchData = response.data.results || response.data;
                setBranches(branchData.map(b => ({
                    value: b.id,
                    label: b.spa_name
                })));
            } catch (error) {
                console.error("Failed to fetch branches for filter", error);
            }
        };
        fetchBranches();
    }, [isRestrictedManager]);

    const handleFilter = () => {
        const filters = {};
        if (search) filters.search = search;
        if (dateRange.startDate) filters.start_date = dateRange.startDate;
        if (dateRange.endDate) filters.end_date = dateRange.endDate;
        if (selectedBranch && !isRestrictedManager) filters.branch = selectedBranch;
        if (selectedCallType) filters.call_type = selectedCallType;
        onFilter(filters);
    };

    const handleClear = () => {
        setSearch('');
        setDateRange({ startDate: '', endDate: '' });
        setSelectedBranch('');
        setSelectedCallType('');
        onFilter({});
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 items-end">
            <div className="space-y-1">
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Search Number</label>
                <div className="relative">
                    <Input
                        placeholder="e.g. 98765..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-3 py-2.5 focus:ring-sky-500 focus:border-sky-500"
                    />
                </div>
            </div>

            {!isRestrictedManager && (
                <div className="space-y-1">
                    <SearchableSelect
                        label="Branch"
                        placeholder="All Branches"
                        options={branches}
                        value={selectedBranch}
                        onChange={setSelectedBranch}
                    />
                </div>
            )}

            <div className="space-y-1">
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Call Type</label>
                <select
                    className="block w-full px-4 py-2.5 border border-gray-200 rounded-xl shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm bg-gray-50 transition-all hover:bg-white"
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

            <div className="space-y-1 lg:col-span-1">
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Date Range</label>
                <div className="flex items-center space-x-2">
                    <input
                        type="date"
                        className="block w-full px-3 py-2 border border-gray-200 rounded-xl shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm bg-gray-50 transition-all hover:bg-white"
                        value={dateRange.startDate}
                        onChange={(e) => setDateRange(prev => ({ ...prev, startDate: e.target.value }))}
                    />
                    <span className="text-gray-400">—</span>
                    <input
                        type="date"
                        className="block w-full px-3 py-2 border border-gray-200 rounded-xl shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm bg-gray-50 transition-all hover:bg-white"
                        value={dateRange.endDate}
                        onChange={(e) => setDateRange(prev => ({ ...prev, endDate: e.target.value }))}
                    />
                </div>
            </div>

            <div className="flex justify-end space-x-3 pb-0.5">
                <Button variant="outline" onClick={handleClear} className="px-6 border-gray-200 text-gray-600">Clear</Button>
                <Button onClick={handleFilter} className="px-8 bg-sky-600 hover:bg-sky-700">Apply</Button>
            </div>
        </div>
    );
};

export default CallLogFilter;


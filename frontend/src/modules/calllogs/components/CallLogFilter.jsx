import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

const CallLogFilter = ({ onFilter, initialBranch = '' }) => {
    const { user } = useSelector(state => state.auth);
    const [search, setSearch] = useState('');
    const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });
    const [branches, setBranches] = useState([]);
    const [selectedBranch, setSelectedBranch] = useState(initialBranch);
    const [selectedCallType, setSelectedCallType] = useState('');

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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Search Number</label>
                <Input
                    placeholder="e.g. 98765..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {!isRestrictedManager && (
                <div>
                    <SearchableSelect
                        label="Branch"
                        placeholder="All Branches"
                        options={branches}
                        value={selectedBranch}
                        onChange={setSelectedBranch}
                    />
                </div>
            )}

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Call Type</label>
                <select
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm"
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

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                    type="date"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm"
                    value={dateRange.startDate}
                    onChange={(e) => setDateRange(prev => ({ ...prev, startDate: e.target.value }))}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                    type="date"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm"
                    value={dateRange.endDate}
                    onChange={(e) => setDateRange(prev => ({ ...prev, endDate: e.target.value }))}
                />
            </div>

            <div className={`border-t md:border-t-0 pt-4 md:pt-0 ${isRestrictedManager ? 'lg:col-span-1' : 'lg:col-span-1'}`}>
                <div className="flex justify-end space-x-2">
                    <Button variant="secondary" onClick={handleClear}>Clear</Button>
                    <Button onClick={handleFilter}>Apply Filters</Button>
                </div>
            </div>
        </div>
    );
};

export default CallLogFilter;


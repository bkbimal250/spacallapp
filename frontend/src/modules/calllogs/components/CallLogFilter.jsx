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
                        label: b.spa_name
                    }))
                );

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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 items-end text-text-primary">

            <div className="space-y-1">

                <label className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                    Search Number
                </label>

                <Input
                    placeholder="e.g. 98765..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="bg-card border-border text-text-primary"
                />

            </div>

            {!isRestrictedManager && (

                <div className="space-y-1">

                    <SearchableSelect
                        label="Branch"
                        placeholder="All Branches"
                        options={branches}
                        value={selectedBranch}
                        onChange={setSelectedBranch}
                        className="bg-card border-border"
                    />

                </div>

            )}

            <div className="space-y-1">

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

            <div className="space-y-1">

                <label className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                    Date Range
                </label>

                <div className="flex items-center gap-2">

                    <input
                        type="date"
                        className="w-full px-2 py-1 bg-card border border-border rounded-md text-text-primary focus:border-primary"
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

            <div className="flex justify-end gap-3">

                <Button
                    variant="outline"
                    onClick={handleClear}
                    className="border-border text-text-secondary hover:bg-cardHover"
                >
                    Clear
                </Button>

                <Button
                    onClick={handleFilter}
                    className="bg-primary text-white hover:bg-primary-hover"
                >
                    Apply
                </Button>

            </div>

        </div>

    );

};

export default CallLogFilter;
import React from 'react';
import { RefreshCcw } from 'lucide-react';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import DateRangePicker from '../../../shared/components/DateRangePicker';

const AnalyticsFilter = ({
    branches,
    selectedBranch,
    setSelectedBranch,
    timeFilter,
    setTimeFilter,
    customDates,
    handleDateChange,
    callType,
    setCallType,
    loading
}) => {
    return (
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 bg-card p-6 rounded-2xl border border-border shadow-sm">
            <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-text-primary tracking-tight">
                    Call Analytics
                </h1>
                <p className="text-sm text-text-secondary mt-1 flex items-center gap-2">
                    Real-time monitoring
                    <span className="flex items-center gap-1 text-primary font-medium bg-primary/5 px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider">
                        <RefreshCcw size={10} className={loading ? "animate-spin" : ""} />
                        Live Updates
                    </span>
                </p>
            </div>

            <div className="flex flex-wrap items-center justify-center lg:justify-end gap-3 flex-grow">
                {/* Branch Filter */}
                <div className="w-full lg:w-[480px] sm:w-64">
                    <SearchableSelect
                        placeholder="All Branches"
                        options={branches}
                        value={selectedBranch}
                        onChange={setSelectedBranch}
                    />
                </div>

                {/* Call Type Filter */}
                <div className="w-full sm:w-44">
                    <select
                        value={callType}
                        onChange={(e) => setCallType(e.target.value)}
                        className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all cursor-pointer"
                    >
                        <option value="">All Call Types</option>
                        <option value="Incoming">Incoming</option>
                        <option value="Outgoing">Outgoing</option>
                        <option value="Missed">Missed</option>
                        <option value="Rejected">Rejected</option>
                    </select>
                </div>

                {/* Time & Date Filters */}
                <div className="flex items-center gap-3 w-full sm:w-auto">
                    {timeFilter === 'custom' && (
                        <DateRangePicker
                            startDate={customDates.startDate}
                            endDate={customDates.endDate}
                            onChange={handleDateChange}
                        />
                    )}

                    <select
                        value={timeFilter}
                        onChange={(e) => setTimeFilter(e.target.value)}
                        className="w-full sm:w-auto bg-background border border-border rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all cursor-pointer"
                    >
                        <option value="today">Today</option>
                        <option value="yesterday">Yesterday</option>
                        <option value="last_7_days">Last 7 Days</option>
                        <option value="last_30_days">Last 30 Days</option>
                        <option value="this_month">This Month</option>
                        <option value="custom">Custom Range</option>
                    </select>
                </div>

            </div>
        </div>
    );
};

export default React.memo(AnalyticsFilter);
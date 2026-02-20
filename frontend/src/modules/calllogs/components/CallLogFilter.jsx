import React from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import DateRangePicker from '../../../shared/components/DateRangePicker';

const CallLogFilter = ({ onFilter }) => {
    const [search, setSearch] = React.useState('');
    const [dateRange, setDateRange] = React.useState({ startDate: '', endDate: '' });

    const handleDateChange = (field, value) => {
        setDateRange(prev => ({ ...prev, [field]: value }));
    };

    const handleFilter = () => {
        const filters = {};
        if (search) filters.search = search;
        if (dateRange.startDate) filters.start_date = dateRange.startDate;
        if (dateRange.endDate) filters.end_date = dateRange.endDate;
        onFilter(filters);
    };

    return (
        <div className="bg-white p-4 rounded-lg shadow mb-4 flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
                <Input
                    placeholder="Search calls (e.g. by number)..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
                <DateRangePicker
                    startDate={dateRange.startDate}
                    endDate={dateRange.endDate}
                    onChange={handleDateChange}
                />
            </div>
            <Button onClick={handleFilter}>
                Filter
            </Button>
        </div>
    );
};

export default CallLogFilter;

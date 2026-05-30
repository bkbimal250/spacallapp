import React from 'react';

const DateRangePicker = ({ startDate, endDate, onChange }) => {
    return (
        <div className="flex items-center space-x-2">

            <input
                type="date"
                value={startDate || ''}
                onChange={(e) => onChange('startDate', e.target.value)}
                className="px-3 py-2 text-sm rounded-lg bg-background border border-border text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
            />

            <span className="text-text-secondary text-sm">
                to
            </span>

            <input
                type="date"
                value={endDate || ''}
                onChange={(e) => onChange('endDate', e.target.value)}
                className="px-3 py-2 text-sm rounded-lg bg-background border border-border text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
            />

        </div>
    );
};

export default DateRangePicker;
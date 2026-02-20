import React from 'react';

const DateRangePicker = ({ startDate, endDate, onChange }) => {
    return (
        <div className='flex items-center space-x-2'>
            <input
                type="date"
                value={startDate || ''}
                onChange={(e) => onChange('startDate', e.target.value)}
                className="border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm"
            />
            <span className="text-gray-500">to</span>
            <input
                type="date"
                value={endDate || ''}
                onChange={(e) => onChange('endDate', e.target.value)}
                className="border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm"
            />
        </div>
    );
};

export default DateRangePicker;

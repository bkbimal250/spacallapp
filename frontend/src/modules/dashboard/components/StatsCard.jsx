import React from 'react';

const StatsCard = ({ title, value, change, isNegative }) => {
    return (
        <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">
                    {title}
                </dt>
                <dd className="mt-1 text-3xl font-semibold text-gray-900">
                    {value}
                </dd>
                {change && (
                    <div className={`mt-2 flex items-baseline text-sm font-semibold ${isNegative ? 'text-red-600' : 'text-green-600'}`}>
                        {change}
                        <span className="ml-2 text-gray-500 font-medium">from last month</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default StatsCard;

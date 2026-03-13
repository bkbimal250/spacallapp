import React from 'react';

const StatsCard = ({ title, value, icon, change, isNegative, className = "" }) => {
    return (
        <div className={`bg-card border border-border rounded-2xl p-5 flex flex-col justify-between transition hover:border-primary/40 hover:bg-background ${className}`}>

            {/* TOP */}
            <div className="flex items-center justify-between">

                <p className="text-sm text-text-secondary font-medium">
                    {title}
                </p>

                {icon && (
                    <div className="p-2 rounded-lg bg-background text-primary">
                        {icon}
                    </div>
                )}

            </div>

            {/* VALUE */}
            <div className="mt-3">

                <p className="text-3xl font-bold text-text-primary">
                    {value}
                </p>

                {change && (
                    <div className={`mt-2 text-xs font-semibold ${isNegative ? "text-danger" : "text-success"}`}>
                        {change}
                        <span className="ml-2 text-text-muted font-medium">
                            from last period
                        </span>
                    </div>
                )}

            </div>

        </div>
    );
};

export default StatsCard;
import React, { memo } from 'react';

const StatsCard = ({ title, value, icon, change, isNegative, className = "" }) => {
    return (
        <div className={`bg-card border border-border rounded-xl p-4 flex flex-col justify-between transition hover:border-primary/40 hover:bg-background ${className}`}>

            {/* TOP */}
            <div className="flex items-center justify-between">

                <p className="text-xs text-text-secondary font-medium">
                    {title}
                </p>

                {icon && (
                    <div className="p-1.5 rounded-md bg-background text-primary">
                        {icon}
                    </div>
                )}

            </div>

            {/* VALUE */}
            <div className="mt-2">

                <p className="text-2xl font-semibold text-text-primary">
                    {value}
                </p>

                {change && (
                    <div className={`mt-1 text-[11px] font-medium ${isNegative ? "text-danger" : "text-success"}`}>
                        {change}
                        <span className="ml-1 text-text-muted">
                            from last
                        </span>
                    </div>
                )}

            </div>

        </div>
    );
};

export default memo(StatsCard);
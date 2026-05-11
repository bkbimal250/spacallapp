import React, { memo } from 'react';

const StatsCard = ({ title, value, icon, change, isNegative, className = "" }) => {
    return (
        <div className={`bg-card border border-border rounded-xl p-4 flex flex-col justify-between transition hover:border-primary/40 hover:bg-background ${className}`}>

            {/* TOP */}
            <div className="flex items-center justify-between gap-3">
                <div className="space-y-0.5 overflow-hidden">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-text-secondary truncate">
                        {title}
                    </p>
                    <p className="text-2xl font-bold text-text-primary tracking-tight">
                        {value}
                    </p>
                </div>

                {icon && (
                    <div className="shrink-0 p-2.5 rounded-2xl bg-white shadow-sm border border-border/50 group-hover:scale-110 transition-transform duration-300">
                        {icon}
                    </div>
                )}
            </div>

                {change && (
                    <div className={`mt-1 text-[11px] font-medium ${isNegative ? "text-danger" : "text-success"}`}>
                        {change}
                        <span className="ml-1 text-text-muted">
                            from last
                        </span>
                    </div>
                )}
            </div>
        );
};

export default memo(StatsCard);
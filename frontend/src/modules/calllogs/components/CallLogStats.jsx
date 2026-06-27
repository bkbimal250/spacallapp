import React, { memo } from 'react';
import StatsCard from '../../dashboard/components/StatsCard';
import {
    Phone,
    PhoneIncoming,
    PhoneOutgoing,
    PhoneMissed,
    PhoneForwarded,
    Clock,
    Users
} from 'lucide-react';

const formatFullNumber = (value) => {
    const number = Number(value || 0);
    return number.toLocaleString('en-IN');
};

const formatCompactNumber = (value) => {
    const number = Number(value || 0);
    const abs = Math.abs(number);

    if (abs < 10000) {
        return formatFullNumber(number);
    }

    if (abs < 1000000) {
        const formatted = number / 1000;
        return `${formatted.toFixed(formatted >= 100 ? 0 : 1).replace(/\.0$/, '')}K`;
    }

    const formatted = number / 1000000;
    return `${formatted.toFixed(formatted >= 10 ? 1 : 2).replace(/\.0+$/, '')}M`;
};

const MetricValue = ({ value }) => {
    return (
        <span
            title={formatFullNumber(value)}
            className="block max-w-full truncate whitespace-nowrap"
        >
            {formatCompactNumber(value)}
        </span>
    );
};

const CallLogStats = ({ stats, loading }) => {
    if (loading || !stats) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-6 animate-pulse">
                {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                    <div key={i} className="h-32 bg-card border border-border rounded-2xl"></div>
                ))}
            </div>
        );
    }

    const missedAndRejected = (stats.missed || 0) + (stats.rejected || 0);
    const uniqueCount = stats.unique_count || stats.unique || 0;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
            <StatsCard
                title="Total Calls"
                value={<MetricValue value={stats.total || 0} />}
                icon={<Phone size={20} />}
            />

            <StatsCard
                title="Unique Records"
                value={<MetricValue value={uniqueCount} />}
                icon={<Users size={20} className="text-primary" />}
                className="hover:border-primary/40 border-primary/20 bg-primary/5"
            />

            <StatsCard
                title="Incoming"
                value={<MetricValue value={stats.incoming || 0} />}
                icon={<PhoneIncoming size={20} className="text-success" />}
                className="hover:border-success/40"
            />

            <StatsCard
                title="Outgoing"
                value={<MetricValue value={stats.outgoing || 0} />}
                icon={<PhoneOutgoing size={20} className="text-info" />}
                className="hover:border-info/40"
            />

            <StatsCard
                title="Missed / Rejected"
                value={<MetricValue value={missedAndRejected} />}
                icon={<PhoneMissed size={20} className="text-danger" />}
                className="hover:border-danger/40"
            />

            {stats.followed_up !== undefined && (
                <>
                    <StatsCard
                        title="Followed Up"
                        value={<MetricValue value={stats.followed_up || 0} />}
                        icon={<Users size={20} className="text-success" />}
                        className="hover:border-success/40 bg-success/5 border-success/20"
                        subtitle={`${stats.missed > 0 ? Math.round((stats.followed_up / stats.missed) * 100) : 0}% rate`}
                    />

                    <StatsCard
                        title="SLA Missed"
                        value={<MetricValue value={stats.sla_missed || 0} />}
                        icon={<Clock size={20} className="text-red-600" />}
                        className="hover:border-red-400  bg-success/5 border-red-200"
                    />
                </>
            )}
        </div>
    );
};

export default memo(CallLogStats);
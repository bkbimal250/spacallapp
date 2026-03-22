
import React, { memo } from 'react';
import StatsCard from '../../dashboard/components/StatsCard';
import { 
    Phone, 
    PhoneIncoming, 
    PhoneOutgoing, 
    PhoneMissed,
    PhoneForwarded,
    Clock
} from 'lucide-react';

const CallLogStats = ({ stats, loading }) => {
    if (loading || !stats) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-pulse">
                {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-32 bg-card border border-border rounded-2xl"></div>
                ))}
            </div>
        );
    }

    const missedAndRejected = (stats.missed || 0) + (stats.rejected || 0);

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard 
                title="Total Calls"
                value={stats.total || 0}
                icon={<Phone size={20} />}
            />

            <StatsCard 
                title="Incoming"
                value={stats.incoming || 0}
                icon={<PhoneIncoming size={20} className="text-success" />}
                className="hover:border-success/40"
            />

            <StatsCard 
                title="Outgoing"
                value={stats.outgoing || 0}
                icon={<PhoneOutgoing size={20} className="text-info" />}
                className="hover:border-info/40"
            />

            <StatsCard 
                title="Missed / Rejected"
                value={missedAndRejected}
                icon={<PhoneMissed size={20} className="text-danger" />}
                className="hover:border-danger/40"
            />
        </div>
    );
};

export default memo(CallLogStats);
